#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import bki_functions as bf
import bki_server_information as bsi



# Read request from BKI_Datastore, update request that it is initiated and write into log
df_request = bf.get_ds_blend_request()
request_id = df_request['Id'].iloc[0]
#TODO activate two lines below
# bf.update_request_log(request_id ,1)
# bf.log_insert('bki_flow_management.py','Request id ' + str(request_id) + ' initiated.')
# Add locations to dictionary
dict_locations = {
    'SILOER': df_request['Lager_siloer'].iloc[0],
    'WAREHOUSE': df_request['Lager_warehouse'].iloc[0],
    'AARHUSHAVN': df_request['Lager_havn'].iloc[0],
    'SPOT': df_request['Lager_spot'].iloc[0],
    'AFLOAT': df_request['Lager_afloat'].iloc[0],
    'UDLAND': df_request['Lager_udland'].iloc[0]
    }
# Minimum available amount of coffee for an item to be included
min_quantity = df_request['Minimum_lager'].iloc[0]
# Different types of certifications
dict_certifications = {
    'Sammensætning': df_request['Sammensætning'].iloc[0],
    'Fairtrade': df_request['Inkluder_fairtrade'].iloc[0],
    'Økologi': df_request['Inkluder_økologi'].iloc[0],
    'Rainforest': df_request['Inkluder_rainforest'].iloc[0],
    'Konventionel': df_request['Inkluder_konventionel'].iloc[0],
    }

# Get all available quantities available for use in production
df_available_coffee = bf.get_all_available_quantities(
    dict_locations,
    min_quantity,
    dict_certifications)



#TODO: Get data from TI script with suggestions for recipe combinations


# =============================================================================
# Create Excel workbook with relevant sheets
# =============================================================================
wb_name = f'Receptforslag_{request_id}.xlsx'
path_file_wb = bsi.filepath_report + r'\\' + wb_name
excel_writer = pd.ExcelWriter(path_file_wb, engine='xlsxwriter')
# Input data for request
bf.insert_dataframe_into_excel(
    excel_writer,
    df_request,
    'Data for anmodning')
# Suggested blends
#TODO
# Green coffee input
# bf.insert_dataframe_into_excel(
#     excel_writer,
#     df_available_coffee,
#     'Kaffekontrakter input')
# Similar/identical blends

# Description/documentation


excel_writer.save()
# Exit script
bf.get_exit_check(0)
