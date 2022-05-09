#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import joblib
import random
import bki_functions as bf
import ti_price_opt as tpo
import time


# Grab Currrent Time Before Running the Code for logging of total execution time
start_time = time.time()


contracts = [2,13,56,62,86,20,48,9,11,79,10,34,12,72,71,16,33,4,36,67,47,41]


def blend_prop_permutations(contracts: list, N_components: int) -> list:
      
    # Dictionary with lists of possible percentages used in blends. Keys indicate no of components in blend.
    udfaldsrum = {
         1: list([100])
        ,2: [i for i in range(5,96,5)]
        ,3: [i for i in range(5,91,5)]
        ,4: [i for i in range(5,86,5)]
        ,5: [i for i in range(5,81,5)]
        ,6: [i for i in range(5,76,5)]
        ,7: [i for i in range(5,71,5)]}
    
    # Combine proportions and contracts with contracts and proportions for single component blends
    # blends_1_final = list(itertools.product(contracts_possible[1], udfaldsrum[1]))
    
    # Get all possible contract permutations for blends with N components
    blends = [contract for contract in itertools.permutations(contracts, N_components)]
    blends = [contract for contract in blends if len(contract) == len(set(contract)) ]
    # Get all possible proportion combinations
    blends_proportions = [comb for comb in itertools.combinations_with_replacement(udfaldsrum[N_components], N_components)]
    blends_proportions = [comb for comb in blends_proportions  if sum(comb) == 100]

    # Combine proportions and contracts
    blends_final = list(itertools.product(blends, blends_proportions))
    # Clear variables from memory
    del blends,blends_proportions
    
    return blends_final



# =============================================================================
# List of contracts
# Number of components to do the blend simulation across as a list
# Number of simulations to run if number of contracts exceed max feasible limit to do at the same time
# =============================================================================
def simulate_selected_contracts(contracts: list ,flavor_model ,flavors_list ,color: int
                                ,target_flavor: list
                                ,no_components: list = [4,5] ,no_simulations: int = 10):

    # If no_components list has more than one value each value is iterated over
    no_of_contracts = len(contracts)
    
    # Dictionary with lists of number of contracts to be used in blends. Key indicate no of components in blend.
    # Value indicate max number of contracts to be able to simulate all combinations.
    # If input length exceeds this
    contracts_possible = {1: 500 ,2: 25 ,3: 6 ,4: 4 ,5: 4 ,6: 6 ,7: 7}
    # Blend no for when blends need to be exported to Excel
    blend_no = 0
    temp = 0
    for i in no_components:
        padding_placeholder = (7 - i) * [-1]
        padding_proportions = (7 - i) * [0] 
        padding = list(zip(list(padding_placeholder), list(padding_proportions)))
        # padding = 7 - i
        # If more options are input than is possible, random selection is necessary    
        if no_of_contracts > contracts_possible[i]:
            for ii in range(no_simulations):
                # Pick the maximum allowed number of contracts at random from input list
                random_contracts = random.choices(contracts, k=contracts_possible[i])
                print(random_contracts)
                # Create all possible blends from the randomly selected contracts
                temp_blends = blend_prop_permutations(random_contracts, i)
                # Convert to proper format and add padding if needed
                temp_blends = [list(zip(list(blend[0]),list(blend[1]))) for blend in temp_blends]
                temp_blends = [blend +padding for blend in temp_blends]
                # Iterate over each blend and append flavor to lists
                
                
                for blend_no_it,blend in enumerate(temp_blends):
                    # Predict flavor
                    predicted_flavor_profile = tpo.taste_pred(
                        blend
                        ,flavor_predictor
                        ,flavors_list
                        ,110)
                    print(blend)
                    # Vi skal have fjernet de uinteressante blends og gemt de spændende i en liste for sig.
                    if not any(abs(predicted_flavor_profile - target_flavor_list) > 1.0):
                        print("her er et match")
                        temp += 1
                    blend_no += 1
                blend_no += 1
            pass
        else: # If len <= contracts possible, no random selection is necessary
            pass
    print(temp)
    return temp_blends,ii



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
target_flavor_list = [6,6,7,6]
# =============================================================================
# END OF TESTING PART
# =============================================================================

#OBS OBS OBS OBS
TEST_AF_SIMULEREDE_BLENDS,FLAVORS = simulate_selected_contracts(contracts ,flavor_predictor ,flavors_list ,110, target_flavor_list)


print(FLAVORS)






# Grab Currrent Time After Running the Code for logging of total execution time
end_time = time.time()
total_time = end_time - start_time
#Subtract Start Time from The End Time
total_time_seconds = int(total_time) % 60
total_time_minutes = total_time // 60
total_time_hours = total_time // 60
execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))

print(execution_time)

