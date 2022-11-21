#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bki_functions as bf
import pandas as pd
import numpy as np


import sys

robusta = False

# Define bar_recipes for later use to determine whether to proces on batch or production order level
bar_recipes = ('10401005','10401207')
# Get data for coffee contracts
contracts = bf.get_coffee_contracts()[["Kontraktnummer", "Sort"]]
# Get data about recipes
recipes = bf.get_recipe_information()[["Receptnummer", "Farve sætpunkt"]].rename(columns={"Farve sætpunkt": "Farve"})
# Get all potentially relevant roaster input (green coffee consumption)
roaster_input = bf.get_roaster_input() \
    [["Dato", "Produktionsordre id", "Batch id", "Kontraktnummer", "Modtagelse", "Kilo"]] \
    .rename(columns={"Dato": "Dato_rist",
                     "Kilo": "Kilo_rist_input"}) \
    .dropna()
# Get all potentially relevant roaster output
roaster_output = bf.get_roaster_output().dropna(subset=["Ordrenummer"]).astype({"Ordrenummer": np.int64}) \
    [["Produktionsordre id", "Batch id", "Ordrenummer", "Receptnummer", "Kilo"]] \
    .rename(columns={"Kilo": "Kilo_rist_output",
                     "Ordrenummer": "Ordre_rist"}) \
    .dropna()
# Get grades for the green coffees
raw_grades = bf.get_gc_grades() \
    [["Dato", "Kontraktnummer", "Modtagelse", "Syre", "Krop", "Aroma", "Eftersmag", "Robusta"]] \
    .rename(columns={"Dato": "Dato_r",
                     "Syre": "Syre_r",
                     "Krop": "Krop_r",
                     "Aroma": "Aroma_r",
                     "Eftersmag": "Eftersmag_r",
                     "Robusta": "Robusta_r"})
raw_grades["Robusta_r"].fillna(10, inplace=True)
raw_grades = raw_grades.dropna(subset=["Kontraktnummer", "Dato_r", "Syre_r", "Krop_r", "Aroma_r",
                                       "Eftersmag_r"])

# Get grades for the finished products
product_grades = bf.get_finished_goods_grades() \
    [["Dato", "Ordrenummer", "Syre", "Krop", "Aroma", "Eftersmag", "Robusta"]] \
    .rename(columns={"Dato": "Dato_p",
                     "Ordrenummer": "Ordre_p",
                     "Syre": "Syre_p",
                     "Krop": "Krop_p",
                     "Aroma": "Aroma_p",
                     "Eftersmag": "Eftersmag_p",
                     "Robusta": "Robusta_p"})
product_grades["Robusta_p"] = product_grades["Robusta_p"].fillna(10)
product_grades = product_grades.dropna() \
    .drop_duplicates(subset=["Ordre_p", "Syre_p", "Krop_p", "Aroma_p","Eftersmag_p"]) \
    .astype({"Ordre_p": np.int64})

# Remove robusta columns from dataset if they are not be used for training the model    
if not robusta:
    raw_grades.drop("Robusta_r", inplace=True, axis=1)
    product_grades.drop("Robusta_p", inplace=True, axis=1)

product_grades["Smagningsid"] = list(range(len(product_grades)))

# Get data for the relationships between orders
orders = bf.get_order_relationships() \
    .rename(columns={"Ordre": "Ordre_p",
                     "Relateret ordre": "Ordre_rist"}) \
    .dropna().astype({'Ordre_p': np.int64,'Ordre_rist': np.int64})

# Merge all relevant tables
roaster_output = pd.merge(roaster_output, recipes, on="Receptnummer")

res = pd.merge(product_grades, orders, on="Ordre_p")
res2 = pd.merge(roaster_output, res, on="Ordre_rist")
res3 = pd.merge(roaster_input, res2, on=["Produktionsordre id", "Batch id"])
res4 = pd.merge(contracts, res3, on=["Kontraktnummer"])
res5 = pd.merge(raw_grades, res4, on=["Kontraktnummer", "Modtagelse"], how="right")
raw_success = pd.merge(raw_grades, res4, on=["Kontraktnummer", "Modtagelse"], how="inner")

missing_raw = res5[res5["Syre_r"].isna()] \
    .drop(columns=["Dato_r", "Modtagelse", "Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r"]) \
    .drop_duplicates()
if robusta:
    missing_raw.drop("Robusta_r", inplace=True, axis=1)

# If no kontrakt/modtagelse has been defined, use data for the last kontrakt graded before the roasting date
found_raw = pd.merge(missing_raw, raw_grades, on="Kontraktnummer")
found_raw = found_raw[found_raw["Dato_r"] < found_raw["Dato_rist"]] \
    .sort_values("Dato_r", ascending=False) \
    .drop_duplicates(subset=["Kontraktnummer", "Produktionsordre id", "Batch id", "Ordre_rist", "Ordre_p"])

filtered_data = pd.concat([raw_success, found_raw]).sort_values("Dato_r", ascending=False) \
    .drop_duplicates(subset=["Kontraktnummer", "Modtagelse", "Produktionsordre id", "Batch id",
                             "Ordre_rist", "Ordre_p", "Kilo_rist_input"])

max_tasting_id = max(list(set(filtered_data["Smagningsid"]))) + 1



df_agg_bar = filtered_data[filtered_data["Receptnummer"].isin(bar_recipes)].groupby(["Receptnummer","Ordre_p"], dropna=False).agg(
    {"Kilo_rist_input": "sum"}).reset_index()
df_agg_bar_order = df_agg_bar.groupby(["Ordre_p"], dropna=False).agg(
    {"Kilo_rist_input": "sum"})
df_agg_bar = pd.merge(
    left = df_agg_bar
    ,right = df_agg_bar_order
    ,how = "left"
    ,on = "Ordre_p")

df_agg_bar["råkaffe proportion"] = df_agg_bar["Kilo_rist_input_x"] / df_agg_bar["Kilo_rist_input_y"]
bar_weights_recipes = {"10401005":0.65,"10401207":0.35}

df_agg_bar["Faktorfelt"] = df_agg_bar["Receptnummer"].map(bar_weights_recipes).fillna(1) / df_agg_bar["råkaffe proportion"]
df_agg_bar = df_agg_bar[["Receptnummer","Ordre_p","Faktorfelt"]]


filtered_data = pd.merge(
    left = filtered_data
    ,right = df_agg_bar
    ,how = "left"
    ,on = ["Receptnummer","Ordre_p"])
filtered_data["Kilo_rist_input"] = filtered_data["Kilo_rist_input"] * filtered_data["Faktorfelt"].fillna(1)

# Add testing data to dataset
df_testing_data = bf.get_test_roastings(robusta,max_tasting_id)
filtered_data = pd.concat([filtered_data,df_testing_data],ignore_index=True).reset_index()
filtered_data.drop(columns=["index","Faktorfelt"],inplace = True)
# Remove duplicates from tastings and add to roaster input
df_testing_data = df_testing_data[df_testing_data["Komponent id"] == 1]
roaster_input = pd.concat([roaster_input,df_testing_data], ignore_index = True)[roaster_input.columns].reset_index()


sys.exit()

tasting_ids = list(set(filtered_data["Smagningsid"]))
X_list = []
Y_list = []

for t_id in tasting_ids:
    
    tasting_data = filtered_data[filtered_data["Smagningsid"] == t_id]
    batch_ids = list(set(tasting_data["Batch id"]))
    prod_ids = list(set(tasting_data["Produktionsordre id"]))

    # If the produced recipes are used for BAR blends, do the analysis on "Produktionsordre"-level
    if not set(tasting_data['Receptnummer']).isdisjoint(bar_recipes):
        for p_id in prod_ids:
            prod_data = tasting_data[tasting_data["Produktionsordre id"] == p_id]
            full_prod = roaster_input[roaster_input["Produktionsordre id"] == p_id]
            weight_tasted_prod = sum(prod_data["Kilo_rist_input"])
            weight_full_prod = sum(full_prod["Kilo_rist_input"])

            if 1.0 - weight_tasted_prod / weight_full_prod < 0.1: #Use data if we have data for 90% of the production order
                weight_per_contract = prod_data[["Kontraktnummer", "Modtagelse", "Kilo_rist_input"]] \
                    .groupby(["Kontraktnummer", "Modtagelse"]).sum()
                unique_contracts = prod_data.groupby(["Kontraktnummer", "Modtagelse"]).mean()

                if 0 < len(unique_contracts) <= 7: # Only use data if we have 7 or fewer unique contracts used in the order, to ensure same dimensions as our input in the model
                    unique_contracts["Proportion"] = weight_per_contract["Kilo_rist_input"] / \
                                                     sum(weight_per_contract["Kilo_rist_input"])

                    if robusta:
                        x_data = unique_contracts[
                            ["Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r", "Robusta_r", "Proportion"]]
                        y_data = unique_contracts[["Syre_p", "Krop_p", "Aroma_p", "Eftersmag_p", "Robusta_p"]][0:1]
                    else:
                        x_data = unique_contracts[["Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r", "Proportion"]]
                        y_data = unique_contracts[["Syre_p", "Krop_p", "Aroma_p", "Eftersmag_p"]][0:1]

                    x_np = x_data.to_numpy()
                    y_np = y_data.to_numpy()
                    if len(unique_contracts) < 7:
                        x_np = np.pad(x_np, constant_values=0, pad_width=[[0, 7 - len(unique_contracts)], [0, 0]])

                    farve = unique_contracts[["Farve"]][0:1].to_numpy()
                    X_list.append(np.append(x_np.flatten(), farve))
                    Y_list.append(y_np.flatten())
    # Else we can do the processing on "Batch"-level
    else:
        for b_id in batch_ids:
            batch_data = tasting_data[tasting_data["Batch id"] == b_id]
            full_batch = roaster_input[roaster_input["Batch id"] == b_id]
            weight_tasted_batch = sum(batch_data["Kilo_rist_input"])
            weight_full_batch = sum(full_batch["Kilo_rist_input"])
            if 1.0 - weight_tasted_batch / weight_full_batch < 0.1:
                weight_per_contract = batch_data[["Kontraktnummer", "Modtagelse", "Kilo_rist_input"]] \
                    .groupby(["Kontraktnummer", "Modtagelse"]).sum()
                unique_contracts = batch_data.groupby(["Kontraktnummer", "Modtagelse"]).mean()

                if 0 < len(unique_contracts) <= 7:
                    unique_contracts["Proportion"] = weight_per_contract["Kilo_rist_input"] / \
                                                     sum(weight_per_contract["Kilo_rist_input"])

                    if robusta:
                        x_data = unique_contracts[
                            ["Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r", "Robusta_r", "Proportion"]]
                        y_data = unique_contracts[["Syre_p", "Krop_p", "Aroma_p", "Eftersmag_p", "Robusta_p"]][0:1]
                    else:
                        x_data = unique_contracts[["Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r", "Proportion"]]
                        y_data = unique_contracts[["Syre_p", "Krop_p", "Aroma_p", "Eftersmag_p"]][0:1]

                    x_np = x_data.to_numpy()
                    y_np = y_data.to_numpy()
                    if len(unique_contracts) < 7:
                        x_np = np.pad(x_np, constant_values=0, pad_width=[[0, 7 - len(unique_contracts)], [0, 0]])

                    farve = unique_contracts[["Farve"]][0:1].to_numpy()
                    X_list.append(np.append(x_np.flatten(), farve))
                    Y_list.append(y_np.flatten())

X_list = np.array(X_list)
Y_list = np.array(Y_list)


