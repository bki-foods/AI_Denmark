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
df_available_coffee.dropna(subset=['Syre','Aroma','Krop','Eftersmag'], inplace=True) 
df_available_coffee['Kontrakt_id'] = df_available_coffee.index



suggestions = [
    [(0, 0.15),   (34, 0.57), (36, 0.06), (41, 0.07), (26, 0.15), (-1, 0),    (-1, 0)]
    ,[(34, 0.94), (31, 0.06), (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0)]
    ,[(34, 0.94), (29, 0.06), (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0)]
    ,[(34, 0.91), (36, 0.09), (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0)]
    ,[(0, 0.06),  (34, 0.48), (4, 0.12),  (2, 0.17),  (41, 0.17), (-1, 0),    (-1, 0)]
    ,[(34, 0.34), (36, 0.06), (5, 0.27),  (14, 0.2),  (17, 0.13), (-1, 0),    (-1, 0)]
    ,[(34, 0.36), (36, 0.06), (40, 0.13), (9, 0.3),   (24, 0.15), (-1, 0),    (-1, 0)]
    ,[(0, 0.13),  (34, 0.26), (5, 0.28),  (23, 0.25), (26, 0.08), (-1, 0),    (-1, 0)]
    ,[(34, 0.38), (9, 0.26),  (36, 0.06), (13, 0.19), (6, 0.11),  (-1, 0),    (-1, 0)]
    ,[(34, 0.74), (15, 0.06), (11, 0.06), (9, 0.07),  (3, 0.07),  (-1, 0),    (-1, 0)]
    ,[(34, 0.72), (8, 0.28),  (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0),    (-1, 0)]
    ,[(34, 0.3),  (36, 0.06), (13, 0.27), (40, 0.08), (6, 0.29),  (-1, 0),    (-1, 0)]
    ,[(34, 0.67), (36, 0.06), (7, 0.07),  (11, 0.2),  (-1, 0),    (-1, 0),    (-1, 0)]
    ,[(34, 0.63), (36, 0.06), (8, 0.15),  (17, 0.09), (4, 0.07),  (-1, 0),    (-1, 0)]
    ,[(34, 0.2),  (36, 0.07), (10, 0.21), (14, 0.15), (12, 0.12), (8, 0.18),  (9, 0.07)]
    ,[(2, 0.22),  (34, 0.28), (5, 0.28),  (18, 0.09), (14, 0.07), (29, 0.06), (-1, 0)]
    ,[(34, 0.65), (18, 0.1),  (7, 0.06),  (9, 0.12),  (19, 0.07), (-1, 0),    (-1, 0)]
    ,[(34, 0.65), (36, 0.06), (11, 0.07), (39, 0.06), (26, 0.16), (-1, 0),    (-1, 0)]
    ,[(34, 0.59), (7, 0.08),  (11, 0.2),  (13, 0.07), (14, 0.06), (-1, 0),    (-1, 0)]
    ,[(4, 0.42),  (5, 0.34),  (5, 0.11),  (3, 0.13),  (-1, 0),    (-1, 0),    (-1, 0)]]


df_blend_suggestions = pd.DataFrame(columns=['Blend_nr','Kontraktnummer_index','Proportion'])   
blend_no = 0
for blend in suggestions:
    blend_no += 1
    for component_line in blend:
        if not component_line[0] == -1:
            con_ix = component_line[0]
            data = {'Blend_nr': blend_no
                    ,'Kontraktnummer_index': con_ix
                    ,'Proportion': component_line[1]}
            df_blend_suggestions = df_blend_suggestions.append(data, ignore_index = True)

blend_suggestion_columns = ['Blend_nr' ,'Kontraktnummer' ,'Modtagelse' ,'Proportion'
                            ,'Sort','Varenavn','Differentiale'
                            ,'Syre', 'Aroma', 'Krop', 'Eftersmag', 'Robusta'
                            ,'Screensize', 'Oprindelsesland','Mærkningsordning']
df_blend_suggestions = pd.merge(
    left = df_blend_suggestions
    ,right = df_available_coffee
    ,how = 'left'
    ,left_on= 'Kontraktnummer_index'
    ,right_on = 'Kontrakt_id')[blend_suggestion_columns]


















        