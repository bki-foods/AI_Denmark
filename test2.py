# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 15:01:02 2022

@author: nmo
"""

padding_items = [-1,-1]
padding_props = [0,0]

suggestions = [
    ([0, 1, 2, 4, 3], [5, 5, 5, 5, 80])
    ,([0, 1, 2, 4, 3], [5, 5, 5, 10, 75])
    ,([0, 1, 2, 4, 3], [5, 5, 5, 15, 70])]

suggestions2 = [blend[0] + padding_items for blend in suggestions]
suggestions3 = [blend[1] + list(padding_props) for blend in suggestions]


test = [list(zip(suggestions2[i],suggestions3[i])) for i in range(len(suggestions2))]




proportions = [[5, 5, 5, 85, 0, 0, 0], [5, 5, 10, 80, 0, 0, 0], [5, 5, 15, 75, 0, 0, 0], [5, 5, 20, 70, 0, 0, 0], 
               [5, 5, 25, 65, 0, 0, 0], [5, 5, 30, 60, 0, 0, 0], [5, 5, 35, 55, 0, 0, 0], [5, 5, 40, 50, 0, 0, 0], 
               [5, 5, 45, 45, 0, 0, 0], [5, 5, 50, 40, 0, 0, 0], [5, 5, 55, 35, 0, 0, 0], [5, 5, 60, 30, 0, 0, 0], 
               [5, 5, 65, 25, 0, 0, 0], [5, 5, 70, 20, 0, 0, 0], [5, 5, 75, 15, 0, 0, 0], [5, 5, 80, 10, 0, 0, 0]]

prop_temp = []
for i in range(len(proportions)):
    blend_props_temp = []
    for prop in proportions[i]:
        blend_props_temp.append(prop / 100.0)
        


tester = [i / 100.0 for i in range(5, 101 - 5, 5)]