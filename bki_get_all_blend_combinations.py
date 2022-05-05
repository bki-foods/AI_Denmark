#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import joblib
import bki_functions as bf
import ti_price_opt as tpo
# import time


# =============================================================================
# # Grab Currrent Time Before Running the Code for logging of total execution time
# start_time = time.time()
# =============================================================================



def get_blend_permutations(contracts: list, N_components: int) -> list:
    
    
    
    len_contracts = len(contracts)
    # Dictionary with lists of possible percentages used in blends. Keys indicate no of components in blend.
    udfaldsrum = {
         1: list([100])
        ,2: [i for i in range(5,96,5)]
        ,3: [i for i in range(5,91,5)]
        ,4: [i for i in range(5,86,5)]
        ,5: [i for i in range(5,81,5)]
        ,6: [i for i in range(5,76,5)]
        ,7: [i for i in range(5,71,5)]}
    
    # Dictionary with lists of number of contracts to be used in blends. Key indicate no of components in blend.
    # The more components in blend the fewer contracts it's possible to use due to massive amounts of possible combinations.
    contracts_possible = {
         1: list(range(len_contracts if len_contracts < 500 else 500))
        ,2: list(range(len_contracts if len_contracts < 75 else 75))
        ,3: list(range(len_contracts if len_contracts < 13 else 13))
        ,4: list(range(len_contracts if len_contracts < 7 else 7))
        ,5: list(range(len_contracts if len_contracts < 6 else 6))
        ,6: list(range(len_contracts if len_contracts < 6 else 6))
        ,7: list(range(len_contracts if len_contracts < 6 else 7))}
    

    # Combine proportions and contracts with contracts and proportions for single component blends
    # blends_1_final = list(itertools.product(contracts_possible[1], udfaldsrum[1]))
    
    # Get all possible contract permutations for blends with N components
    blends = [contract for contract in itertools.permutations(contracts_possible[N_components], N_components)]
    blends = [contract for contract in blends if len(contract) == len(set(contract)) ]
    # Get all possible proportion combinations
    blends_proportions = [comb for comb in itertools.combinations_with_replacement(udfaldsrum[N_components], N_components)]
    blends_proportions = [comb for comb in blends_proportions  if sum(comb) == 100]

    # Combine proportions and contracts
    blends_final = list(itertools.product(blends, blends_proportions))
    # Clear variables from memory
    del blends,blends_proportions
    
    return blends_final




contracts = [40,41,53,30,13,23,32,45,16,49,31,43,7,2,4,11,8,21,26,1,14,20,39,47,35,12,6,9]




# If len(contracts) > max












# =============================================================================
# TEMP for testing of permutations
# =============================================================================
# Add locations to dictionary for later
dict_locations = {
    "SILOER": 1
    ,"WAREHOUSE": 1
    ,"AARHUSHAVN": 1
    ,"SPOT": 0
    ,"AFLOAT": 0
    ,"UDLAND": 0}

# Minimum available amount of coffee for an item to be included
min_quantity = 1000


# Different types of certifications
dict_certifications = {
    "Sammensætning": "Blandet"
    ,"Fairtrade": 1
    ,"Økologi": 1
    ,"Rainforest": 1
    ,"Konventionel": 1}


# Get all available quantities available for use in production.
df_available_coffee = bf.get_all_available_quantities(
    dict_locations
    ,min_quantity
    ,dict_certifications)
# Remove rows with na, we need values for all parameters. Reset index afterwards
df_available_coffee.dropna(subset=["Syre","Aroma","Krop","Eftersmag"],inplace=True)
df_available_coffee.reset_index(drop=True, inplace=True)
contracts_list = df_available_coffee["Kontraktnummer"].to_list()
# model for flavor predictor
model_name = "flavor_predictor_no_robusta.sav"
flavor_predictor = joblib.load(model_name)
flavor_columns = ["Syre","Aroma","Krop","Eftersmag"]
flavors_list = df_available_coffee[flavor_columns].to_numpy()

x = get_blend_permutations(contracts_list, 2)



# =============================================================================
# # Iterate over each blend and append flavor to lists
# for i,blend_no in enumerate(test):
#     pass
#     # Iterate over integers.. cleanup...
#     blend_no = int(i)
#     # Get hof blend by index
#     hof_blend = x[blend_no]
#     # Predict flavor
#     predicted_flavors = tpo.taste_pred(
#         hof_blend
#         ,flavor_predictor # OK
#         ,flavors_list
#         ,110) # OK
#     # Add each flavor to each own list
#     print(predicted_flavors)
# 
# =============================================================================







#hof_blend = # Nested lists and tuples, format: [[(),(),()],[(),(),()],[(),(),()]]
#flavor_predictor = model navn
# flavors_list = numpy array med flavors på alle available amounts
# request_farve = fast værdi















# =============================================================================
# 
# # Grab Currrent Time After Running the Code for logging of total execution time
# end_time = time.time()
# total_time = end_time - start_time
# #Subtract Start Time from The End Time
# total_time_seconds = int(total_time) % 60
# total_time_minutes = total_time // 60
# total_time_hours = total_time // 60
# execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))
# 
# print(execution_time)
# 
# =============================================================================
