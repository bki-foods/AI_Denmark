#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import statistics
import ti_data_preprocessing as tdp



ind1_collection =[  [(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                  ,[(40, 0.16), (41, 0.06), (52, 0.38), (26, 0.4), (-1, 0), (-1, 0), (-1, 0)]
                  ,[(40, 0.16), (41, 0.06), (52, 0.38), (26, 0.4), (-1, 0), (-1, 0), (-1, 0)]
                  ,[(40, 0.16), (41, 0.06), (52, 0.38), (26, 0.4), (-1, 0), (-1, 0), (-1, 0)]
                  ,[(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]]
ind2_collection = [ [(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
                   ,[(3, 0.06), (38, 0.18), (40, 0.6), (18, 0.07), (21, 0.09), (-1, 0), (-1, 0)]
                   ,[(16, 0.22), (18, 0.58), (52, 0.06), (21, 0.06), (54, 0.08), (-1, 0), (-1, 0)]
                   ,[(19, 0.66), (44, 0.12), (16, 0.08), (35, 0.07), (40, 0.07), (-1, 0), (-1, 0)]
                   ,[(8, 0.07), (16, 0.24), (49, 0.07), (19, 0.07), (31, 0.55), (-1, 0), (-1, 0)]
                   ,[(40, 0.25), (10, 0.34), (25, 0.06), (26, 0.29), (27, 0.06), (-1, 0), (-1, 0)]
                   ,[(35, 0.21), (6, 0.44), (7, 0.06), (12, 0.23), (54, 0.06), (-1, 0), (-1, 0)]
                   ,[(7, 0.07), (8, 0.09), (40, 0.11), (49, 0.37), (22, 0.36), (-1, 0), (-1, 0)]
                   ,[(50, 0.06), (57, 0.28), (26, 0.08), (27, 0.51), (30, 0.07), (-1, 0), (-1, 0)]
                   ,[(37, 0.16), (15, 0.11), (16, 0.2), (17, 0.14), (31, 0.39), (-1, 0), (-1, 0)]
                   ,[(37, 0.06), (6, 0.12), (48, 0.28), (53, 0.21), (31, 0.33), (-1, 0), (-1, 0)]
                   ,[(9, 0.16), (13, 0.2), (15, 0.31), (21, 0.17), (31, 0.16), (-1, 0), (-1, 0)]]

no_collections = range(len(ind1_collection))

ind1 = [(9, 0.06), (13, 0.3), (15, 0.21), (21, 0.27), (31, 0.16), (-1, 0), (-1, 0)]
ind2 = [(9, 0.16), (13, 0.2), (15, 0.31), (21, 0.17), (31, 0.16), (-1, 0), (-1, 0)]


def equal_blends(ind1, ind2):
    #TODO: Blends er identiske hvis de indeholder de samme kontrakter, uagtet proportionerne
    comp1 = [ind1[i][0] for i in range(len(ind1)) if ind1[i][0] != -1]
    comp2 = [ind2[i][0] for i in range(len(ind2)) if ind2[i][0] != -1]
    return set(comp1) == set(comp2)

def blends_too_equal(blend1, blend2) -> bool:
    """
    Compares two proposed blends of coffees. If they do not contain exactly the same components,
    they are deemed different. If they contain the exact same components, they are deemed different enough
    if any of the ABS differences in proportions are >= 0.1.
    Returns bool
    """
    
    # Get list of components in each blend, -1 to remove placeholder values
    blend_1_components = [blend1[i][0] for i in range(len(blend1)) if blend1[i][0] != -1]
    blend_2_components = [blend2[i][0] for i in range(len(blend2)) if blend2[i][0] != -1]
    # Do blends contain same items. If not they are different already
    blends_too_equal = set(blend_1_components) == set(blend_2_components)
    # If both blends contain same items, compare proportions
    if blends_too_equal:
        # Get lists of proportions for each blend
        blend_1_proportions = [blend1[i][1]  for i in range(len(blend1)) if blend1[i][0] != -1]
        blend_2_proportions = [blend2[i][1]  for i in range(len(blend2)) if blend2[i][0] != -1]
        # Get the ABS difference between the blends. Round to prevent issues with floats
        blends_differences = [round(abs(b1 - b2),2) for b1, b2 in zip(blend_1_proportions, blend_2_proportions)]
        # # Blends are different enough if the mean ABS change is >= 0.1 across components
        # blends_different_enough = ( sum(blends_differences) / len(blend_1_components) ) >= 0.1
        # Blends are different enough if any component has had its proportion changed by 0.1 or more
        # blends_too_equal = not any(diff >= 0.1 for diff in blends_differences)
        blends_too_equal = statistics.mean(blends_differences) < 0.05
    return blends_too_equal


for i in no_collections:
    print("i: ",i, "\torg: " ,equal_blends(ind1_collection[i], ind2_collection[i]), "\tnew: ", blends_too_equal(ind1_collection[i], ind2_collection[i]))


# Blend 0 skal være True i new, blend 11 skal være true i org, false i NEW



datacleaning_df = tdp.get_blend_grade_data(False)[2]





