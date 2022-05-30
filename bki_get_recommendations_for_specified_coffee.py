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
items = list(range(8))
requested_item = 3
requested_proportion = 20
# Remove the requested contract from the list of possible contracts
items = [item for item in items if item != requested_item]


# Dictionary with lists of possible percentages for requested item in blends. Keys indicate no of components in blend.
udfaldsrum_requested_item = {
     1: list([100])
    ,2: [i for i in range(requested_proportion,96,5)]
    ,3: [i for i in range(requested_proportion,91,5)]
    ,4: [i for i in range(requested_proportion,86,5)]
    ,5: [i for i in range(requested_proportion,81,5)]
    ,6: [i for i in range(requested_proportion,76,5)]
    ,7: [i for i in range(requested_proportion,71,5)]}
# Dictionary with lists of possible percentages for components that are not that main component
udfaldsrum_remaining_items = {
     1: None
    ,2: [i for i in range(5,101 - requested_proportion,5)]
    ,3: [i for i in range(5,96 - requested_proportion,5)]
    ,4: [i for i in range(5,91 - requested_proportion ,5)]
    ,5: [i for i in range(5,86 - requested_proportion,5)]
    ,6: [i for i in range(5,81 - requested_proportion,5)]
    ,7: [i for i in range(5,76 - requested_proportion,5)]}
# Dictionary with the max no of input components per blend combination
udfaldsrum_max_components = {
     1: 50
    ,2: 25
    ,3: 25
    ,4: 11
    ,5: 8
    ,6: 7
    ,7: 7}


"""
Ovenfor har jeg en dictionary med alle de mulige ufald af procentandele for den sort, der er anmodet om, samt dens minimum proportion.
Kan jeg anvende den i itertools, for derefter at lave en sekundær itertools der tager højde for at det hele skal summe til 1
"""

no_components = [2,3,4,5,6,7]
iterator = no_components[-4]

# Proportion for the requested component will always be the last element in the list of proportions
# Get all possible proportion combinations
proportions = [list(comb) for comb in itertools.combinations_with_replacement(udfaldsrum_remaining_items[iterator], iterator -1)]

# Get a list of missing proportions to sum to 100
missing_proportion = [100 - sum(props) for props in proportions]

proportions = list(zip(missing_proportion, proportions))

# Append the requested component proportion to the list of proportions.
[props[1].append(props[0]) for props in proportions]
# Only keep the proportion combinations which sum to 100 and prop >= requested proportion
proportions = [props[1] for props in proportions if sum(props[1]) == 100 and props[1][-1] >= requested_proportion]


# Get all possible blend combinations
blends = [list(contract) for contract in itertools.permutations(items, iterator -1)]


blends = list(zip(blends, [requested_item] * len(proportions))) # TODO, not needed?

# [blend[1].append(blend[0]) for blend in blends]
for i in blends:
    print(i[0])
    print(i[1])

# Combine proportions and contracts
blends_prop = list(itertools.product(blends, proportions))



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







# Grab Currrent Time After Running the Code for logging of total execution time
end_time = time.time()
total_time = end_time - start_time
#Subtract Start Time from The End Time
total_time_seconds = int(total_time) % 60
total_time_minutes = total_time // 60
total_time_hours = total_time // 60
execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))

print(execution_time)

