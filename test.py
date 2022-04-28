#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import joblib
import bki_functions as bf
import bki_server_information as bsi
import ti_price_opt as tpo

import shutil
import os
import datetime

# =============================================================================
# # Read request from BKI_Datastore
# df_request = bf.get_ds_blend_request()
# df_request['Robusta'].fillna(10, inplace=True)
# # Add locations to dictionary for later
# dict_locations = {
#     'SILOER': df_request['Lager_siloer'].iloc[0]
#     ,'WAREHOUSE': df_request['Lager_warehouse'].iloc[0]
#     ,'AARHUSHAVN': df_request['Lager_havn'].iloc[0]
#     ,'SPOT': df_request['Lager_spot'].iloc[0]
#     ,'AFLOAT': df_request['Lager_afloat'].iloc[0]
#     ,'UDLAND': df_request['Lager_udland'].iloc[0]}
# 
# # Minimum available amount of coffee for an item to be included
# min_quantity = df_request['Minimum_lager'].iloc[0]
# 
# # Different types of certifications
# dict_certifications = {
#     'Sammensætning': df_request['Sammensætning'].iloc[0]
#     ,'Fairtrade': df_request['Inkluder_fairtrade'].iloc[0]
#     ,'Økologi': df_request['Inkluder_økologi'].iloc[0]
#     ,'Rainforest': df_request['Inkluder_rainforest'].iloc[0]
#     ,'Konventionel': df_request['Inkluder_konventionel'].iloc[0]
#     }
# 
# # Get all available quantities available for use in production.
# df_available_coffee = bf.get_all_available_quantities(
#     dict_locations
#     ,min_quantity
#     ,dict_certifications)
# column_order_available_coffee = ['Kontraktnummer','Modtagelse','Lokation','Beholdning'
#                                  ,'Syre','Aroma','Krop','Eftersmag','Robusta','Differentiale'
#                                  ,'Sort','Varenavn','Screensize','Oprindelsesland','Mærkningsordning']
# df_available_coffee = df_available_coffee[column_order_available_coffee]
# 
# 
# # # BKI function to predict a taste profile from a dataframe input
# def predict_taste_profile(individual, flavor_model, candidates, color, MAX_C=7):
#     D = len(candidates[0, :])
#     size = len(individual)
#     components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
#     proportions = [individual[i][1] for i in range(size) if individual[i][0] != -1]
#     num_components = len(components)
# 
#     model_input = np.array([])
#     for c, p in zip(components, proportions):
#         model_input = np.concatenate((model_input, candidates[c, :]))
#         model_input = np.concatenate((model_input, [p]))
#     model_input = np.concatenate((model_input, [0] * ((D + 1) * (size - num_components))))
#     model_input = np.concatenate((model_input, [color]))
# 
#     # model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1))) # Dette er hvad vi "tror" input individual vil smage som - Let til tests
#     # model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) * 2) / 2 # Round to .5 values
#     model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) * 4) / 4 # Round to .25 values
#     # Evt. gang ovenstående med 2 --> round --> divider med 2 for at få halve karakterer
#     return model_output
# 
# 
# # Dette er en liste over individuals: for i in enumerate(hall_of_fame) - hall_of_fame[i] -> 'individual'
# hall_of_fame = [ 
# 	[(68, 0.16),(70, 0.15),(48, 0.1),(52, 0.53),(31, 0.06),(-1, 0),(-1, 0)]
# 	,[(99, 0.06), (69, 0.06), (70, 0.25), (52, 0.57), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(99, 0.06), (68, 0.13), (70, 0.46), (93, 0.21), (31, 0.14), (-1, 0), (-1, 0)]
# 	,[(68, 0.18), (52, 0.06), (85, 0.4), (93, 0.23), (31, 0.13), (-1, 0), (-1, 0)]
# 	,[(100, 0.11), (75, 0.06), (78, 0.36), (84, 0.41), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(70, 0.22), (52, 0.06), (85, 0.32), (93, 0.26), (31, 0.14), (-1, 0), (-1, 0)]
# 	,[(99, 0.06), (68, 0.16), (70, 0.08), (52, 0.64), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(68, 0.06), (38, 0.06), (70, 0.3), (52, 0.32), (31, 0.26), (-1, 0), (-1, 0)]
# 	,[(99, 0.06), (69, 0.06), (70, 0.42), (93, 0.32), (31, 0.14), (-1, 0), (-1, 0)]
# 	,[(100, 0.08), (70, 0.31), (52, 0.06), (85, 0.28), (31, 0.27), (-1, 0), (-1, 0)]
# 	,[(66, 0.06), (69, 0.06), (70, 0.14), (52, 0.64), (31, 0.1), (-1, 0), (-1, 0)]
# 	,[(3, 0.06), (68, 0.2), (70, 0.11), (30, 0.48), (31, 0.15), (-1, 0), (-1, 0)]
# 	,[(66, 0.21), (69, 0.06), (70, 0.38), (93, 0.29), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(66, 0.26), (68, 0.06), (70, 0.26), (93, 0.29), (31, 0.13), (-1, 0), (-1, 0)]
# 	,[(66, 0.12), (68, 0.19), (70, 0.16), (52, 0.39), (31, 0.14), (-1, 0), (-1, 0)]
# 	,[(42, 0.42), (77, 0.08), (48, 0.18), (30, 0.26), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(73, 0.06), (10, 0.08), (76, 0.24), (52, 0.54), (91, 0.08), (-1, 0), (-1, 0)]
# 	,[(3, 0.06), (68, 0.2), (54, 0.33), (30, 0.19), (31, 0.22), (-1, 0), (-1, 0)]
# 	,[(66, 0.13), (70, 0.29), (79, 0.45), (54, 0.07), (31, 0.06), (-1, 0), (-1, 0)]
# 	,[(99, 0.26), (73, 0.21), (77, 0.06), (52, 0.21), (26, 0.26), (-1, 0), (-1, 0)]]
# # Den trænede model til prediktion --> 'flavor_model'
# flavor_predictor = joblib.load('bki_flavor_predictor_no_robusta.sav') 
# # Farven på recepten vil skal ramme
# color = 110
# # Empty list with flavor profiles to be filled in loop below
# predicted_flavor_profiles = []
# # Loop over each blend suggestion to predict flavor
# # for blend in hall_of_fame:
# #     blend_component_flavors = []
# #     for component_line in blend:
# #         if not component_line[0] == -1:
# #             flavors = df_available_coffee[['Syre','Aroma','Krop','Eftersmag']].iloc[component_line[0]].tolist()
# #             blend_component_flavors += [flavors]
# #         else:
# #             blend_component_flavors += [[-1,-1,-1,-1]]
# #     predicted_flavor = predict_taste_profile(
# #         individual = blend
# #         ,flavor_model = flavor_predictor
# #         ,candidates = blend_component_flavors
# #         ,color = color)
# #     print(predicted_flavor)
# =============================================================================


# import the builtin time module
import time

# Grab Currrent Time Before Running the Code
start_time = time.time()

for i in range(100000000):
    pass

# Grab Currrent Time After Running the Code
end = time.time()

#Subtract Start Time from The End Time
total_time_seconds = end - start
total_time_minutes = total_time_seconds // 60
total_time_hours = total_time_minutes // 60

execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))














        