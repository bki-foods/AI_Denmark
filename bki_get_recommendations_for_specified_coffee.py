#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import joblib
import bki_functions as bf
import ti_price_opt as tpo
import time
import pandas as pd




# Grab Currrent Time Before Running the Code for logging of total execution time
start_time = time.time()

# Temp variables, change to values from query #TODO!
items = [0,1,2,3,4,5,6,7]
request_item = 5 # Prime A
request_proportion = 5



def get_blends_with_proportions(required_item:int, min_proportion:int, available_items:list, number_of_components:int) -> list:
    #TODO! Docstring!!!
    
    # Create padding for component index and their proportions to ensure all blends have the required dimensions
    padding_placeholder = (7 - number_of_components) * [-1]
    padding_proportions = (7 - number_of_components) * [0] 

    number_of_available_items = len(available_items)
    # If a blend recommendation is requested with more components than components are available, terminate.
    # Terminate if the theoretical amount of records to calculate across exceeds ~3 milion
    if number_of_components > number_of_available_items or number_of_components < 2:
        return []
    if number_of_components > 6 and number_of_available_items > 8:
        return []
    if number_of_components > 5 and number_of_available_items > 10:
        return []
    if number_of_components > 4 and number_of_available_items > 15:
        return []

    # Dictionary with lists of possible percentages for components that are not that main component - hardcoded increments
    # Min proportion of a component is 5, and all component proportions are incremented by 5.
    ranges_proportions_remaining_items = {
         2: [i / 100.0 for i in range(5, 101 - min_proportion, 5)]
        ,3: [i / 100.0 for i in range(5, 96 - min_proportion, 5)]
        ,4: [i / 100.0 for i in range(5, 91 - min_proportion, 5)]
        ,5: [i / 100.0 for i in range(5, 86 - min_proportion, 5)]
        ,6: [i / 100.0 for i in range(5, 81 - min_proportion, 5)]
        ,7: [i / 100.0 for i in range(5, 76 - min_proportion, 5)]}
  
    # Remove the requested contract from the list of possible contracts
    available_items = [item for item in available_items if item != required_item]  
    
    # Proportion for the requested component will always be the last element in the list of proportions
    # Get all possible proportion combinations
    proportions = [list(comb) for comb in itertools.combinations_with_replacement(ranges_proportions_remaining_items[number_of_components], number_of_components -1)]
    
    # Create a list of missing proportions such that each blend will sum to 100
    missing_proportions = [round(1.0 - sum(props),2) for props in proportions]
    proportions = list(zip(missing_proportions, proportions))
    # Append the requested component proportion to the list of proportions.
    [props[1].append(props[0]) for props in proportions]
    # Only keep the proportion combinations which sum to 100 and prop >= requested proportion
    proportions = [props[1] for props in proportions if sum(props[1]) == 1.0 and props[1][-1] >= min_proportion / 100.0]   
    proportions = [props + padding_proportions for props in proportions]
    # Get all possible blend combinations
    blends = [list(contract) for contract in itertools.permutations(available_items, number_of_components -1)]
    # Add requested blend item as last value in blends to correspond with proportions
    blends = [blend + [required_item] for blend in blends]
    blends = [blend + padding_placeholder for blend in blends]
    
    # Combine proportions and contracts into final list
    blends_prop = list(itertools.product(blends, proportions))
    blends_prop = [list(zip(blends_prop[i][0],blends_prop[i][1])) for i in range(len(blends_prop))]
    blends_prop = [blend for blend in blends_prop]  
    
    return blends_prop


def get_fitting_blends(blends, prices, flavor_model, flavors_components, target_flavor, target_color:int, cut_off_value:float = 0.75)->list:
    """
    #TODO!!

    Parameters
    ----------
    blends :
        A list containing all the blends to be evaluated containing index no of component and its proportion.
        Each blend must be 7 components long. Use -1 as placeholder for NULL components with a proportion of 0.
    prices :
        A list of prices for all possible components.
    flavor_model :
        A trained model used to predict the flavor of each blend.
    flavors_components :
        A list with all the flavor profiles of all possible components.
    target_flavor :
        The Target flavor which is requested
    target_color : int
        The color which the blends are expected to be roasted to
    cut_off_value : float

    Returns
    -------
    A list with the blends that have no differences to the target flavor profile greater than the cuf_off_value

    """
    # Create a list of calculated diffs in predicted flavor profile when compared to the target
    blends_flavor_diffs = [tpo.taste_diff(blend, flavor_model, flavors_components, target_flavor, target_color).tolist() for blend in blends]
    # Get the largest diff for each blend
    blends_flavor_diffs = [max(blend[0]) for blend in blends_flavor_diffs]
    
    # Get the index values for all blends whose largest flavor diff does not exceed the cuf off value, create a list with actual blends
    blends_with_close_enough_flavor = [i for i,val in enumerate(blends_flavor_diffs) if not val > cut_off_value]
    interesting_blends = [blends[i] for i in blends_with_close_enough_flavor]

    # Create a list of fitness values for each of the  input blends
    predicted_fitness = [tpo.blend_fitness(
         blend
         ,prices
         ,flavor_model
         ,flavors_components
         ,target_flavor
         ,target_color).tolist() for blend in interesting_blends]
    predicted_fitness = [val[0] for val in predicted_fitness]
    
    return interesting_blends,predicted_fitness



def get_fitting_blends_complete_list(required_item:int, min_proportion:int, available_items:list, prices
                                     ,flavor_model, flavors_components, target_flavor:list
                                     ,target_color:int, cut_off_value:float = 0.75) ->list:
    #TODO! Docstring
    best_fitting_blends = []
    best_fitting_fitness = []
    
    # Use the number of components as iterator    
    for i in [2,3]: #[2,3,4,5,6,7]
        all_blends_incl_proportions = get_blends_with_proportions(
            required_item
            ,min_proportion
            ,available_items
            ,i)
        
        print("Components: " + str(i) + "\n" "Possible blends: " + str(len(all_blends_incl_proportions)))
        
        # If data exists, get all blends that are within cut-off criteria
        if len(all_blends_incl_proportions) > 0:
            new_blends, new_fitness = get_fitting_blends(
                all_blends_incl_proportions
                ,prices
                ,flavor_model
                ,flavors_components
                ,target_flavor
                ,target_color
                ,cut_off_value)
            if len(new_blends):
                #Extend lists with blends and fitness values if any new exists
                best_fitting_blends.extend([blend for blend in new_blends])
                best_fitting_fitness.extend([fitness for fitness in new_fitness])
    
    
        print("No. of fitting blends after run: " + str(len(new_blends)))
        print("Runtime seconds: " + str(int(time.time() - start_time)))
        print("---------------------------------------------------------")
        
    blend_numbers = list(range(len(best_fitting_fitness)))
    
    return best_fitting_blends,best_fitting_fitness,blend_numbers


def data_chunker(data:list, chunk_size:int=2000) -> list:
    while data:
        chunk = data[:chunk_size]
        data = data[chunk_size:]
        
        yield chunk

# =============================================================================
# TEMP for testing of permutations
# =============================================================================
# Add locations to dictionary for later
dict_locations = {
    "SILOER": 1
    ,"WAREHOUSE": 0
    ,"AARHUSHAVN": 0
    ,"SPOT": 0
    ,"AFLOAT": 0
    ,"UDLAND": 0}

# Minimum available amount of coffee for an item to be included
min_quantity = 1000


# Different types of certifications
dict_certifications = {
    "Sammensætning": "Ren arabica"
    ,"Fairtrade": 0
    ,"Økologi": 0
    ,"Rainforest": 0
    ,"Konventionel": 1}


# Get all available quantities available for use in production.
df_available_coffee = bf.get_all_available_quantities(
    dict_locations
    ,min_quantity
    ,dict_certifications
    ,True)
# Remove rows with na, we need values for all parameters. Reset index afterwards
df_available_coffee.dropna(subset=["Syre","Aroma","Krop","Eftersmag"],inplace=True)
df_available_coffee.reset_index(drop=True, inplace=True)
# Add dataframe index to a column to use for join later on
df_available_coffee["Kontrakt_id"] = df_available_coffee.index
contracts_list = df_available_coffee["Kontraktnummer"].to_list()
# model for flavor predictor
model_name = "flavor_predictor_no_robusta.sav"
flavor_predictor = joblib.load(model_name)
flavor_columns = ["Syre","Aroma","Krop","Eftersmag"]
flavors_list = df_available_coffee[flavor_columns].to_numpy()
target_flavor_list = [6,6,7,6]
target_color = 110
contract_prices_list = df_available_coffee["Standard Cost"].to_numpy().reshape(-1, 1)
# =============================================================================
# TEMP test data above for testing functions
# =============================================================================


best_fitting_hof = []
best_fitting_hof_size = 50

best_fitting_blends,best_fitting_fitness,blend_numbers = get_fitting_blends_complete_list(
    request_item
    ,request_proportion
    ,items
    ,contract_prices_list
    ,flavor_predictor
    ,flavors_list
    ,target_flavor_list
    ,target_color)

blends_with_fitness = list(zip(best_fitting_blends,best_fitting_fitness))


while blend_numbers:
    # Add blend no to variable and remove from list, looking to exhaust
    blend_no = blend_numbers[0]
    del blend_numbers[0]
    
    # If hof is empty, add the first blend to hof by default
    if not best_fitting_hof:
        best_fitting_hof.append(blend_no)
    # Check if any of the blends in the hof are too similar to the current blend
    blend_similar_to_hof = [tpo.blends_too_similar(best_fitting_blends[blend_no], best_fitting_blends[hof_blend]) for hof_blend in best_fitting_hof]
    # Get all fitness values of hof
    hof_fitness_total = [best_fitting_fitness[blend] for blend in best_fitting_hof]
    if not any(blend_similar_to_hof):
        # If hof has not reached max size yet, add the blend
        if len(best_fitting_hof) < best_fitting_hof_size:
            best_fitting_hof.append(blend_no)
        # If hof has reached max size, evaluate fitness value of current blend and 
        else:
            min_fitness_hof = min(hof_fitness_total)
            # If fitness of current blend is higher than the lowest in hof, replace
            if best_fitting_fitness[blend_no] > min_fitness_hof:
                # Get the index of the worst fitness value
                ix_worst_fitness = hof_fitness_total.index(min_fitness_hof)
                # Replace worst fitness with current blend
                best_fitting_hof[ix_worst_fitness] = blend_no
    # If current blend is similar to one or more in hof, we need to compare fitness values of these
    else:
        min_fitness_hof_similar = [hof_fitness_total[i] if blend_similar_to_hof[i] else 999 for i in range(len(best_fitting_hof))]
        
    
    
# any([best_fitting_fitness[blend_no] for blend_no in best_fitting_hof]) 


# =============================================================================
# # Suggested blends, hall of fame
# df_tester = pd.DataFrame(columns=["Blend_nr","Kontraktnummer_index","Proportion"])   
# # Create iterator to create a blend number for each complete blend suggestion
# blend_no = 1000
# # Nested lists and tuples, format: [[(),(),()],[(),(),()],[(),(),()]]
# for blend in best_fitting_blends:
#     blend_no += 1
#     for component_line in blend:
#         if not component_line[0] == -1: # -1 indicates a NULL placeholder value, these are ignored
#             con_ix = component_line[0]
#             # Extract data for each component line for each blend suggestion and append to dataframe
#             data = {"Blend_nr": blend_no
#                     ,"Kontraktnummer_index": con_ix
#                     ,"Proportion": component_line[1]}
#             df_tester = df_tester.append(data, ignore_index = True)
# =============================================================================






















# =============================================================================
# 
# 
# # Merge blend suggestions with input available coffees to add additional info to datafarme, and alter column order
# df_tester = pd.merge(
#     left = df_tester
#     ,right = df_available_coffee
#     ,how = "left"
#     ,left_on= "Kontraktnummer_index"
#     ,right_on = "Kontrakt_id")
# # Calculate blend cost per component using the standard cost price of each component
# df_tester["Beregnet pris"] = df_tester["Proportion"] * df_tester["Standard Cost"]
# df_tester["Beregnet pris +1M"] = df_tester["Proportion"] * df_tester["Forecast Unit Cost +1M"]
# df_tester["Beregnet pris +2M"] = df_tester["Proportion"] * df_tester["Forecast Unit Cost +2M"]
# df_tester["Beregnet pris +3M"] = df_tester["Proportion"] * df_tester["Forecast Unit Cost +3M"]
# 
# 
# # Defined column order for final dataframe, only add robusta if it is to be predicted.
# blend_suggestion_columns = ["Blend_nr" ,"Sort","Varenavn" ,"Proportion"
#                             ,"Beregnet pris" ,"Beregnet pris +1M"
#                             ,"Beregnet pris +2M", "Beregnet pris +3M"]
# 
# df_tester = df_tester[blend_suggestion_columns]
# =============================================================================
































# Grab Currrent Time After Running the Code for logging of total execution time
end_time = time.time()
total_time = end_time - start_time
#Subtract Start Time from The End Time
total_time_seconds = int(total_time) % 60
total_time_minutes = total_time // 60
total_time_hours = total_time // 60 // 60
execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))

print(execution_time)
print(round(total_time,2))


