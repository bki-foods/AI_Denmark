#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import joblib
import bki_functions as bf
import ti_price_opt as tpo
import time


# Grab Currrent Time Before Running the Code for logging of total execution time
start_time = time.time()

# Temp variables, change to values from query
items = [1,2,10,11,12,13,15,19,28]
request_item = 10
request_proportion = 5



def get_blends_with_proportions(required_item:int, min_proportion:int, available_items:list, number_of_components:int) -> list:

    padding_placeholder = (7 - number_of_components) * [-1]
    padding_proportions = (7 - number_of_components) * [0] 

    number_of_available_items = len(available_items)
    # If a blend recommendation is requested with more components than components are available, terminate.
    # Terminate if the theoretical amount of records to calculate across exceeds ~3 milion
    if number_of_components > number_of_available_items or number_of_components < 2:
        return None
    if number_of_available_items > 16:
        return None
    if number_of_components == 7 and number_of_available_items > 8:
        return None
    if number_of_components > 5 and number_of_available_items > 10:
        return None
    if number_of_components > 4 and number_of_available_items > 15:
        return None

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
    blends_prop = [blend for blend in blends_prop]
    
    blends_prop = [list(zip(blends_prop[i][0],blends_prop[i][1])) for i in range(len(blends_prop))]
    # Clear variables from memory
    # del blends,proportions,missing_proportions
    
    return blends_prop


def get_best_fitting_blends(blends, prices, flavor_model, flavors_components, target_flavor, target_color, no_return_values=50)->list:
    """
    

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
    no_return_values :
        The number of proposed blends which are to be returned.
        The default value is 50.

    Returns
    -------
    A list with the top N best fitting blends.

    """
    
    # Create a list of fitness values for each of the  input blends using the tpo function from main script.
    predicted_fitness = [float(tpo.blend_fitness(
        blends[i]
        ,prices
        ,flavor_model
        ,flavors_components
        ,target_flavor
        ,target_color)) for i in range(len(blends))]
    # Sort the fitness list and limit it to a top N list
    predicted_fitness_top_list = sorted(predicted_fitness,reverse=True)[:no_return_values]
    # Create a list with the blends which have a fitness value present in the top 50 list
    interesting_blends = [i for i in range(len(predicted_fitness)) if predicted_fitness[i] in predicted_fitness_top_list]
    # Filtered list with the top N best fitting blends
    interesting_blends = [blends[i] for i in interesting_blends]

    return interesting_blends







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
    ,dict_certifications
    ,True)
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
target_color = 110
contract_prices_list = df_available_coffee["Standard Cost"].to_numpy().reshape(-1, 1)
# =============================================================================
# TEMP test data above for testing functions
# =============================================================================





all_blends_incl_proportions = get_blends_with_proportions(
    request_item
    ,request_proportion
    ,items
    ,4)



best_fitting_blends = get_best_fitting_blends(
    all_blends_incl_proportions
    ,contract_prices_list
    ,flavor_predictor
    ,flavors_list
    ,target_flavor_list
    ,target_color
    ,50)


# =============================================================================
# predicted_fitness = [float(tpo.blend_fitness(
#     all_blends_incl_proportions[i]
#     ,contract_prices_list
#     ,flavor_predictor
#     ,flavors_list
#     ,target_flavor_list
#     ,target_color)) for i in range(len(all_blends_incl_proportions))]
# predicted_fitness_top_list = sorted(predicted_fitness,reverse=True)[:50]
# interesting_blends = [i for i in range(len(predicted_fitness)) if predicted_fitness[i] in predicted_fitness_top_list]
# interesting_blends = [all_blends_incl_proportions[i] for i in interesting_blends]
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

