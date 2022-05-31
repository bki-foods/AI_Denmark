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

# Temp variables, change to values from query
items = list(range(11))
request_item = 3
request_proportion = 5



def get_blends_with_proportions(required_item: int, min_proportion: int, available_items: list, number_of_components: int) -> list:


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
    ranges_proportions_remaining_items = {
         2: [i for i in range(5,101 - min_proportion,5)]
        ,3: [i for i in range(5,96 - min_proportion,5)]
        ,4: [i for i in range(5,91 - min_proportion ,5)]
        ,5: [i for i in range(5,86 - min_proportion,5)]
        ,6: [i for i in range(5,81 - min_proportion,5)]
        ,7: [i for i in range(5,76 - min_proportion,5)]}
  
    # Remove the requested contract from the list of possible contracts
    available_items = [item for item in available_items if item != required_item]  
    
    # Proportion for the requested component will always be the last element in the list of proportions
    # Get all possible proportion combinations
    proportions = [list(comb) for comb in itertools.combinations_with_replacement(ranges_proportions_remaining_items[number_of_components], number_of_components -1)]
    
    # Create a list of missing proportions such that each blend will sum to 100
    missing_proportions = [100 - sum(props) for props in proportions]
    proportions = list(zip(missing_proportions, proportions))
    # Append the requested component proportion to the list of proportions.
    [props[1].append(props[0]) for props in proportions]
    # Only keep the proportion combinations which sum to 100 and prop >= requested proportion
    proportions = [props[1] for props in proportions if sum(props[1]) == 100 and props[1][-1] >= min_proportion]    
    # Get all possible blend combinations
    blends = [list(contract) for contract in itertools.permutations(available_items, number_of_components -1)]
    # Add requested blend item as last value in blends to correspond with proportions
    blends = [blend + [required_item] for blend in blends]
    
    # Combine proportions and contracts into final list
    blends_prop = list(itertools.product(blends, proportions))
    
    # Clear variables from memory
    del blends,proportions,missing_proportions
    
    return blends_prop


for i in range(1,8):
    xyz = get_blends_with_proportions(
        request_item
        ,5
        ,items
        ,i)
    print("i: " + str(i) + "\n", len(xyz)) if xyz else None

# =============================================================================
# xyz = get_blends_with_proportions(
#     request_item
#     ,request_proportion
#     ,items
#     ,5)
# =============================================================================




# Grab Currrent Time After Running the Code for logging of total execution time
end_time = time.time()
total_time = end_time - start_time
#Subtract Start Time from The End Time
total_time_seconds = int(total_time) % 60
total_time_minutes = total_time // 60
total_time_hours = total_time // 60
execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))

print(execution_time)

