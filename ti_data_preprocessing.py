import math

from bki_opt.coffee_data_connection import CoffeeDataConnection
import pandas as pd
import numpy as np


def get_raw_flavor_data(con: CoffeeDataConnection, robusta=True):
    """
    Get the raw flavor data from the database. Used to get training data for the ML model.
    :param con: A CoffeeDataConnection that is connected to the data we want to use (either database or excel file)
    :param robusta: Boolean for whether or not to consider robusta flavor.
    :return raw_grades: All the raw flavor grades from the given database.
    """
    if (robusta):
        raw_grades = con.get_gc_grades() \
            [["Dato", "Kontraktnummer", "Modtagelse", "Status", "Syre", "Krop", "Aroma", "Eftersmag", "Robusta"]] \
            .rename(columns={"Dato": "Dato_r",
                             "Status": "Status_r",
                             "Syre": "Syre_r",
                             "Krop": "Krop_r",
                             "Aroma": "Aroma_r",
                             "Eftersmag": "Eftersmag_r",
                             "Robusta": "Robusta_r"})
        raw_grades["Robusta_r"] = raw_grades["Robusta_r"].fillna(10)
        raw_grades = raw_grades.dropna(subset=["Kontraktnummer", "Modtagelse", "Dato_r", "Status_r", "Syre_r", "Krop_r",
                                               "Aroma_r", "Eftersmag_r", "Robusta_r"]) \
                               .drop_duplicates(subset=["Kontraktnummer"])

    else:
        raw_grades = con.get_gc_grades() \
            [["Dato", "Kontraktnummer", "Modtagelse", "Status", "Syre", "Krop", "Aroma", "Eftersmag"]] \
            .rename(columns={"Dato": "Dato_r",
                             "Status": "Status_r",
                             "Syre": "Syre_r",
                             "Krop": "Krop_r",
                             "Aroma": "Aroma_r",
                             "Eftersmag": "Eftersmag_r"}) \
            .dropna(subset=["Kontraktnummer", "Modtagelse",  "Dato_r", "Status_r", "Syre_r", "Krop_r", "Aroma_r",
                            "Eftersmag_r"]) \
            .drop_duplicates(subset=["Kontraktnummer"])

    return raw_grades



def get_blend_grade_data(con: CoffeeDataConnection, robusta=True):
    """
    Get the flavor data of the raw input coffee linked to the flavor data of the final output product for all products
    and raw input in the database.
    :param con: A CoffeeDataConnection that is connected to the data we want to use (either database or excel file)
    :param robusta: Boolean for whether or not to consider robusta flavor.
    :return X_list, Y_list: A dataset of all the input flavors (X) for every blend produced in the database coupled with
        the flavor of the corresponding output product (Y).
    """
    robusta_sorts = (10102120, 10102130, 10102170, 10102180, 10103420)

    contracts = con.get_coffee_contracts()[["Kontraktnummer", "Sort"]]
    recipes = con.get_recipe_information()[["Receptnummer", "Farve sætpunkt"]].rename(columns={"Farve sætpunkt": "Farve"})
    roaster_input = con.get_roaster_input() \
        [["Dato", "Produktionsordre id", "Batch id", "Kontraktnummer", "Modtagelse", "Kilo"]] \
        .rename(columns={"Dato": "Dato_rist",
                         "Kilo": "Kilo_rist_input"}) \
        .dropna()

    roaster_output = con.get_roaster_output().dropna(subset=["Ordrenummer"]).astype({"Ordrenummer": np.int64}) \
        [["Produktionsordre id", "Batch id", "Ordrenummer", "Receptnummer", "Kilo"]] \
        .rename(columns={"Kilo": "Kilo_rist_output",
                         "Ordrenummer": "Ordre_rist"}) \
        .dropna()

    if (robusta):
        raw_grades = con.get_gc_grades() \
            [["Dato", "Kontraktnummer", "Modtagelse", "Status", "Syre", "Krop", "Aroma", "Eftersmag", "Robusta"]] \
            .rename(columns={"Dato": "Dato_r",
                             "Status": "Status_r",
                             "Syre": "Syre_r",
                             "Krop": "Krop_r",
                             "Aroma": "Aroma_r",
                             "Eftersmag": "Eftersmag_r",
                             "Robusta": "Robusta_r"})
        raw_grades['Robusta_r'] = raw_grades['Robusta_r'].fillna(10)
        raw_grades = raw_grades.dropna(subset=["Kontraktnummer", "Dato_r", "Status_r", "Syre_r", "Krop_r", "Aroma_r",
                                               "Eftersmag_r", "Robusta_r"])

        product_grades = con.get_finished_goods_grades() \
            [["Dato", "Ordrenummer", "Status", "Syre", "Krop", "Aroma", "Eftersmag", "Robusta"]] \
            .rename(columns={"Dato": "Dato_p",
                             "Ordrenummer": "Ordre_p",
                             "Status": "Status_p",
                             "Syre": "Syre_p",
                             "Krop": "Krop_p",
                             "Aroma": "Aroma_p",
                             "Eftersmag": "Eftersmag_p",
                             "Robusta": "Robusta_p"})
        product_grades['Robusta_p'] = product_grades['Robusta_p'].fillna(10)
        product_grades = product_grades.dropna().drop_duplicates(subset=["Ordre_p", "Syre_p", "Krop_p", "Aroma_p",
                                                                         "Eftersmag_p", "Robusta_p"])
    else:
        raw_grades = con.get_gc_grades() \
            [["Dato", "Kontraktnummer", "Modtagelse", "Status", "Syre", "Krop", "Aroma", "Eftersmag"]] \
            .rename(columns={"Dato": "Dato_r",
                             "Status": "Status_r",
                             "Syre": "Syre_r",
                             "Krop": "Krop_r",
                             "Aroma": "Aroma_r",
                             "Eftersmag": "Eftersmag_r"}) \
            .dropna(subset=["Kontraktnummer", "Dato_r", "Status_r", "Syre_r", "Krop_r", "Aroma_r",
                            "Eftersmag_r"])

        product_grades = con.get_finished_goods_grades() \
            [["Dato", "Ordrenummer", "Status", "Syre", "Krop", "Aroma", "Eftersmag"]] \
            .rename(columns={"Dato": "Dato_p",
                             "Ordrenummer": "Ordre_p",
                             "Status": "Status_p",
                             "Syre": "Syre_p",
                             "Krop": "Krop_p",
                             "Aroma": "Aroma_p",
                             "Eftersmag": "Eftersmag_p"}) \
            .dropna().drop_duplicates(subset=["Ordre_p", "Syre_p", "Krop_p", "Aroma_p", "Eftersmag_p"])

    raw_grades = raw_grades[raw_grades["Status_r"] == "Godkendt"]
    product_grades = product_grades[product_grades["Status_p"] == "Godkendt"]
    product_grades["Smagningsid"] = list(range(len(product_grades)))

    orders = con.get_order_relationships() \
        .rename(columns={"Ordre": "Ordre_p",
                         "Relateret ordre": "Ordre_rist"}) \
        .dropna()

    roaster_output = pd.merge(roaster_output, recipes, on="Receptnummer")

    res = pd.merge(product_grades, orders, on="Ordre_p")
    res2 = pd.merge(roaster_output, res, on="Ordre_rist")
    res3 = pd.merge(roaster_input, res2, on=["Produktionsordre id", "Batch id"])
    res4 = pd.merge(contracts, res3, on=["Kontraktnummer"])
    res5 = pd.merge(raw_grades, res4, on=["Kontraktnummer", "Modtagelse"], how="right")
    raw_success = pd.merge(raw_grades, res4, on=["Kontraktnummer", "Modtagelse"], how="inner")
    if robusta:
        missing_raw = res5[res5['Status_r'].isna()] \
            .drop(columns=["Dato_r", "Modtagelse", "Status_r", "Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r",
                           "Robusta_r"]) \
            .drop_duplicates()
    else:
        missing_raw = res5[res5['Status_r'].isna()] \
            .drop(columns=["Dato_r", "Modtagelse", "Status_r", "Syre_r", "Krop_r", "Aroma_r", "Eftersmag_r"]) \
            .drop_duplicates()

    found_raw = pd.merge(missing_raw, raw_grades, on="Kontraktnummer")
    found_raw = found_raw[found_raw["Dato_r"] < found_raw["Dato_rist"]] \
        .sort_values("Dato_r", ascending=False) \
        .drop_duplicates(subset=["Kontraktnummer", "Produktionsordre id", "Batch id", "Ordre_rist", "Ordre_p"])

    filtered_data = pd.concat([raw_success, found_raw]).sort_values("Dato_r", ascending=False) \
        .drop_duplicates(subset=["Kontraktnummer", "Modtagelse", "Produktionsordre id", "Batch id",
                                 "Ordre_rist", "Ordre_p", "Kilo_rist_input"])

    tasting_ids = list(set(filtered_data["Smagningsid"]))

    X_list = []
    Y_list = []

    for t_id in tasting_ids:
        tasting_data = filtered_data[filtered_data["Smagningsid"] == t_id]
        batch_ids = list(set(tasting_data["Batch id"]))
        prod_ids = list(set(tasting_data["Produktionsordre id"]))

        # If the product contains robusta coffee, we need to do the analysis on "Produktionsordre"-level
        if not set(tasting_data["Sort"]).isdisjoint(robusta_sorts):
            for p_id in prod_ids:
                prod_data = tasting_data[tasting_data["Produktionsordre id"] == p_id]
                full_prod = roaster_input[roaster_input["Produktionsordre id"] == p_id]
                weight_tasted_prod = sum(prod_data["Kilo_rist_input"])
                weight_full_prod = sum(full_prod["Kilo_rist_input"])

                if 1.0 - weight_tasted_prod / weight_full_prod < 0.1:
                    weight_per_contract = prod_data[["Kontraktnummer", "Modtagelse", "Kilo_rist_input"]] \
                        .groupby(["Kontraktnummer", "Modtagelse"]).sum()
                    unique_contracts = prod_data.groupby(["Kontraktnummer", "Modtagelse"]).mean()

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

    return np.array(X_list), np.array(Y_list)
