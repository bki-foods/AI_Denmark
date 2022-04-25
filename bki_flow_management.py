#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import joblib
import bki_functions as bf
import bki_server_information as bsi
import ti_price_opt as tpo


# Read request from BKI_Datastore
df_request = bf.get_ds_blend_request()
df_request['Robusta'].fillna(10, inplace=True) # Modellen skal bruge en værdi for robusta parameteren
# Create necessary request variables for later use
request_id = df_request['Id'].iloc[0]
request_recipient = df_request['Bruger_email'].iloc[0]
request_syre = df_request['Syre'].iloc[0]
request_aroma = df_request['Aroma'].iloc[0]
request_krop = df_request['Krop'].iloc[0]
request_eftersmag = df_request['Eftersmag'].iloc[0]

# Update request that it is initiated and write into log
bf.update_request_log(request_id ,1)
bf.log_insert('bki_flow_management.py','Request id ' + str(request_id) + ' initiated.')

# Add locations to dictionary for later
dict_locations = {
    'SILOER': df_request['Lager_siloer'].iloc[0]
    ,'WAREHOUSE': df_request['Lager_warehouse'].iloc[0]
    ,'AARHUSHAVN': df_request['Lager_havn'].iloc[0]
    ,'SPOT': df_request['Lager_spot'].iloc[0]
    ,'AFLOAT': df_request['Lager_afloat'].iloc[0]
    ,'UDLAND': df_request['Lager_udland'].iloc[0]}

# Minimum available amount of coffee for an item to be included
min_quantity = df_request['Minimum_lager'].iloc[0]

# Different types of certifications
dict_certifications = {
    'Sammensætning': df_request['Sammensætning'].iloc[0]
    ,'Fairtrade': df_request['Inkluder_fairtrade'].iloc[0]
    ,'Økologi': df_request['Inkluder_økologi'].iloc[0]
    ,'Rainforest': df_request['Inkluder_rainforest'].iloc[0]
    ,'Konventionel': df_request['Inkluder_konventionel'].iloc[0]
    }

# Get all available quantities available for use in production.
df_available_coffee = bf.get_all_available_quantities(
    dict_locations
    ,min_quantity
    ,dict_certifications)
column_order_available_coffee = ['Kontraktnummer','Modtagelse','Lokation','Beholdning'
                                 ,'Syre','Aroma','Krop','Eftersmag','Robusta','Differentiale'
                                 ,'Sort','Varenavn','Screensize','Oprindelsesland','Mærkningsordning']
df_available_coffee = df_available_coffee[column_order_available_coffee]
df_available_coffee['Robusta'].fillna(10, inplace=True)
df_available_coffee.dropna(subset=['Syre','Aroma','Krop','Eftersmag'], inplace=True) # Vi skal have karakterer, ellers dur det ikke #TODO Skal vi lave en oversigt over problembørnene?


#TODO: Get data from TI script with suggestions for recipe combinations
contracts_list = df_available_coffee['Kontraktnummer'].to_list()
flavors_list = df_available_coffee[['Syre','Aroma','Krop','Eftersmag','Robusta']].to_numpy()
differentials_list = df_available_coffee['Differentiale'].to_numpy().reshape(-1, 1)
target_flavor_list = df_request[['Syre','Aroma','Krop','Eftersmag','Robusta']].to_numpy()[0]

pop, logbook, hof = tpo.ga_cheapest_blend(
    contracts_list
    ,flavors_list
    ,differentials_list
    ,joblib.load('bki_flavor_predictor_robusta.sav')
    ,target_flavor_list
    ,df_request['Farve'].iloc[0])

print(pop, logbook, hof)


# =============================================================================
# Create Excel workbook with relevant sheets
# =============================================================================
wb_name = f'Receptforslag_{request_id}.xlsx'
path_file_wb = bsi.filepath_report + r'\\' + wb_name
excel_writer = pd.ExcelWriter(path_file_wb, engine='xlsxwriter')

# Suggested blends

# df_suggested_blends = pd.DataFrame (hof, columns = ['Kontrakt_index', 'Proportion'])
# print(df_suggested_blends)
# Green coffee input
bf.insert_dataframe_into_excel(
    excel_writer
    ,df_available_coffee
    ,'Kaffekontrakter input')
# Similar/identical blends
bf.insert_dataframe_into_excel(
    excel_writer
    ,bf.get_identical_recipes(request_syre, request_aroma, request_krop, request_eftersmag)
    ,'Identiske, lign. recepter')
# Input data for request, replace 0/1 with text values before transposing
dict_include_exclude = {0: 'Ekskluder', 1: 'Inkluder'}
columns_include_exclude = ['Inkluder_konventionel','Inkluder_fairtrade','Inkluder_økologi'
                           ,'Inkluder_rainforest','Lager_siloer','Lager_warehouse','Lager_havn'
                           ,'Lager_spot','Lager_afloat','Lager_udland']
for col in columns_include_exclude:
    df_request[col] = df_request[col].map(dict_include_exclude)
# Transpose 
df_request = df_request.transpose().reset_index()
df_request.columns = ['Oplysning','Værdi']
bf.insert_dataframe_into_excel(
    excel_writer
    ,df_request
    ,'Data for anmodning')
# Save and close workbook
excel_writer.save()
excel_writer.close()

# Update source table with status, filename and -path
bf.update_request_log(request_id ,2 ,wb_name, bsi.filepath_report)
bf.log_insert('bki_flow_management.py','Request id ' + str(request_id) + ' completed.')

# Create record in cof.email_log
dict_email = {
    'Id_Org': request_id
    ,'Email_type': 5
    ,'Email_til': request_recipient
    ,'Email_emne': f'Excel fil med receptforslag klar: {wb_name}'
    ,'Email_tekst': f'''Excel fil med receptforslag er klar.
                        Filnavn: {wb_name}
                        Filsti: {bsi.filepath_report} \n\n\n'''
    ,'Id_org_kildenummer': 9}
bf.insert_into_email_log(dict_email)
bf.log_insert('bki_flow_management.py','Notification email for request id ' + str(request_id) + ' created.')
