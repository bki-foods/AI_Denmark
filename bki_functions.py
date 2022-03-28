#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
import bki_server_information as bsi



# Convert list into string for SQL IN operator
def string_to_sql(list_with_values: list) -> str:
    """
    Convert list of values into a single string which can be used for SQL queries IN clauses.
    Input ['a','b','c'] --> Output 'a','b','c'
    \n Parameters
    ----------
    list_with_values : list
        List containing all values which need to be joined into one string
    \n Returns
    -------
    String with comma separated values.
    Returned values are encased in '' when returned.
    """
    if len(list_with_values) == 0:
        return ''
    else:
        return "'{}'".format("','".join(list_with_values))


# Check if script is supposed to exit. 0 value = exit
def get_exit_check(value: int):
    """Calls sys.exit() if input value == 0"""
    if value == 0:
        sys.exit()
    else:
        pass

# Compare two dataframes with specified columns and see if dataframe 2 is missing any values compared to dataframe 1
def get_list_of_missing_values(df_total:pd.DataFrame(), total_column_name:str, df_compare:pd.DataFrame(), compare_column_name:str) -> list:
    """
    Compares the values in two specified columns from two specified dataframes and returns a list of any values present in first dataframe,
    that does not exist in the second.

    Parameters
    ----------
    df_total : pd.DataFrame()
        A dataframe containing rows with all the values which the second dataframe is to be compared to.
    total_column_name : str
        Name of the column with values which are to be compared with .
    df_compare : pd.DataFrame()
        A dataframe containing rows with values which are to be compared to the first dataframe.
    compare_column_name : str
        Name of the column with values which are to be compared with the first dataframe.

    Returns
    -------
    missing_values : List
        Returns a list with all values present in the first dataframe that cannot be found in the second dataframe..
    """
    total_values_list = df_total[total_column_name].unique().tolist()
    compare_values_list = df_compare[compare_column_name].unique().tolist()
    missing_values = list(set(total_values_list) - set(compare_values_list))
    return missing_values



# Get information from coffee contracts from Navision
def get_coffee_contracts() -> pd.DataFrame():
    """
    Returns information from Navision for coffee contracts as a Pandas DataFrame.
    """
    query = """ SELECT PH.[No_] AS [Kontraktnummer]	,PH.[Buy-from Vendor No_] AS [Leverandør]
        	,CR.[Name] AS [Oprindelsesland]
            ,CASE WHEN PH.[Harvest] = 0	THEN ''	WHEN PH.[Harvest] = 1 THEN 'Ny'
        		WHEN PH.[Harvest] = 2 THEN 'Gammel' WHEN PH.[Harvest] = 3 THEN 'Blandet' END AS [Høst]
        	,CASE WHEN PH.[Harvest Year] = 0 THEN NULL ELSE PH.[Harvest Year] END AS [Høstår]
        	,PH.[Screen Size] AS [Screensize]
        	,CASE WHEN PH.[Washed Coffee] = 1 THEN 'Vasket'
                WHEN PH.[Washed Coffee] = 0 AND PH.[No_] >= '21-037' THEN 'Uvasket'
        		ELSE NULL END AS [Metode]
        	,PL.[No_] AS [Sort] ,I.[Mærkningsordning] ,PH.[Differentials] AS [Differentiale]
            FROM [dbo].[BKI foods a_s$Purchase Header] AS PH
            INNER JOIN [dbo].[BKI foods a_s$Purchase Line] AS PL
            	ON PH.[No_] = PL.[Document No_]
            	AND [PL].[Line No_] = 10000
            LEFT JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON PL.[No_] = I.[No_]
            LEFT JOIN [dbo].[BKI foods a_s$Country_Region] AS CR
            	ON PH.[Pay-to Country_Region Code] = CR.[Code]
            WHERE PH.[Kontrakt] = 1 """
    df = pd.read_sql(query, bsi.con_nav)
    return df

# Get masterdata for recipes (green coffee blends)
def get_recipe_information() -> pd.DataFrame():
    """
    Returns masterdata for recipes (blends of green coffee) as a pandas DataFrame.
    """
    query = """ SELECT PRI.[CUSTOMER_CODE] AS [Receptnummer]
        	,PRI.[COLOR] AS [Farve sætpunkt] ,I.[Mærkningsordning]
            FROM [dbo].[BKI foods a_s$PROBAT Item] AS PRI
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON PRI.[CUSTOMER_CODE] = I.[No_]
            WHERE PRI.[CUSTOMER_CODE] LIKE '1040%' """
    df = pd.read_sql(query, bsi.con_nav)
    return df


# Get all records for grades given to green coffe
def get_gc_grades() -> pd.DataFrame():
    """
    Returns all grades given to green coffees as a pandas DataFrame.
    Only records where grading has resulted in an approval of the product are included.
    Rejected gradings are excluded since these product would never make it to production.
    Only one of the grading-parameters need to be used for a record to be included.
    Grading done for all of syre, krop, aroma, eftersmag, robusta is not guarenteed.
    """
    query = """ SELECT S.[Dato] ,S.[Bruger] ,S.[Kontraktnummer] ,RRP.[Delivery] AS [Modtagelse]
        	,ST.[Beskrivelse] AS [Smagningstype] ,S.[Smag_Syre] AS [Syre]
        	,S.[Smag_Krop] AS [Krop] ,S.[Smag_Aroma] AS [Aroma]
        	,S.[Smag_Eftersmag] AS [Eftersmag] ,S.[Smag_Robusta] AS [Robusta]
        	,CASE WHEN S.[Status] = 1 THEN 'Godkendt' 
                WHEN S.[Status] = 0 THEN 'Afvist' ELSE 'Ej smagt' END AS [Status]
        	,S.[Bemærkning]
            FROM [cof].[Smageskema] AS S
            LEFT JOIN [cof].[Smagningstype] AS ST
            	ON S.[Smagningstype] = ST.[Id]
            LEFT JOIN [cof].[Risteri_råkaffe_planlægning] AS RRP
            	ON S.[Id_org] = RRP.[Id]
            	AND S.[Id_org_kildenummer] = 1
            WHERE S.[Kontraktnummer] IS NOT NULL
            	AND COALESCE(S.[Smag_Syre],S.[Smag_Krop],S.[Smag_Aroma],S.[Smag_Eftersmag],S.[Smag_Robusta]) IS NOT NULL
            AND S.[Status] = 1 """
    df = pd.read_sql(query, bsi.con_ds)
    return df

# Get all records for grades given to finished goods
def get_finished_goods_grades() -> pd.DataFrame():
    """
    Returns all grades given to finished goods as a pandas DataFrame.
    Records are included whether or not the finished product has been approved or rejected.
    Any given order number 'ordrenummer' may have multiple records related to it.
    Only one of the grading-parameters need to be used for a record to be included.
    Grading done for all of syre, krop, aroma, eftersmag, robusta is not guarenteed.
    """
    query = """ SELECT S.[Dato] ,S.[Bruger] ,S.[Referencenummer] AS [Ordrenummer]
        	,S.[Smag_Syre] AS [Syre] ,S.[Smag_Krop] AS [Krop] ,S.[Smag_Aroma] AS [Aroma]
        	,S.[Smag_Eftersmag] AS [Eftersmag] ,S.[Smag_Robusta] AS [Robusta]
        	,CASE WHEN S.[Status] = 1 THEN 'Godkendt' WHEN S.[Status] = 0 THEN 'Afvist'
        		ELSE 'Ej smagt' END AS [Status]
        	,S.[Bemærkning] ,KP.[Silo]
            FROM [cof].[Smageskema] AS S
            LEFT JOIN [cof].[Kontrolskema_prøver] AS KP
            	ON S.[Id_org] = KP.[Id]
            	AND S.[Id_org_kildenummer] = 6
            WHERE COALESCE(S.[Smag_Syre],S.[Smag_Krop],S.[Smag_Aroma],S.[Smag_Eftersmag],S.[Smag_Robusta]) IS NOT NULL
            	AND S.[Referencetype] = 2
            	AND S.[Referencenummer] IS NOT NULL
                AND S.[Varenummer] NOT LIKE '1090%' """
    df = pd.read_sql(query, bsi.con_ds)
    return df

# Get all related orders from Navision for orders which have been given a grade
def get_nav_order_related() -> pd.DataFrame():
    """
    Returns a set of orders and the directly related orders from Navision returned as a pandas DataFrame.
    """
    # Get dataframe with orders given grades, convert til liste and string used for SQL query.
    df_orders = get_finished_goods_grades()
    graded_orders_list = df_orders['Ordrenummer'].unique().tolist()
    po_sql_string = string_to_sql(graded_orders_list)
    # Get related orders from Navision
    query_nav_order_related = f""" SELECT [Prod_ Order No_] AS [Ordre]
                                   ,[Reserved Prod_ Order No_] AS [Relateret ordre]
                                   FROM [dbo].[BKI foods a_s$Reserved Prod_ Order No_]
                                   WHERE [Prod_ Order No_] IN ({po_sql_string})
                                   AND [Invalid] = 0 """
    df_nav_order_related = pd.read_sql(query_nav_order_related, bsi.con_nav)
    return df_nav_order_related

# Get all related orders from Probat for remainder of orders, which have no reservations in Navision
def get_probat_orders_related() -> pd.DataFrame():
    """
    Returns a set of orders and the directly related orders from Probat returned as a pandas DataFrame.
    Only returns orders which have no relationships defined in Navision
    """
    # Get a list of orders which do not have valid relationships defined in Navision
    orders_to_search = get_list_of_missing_values(get_finished_goods_grades()
                                                  ,'Ordrenummer'
                                                  ,get_nav_order_related()
                                                  ,'Ordre')
    # Convert list to a string valid for SQL query
    sql_search_string = string_to_sql(orders_to_search)

    query = f""" WITH CTE_ORDERS AS (
                SELECT [ORDER_NAME] AS [Ordre] ,[S_ORDER_NAME] AS [Relateret ordre]
                FROM [dbo].[PRO_EXP_ORDER_SEND_PG]
                WHERE [S_ORDER_NAME] <> 'Retour Ground' AND [ORDER_NAME] <> ''
                GROUP BY [ORDER_NAME],[S_ORDER_NAME]
                UNION ALL
                SELECT [ORDER_NAME] AS [Ordre] ,[S_ORDER_NAME] AS [Relateret ordre]
                FROM [dbo].[PRO_EXP_ORDER_SEND_PB]
                WHERE [S_ORDER_NAME] <> 'Retour Ground' AND [ORDER_NAME] <> ''
                GROUP BY [ORDER_NAME],[S_ORDER_NAME]
                )
                SELECT *
                FROM CTE_ORDERS
                WHERE [Ordre] IN ({sql_search_string}) """
    df = pd.read_sql(query, bsi.con_probat)
    return df

# Get roasting orders from grinding orders from Probat
def get_order_relationships() -> pd.DataFrame():
    """
    Adds roasting orders to the complete dataframe with Navision and Probat related orders.
    Returns a new dataframe with roasting orders added
    """
    # Read all orders from Probat. Roasting orders are unioned to ease data transformation in final df.
    query = """ SELECT [ORDER_NAME],[S_ORDER_NAME]
                FROM [dbo].[PRO_EXP_ORDER_LOAD_G]
                WHERE [S_ORDER_NAME] <> 'REWORK ROAST'
                GROUP BY [ORDER_NAME],[S_ORDER_NAME]
                UNION ALL
                SELECT [ORDER_NAME],[ORDER_NAME]
                FROM [dbo].[PRO_EXP_ORDER_UNLOAD_R]
                WHERE [ORDER_NAME] IS NOT NULL
                GROUP BY [ORDER_NAME],[ORDER_NAME] """
    df_orders = pd.read_sql(query, bsi.con_probat)
    # Get a dataframe with Probat and Navision relationships unioned.
    df_orders_total = pd.concat([get_nav_order_related(), get_probat_orders_related()])
    # Left join roasting orders on df_orders_total
    df_with_roasting_orders = pd.merge(
                                df_orders_total
                                ,df_orders
                                ,left_on='Relateret ordre'
                                ,right_on='ORDER_NAME'
                                ,how='left')
    # Prepare final dataframe
    df_orders_final = pd.DataFrame()
    df_orders_final[['Ordre','Relateret ordre']] = df_with_roasting_orders[['Ordre','S_ORDER_NAME']]
    df_orders_final.dropna(inplace=True)
    return df_orders_final


# Get input coffees used for roasting orders identified
def get_roaster_input() -> pd.DataFrame():
    """
    Returns the input of green coffee used for roasting orders identified as used in a finished product.
    """
    # Get dataframe, list and concatenated string for sql with relevant order numbers
    df_orders = get_order_relationships()
    orders_list = df_orders['Relateret ordre'].unique().tolist()
    orders_sql = string_to_sql(orders_list)
    # Query Probat for records
    query = f""" SELECT	[RECORDING_DATE] AS [Dato] ,[DESTINATION] AS [Rister]
                ,[PRODUCTION_ORDER_ID] AS [Produktionsordre id]
                ,[BATCH_ID] AS [Batch id],[SOURCE] AS [Kilde silo]
                ,[S_CONTRACT_NO] AS [Kontraktnummer],[S_DELIVERY_NAME] AS [Modtagelse]
                ,[S_TYPE_CELL] AS [Sortnummer i silo] ,[WEIGHT] / 1000.0 AS [Kilo]
                FROM [dbo].[PRO_EXP_ORDER_LOAD_R]
                WHERE [ORDER_NAME] IN ({orders_sql}) """
    df = pd.read_sql(query, bsi.con_probat)
    return df


# Get input coffees used for roasting orders identified
def get_roaster_output() -> pd.DataFrame():
    """
    Returns the output of roasting orders identified as used in a finished product.
    """
    # Get dataframe, list and concatenated string for sql with relevant order numbers
    df_orders = get_order_relationships()
    orders_list = df_orders['Relateret ordre'].unique().tolist()
    orders_sql = string_to_sql(orders_list)
    # Query Probat for records
    query = f""" WITH G AS (
                SELECT LG.[S_PRODUCT_ID] ,MAX(ULG.[DEST_NAME]) AS [Silo]
                FROM [dbo].[PRO_EXP_ORDER_LOAD_G] AS LG
                INNER JOIN [dbo].[PRO_EXP_ORDER_UNLOAD_G] AS ULG
                	ON LG.[BATCH_ID] = ULG.[BATCH_ID]
                GROUP BY LG.[S_PRODUCT_ID] )
                , ULR AS (
                SELECT ULR.[PRODUCTION_ORDER_ID] AS [Produktionsordre id]
                ,ULR.[BATCH_ID] AS [Batch id] ,ULR.[ORDER_NAME] AS [Ordrenummer]
               	,ULR.[S_CUSTOMER_CODE] AS [Receptnummer] ,ULR.[DEST_NAME] AS [Silo]
               	,ULR.[S_PRODUCT_ID] ,SUM(ULR.[WEIGHT]) / 1000.0 AS [Kilo]
                FROM [dbo].[PRO_EXP_ORDER_UNLOAD_R] AS ULR
                GROUP BY ULR.[PRODUCTION_ORDER_ID] ,ULR.[BATCH_ID]
                ,ULR.[ORDER_NAME], ULR.[S_CUSTOMER_CODE]
                ,ULR.[DEST_NAME] ,ULR.[S_PRODUCT_ID] )
                SELECT ULR.[Produktionsordre id] ,ULR.[Batch id]
                ,ULR.[Ordrenummer] ,ULR.[Receptnummer] ,ULR.[Kilo]
                ,COALESCE(G.[Silo],ULR.[Silo]) AS [Silo]
                FROM ULR
                LEFT JOIN G
                	ON ULR.[S_PRODUCT_ID] = G.[S_PRODUCT_ID]
                WHERE ULR.[Ordrenummer] IN ({orders_sql}) """
    df = pd.read_sql(query, bsi.con_probat)
    return df


# =============================================================================
# temp_list = get_list_of_missing_values(get_finished_goods_grades()
#                                         ,'Ordrenummer'
#                                         ,get_order_relationships()
#                                         ,'Ordre')
# print(temp_list)
# =============================================================================













# Read top 1 record of blend request log
def get_ds_blend_request() -> pd.DataFrame():
    """
    Returns a pandas dataframe with the top 1 record from BKI_Datastore which has not been started or completed.
    Returns columns from database with same names as they exist in source table.
    If no non-started or non-completed records exists, sys.exit() is called to terminate script.
    """
    query = 'SELECT TOP 1 * FROM [cof].[Receptforslag_log] WHERE [Status] = 0'
    df = pd.read_sql(query, bsi.con_ds)
    # Call function to exit script if no data exists from query
    get_exit_check(len(df))
    # If script has not been terminated, return dataframe with data
    return df

def get_spot_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from SPOT."""
    query = """ SELECT PL.[Document No_] AS [Kontraktnummer],PL.[Location Code] AS [Lokation]
                    ,PL.[Outstanding Quantity] AS [Beholdning]
            FROM [dbo].[BKI foods a_s$Purchase Line] AS PL
            INNER JOIN [dbo].[BKI foods a_s$Purchase Header] AS PH
            	ON PL.[Document No_] = PH.[No_]
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON PL.[No_] = I.[No_]
            WHERE PL.[Type] = 2	AND PL.[Location Code] = 'SPOT'
            	AND PL.[Outstanding Quantity] > 0 AND PH.[Kontrakt] = 1
            	AND I.[Item Category Code] = 'RÅKAFFE'
            UNION ALL
            SELECT ILE.[Coffee Batch No_] ,ILE.[Location Code]
                ,SUM(ILE.[Remaining Quantity]) AS [Qty]
            FROM [dbo].[BKI foods a_s$Item Ledger Entry] AS ILE
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON ILE.[Item No_]= I.[No_]
            WHERE ILE.[Remaining Quantity] > 0 AND ILE.[Location Code] = 'SPOT'
            	AND I.[Item Category Code] = 'RÅKAFFE'
            GROUP BY ILE.[Coffee Batch No_] ,ILE.[Location Code] """
    df = pd.read_sql(query, bsi.con_nav)
    return df

def get_havn_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from AARHUSHAVN & EKSLAGER2."""
    query = """ SELECT ILE.[Coffee Batch No_] AS [Kontraktnummer]
                ,'AARHUSHAVN' AS [Lokation] ,SUM(ILE.[Remaining Quantity]) AS [Beholdning]
            FROM [dbo].[BKI foods a_s$Item Ledger Entry] AS ILE
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON ILE.[Item No_]= I.[No_]
            WHERE ILE.[Remaining Quantity] > 0 AND ILE.[Location Code] IN ('AARHUSHAVN','EKSLAGER2')
            	AND I.[Item Category Code] = 'RÅKAFFE'
            GROUP BY ILE.[Coffee Batch No_] """
    df = pd.read_sql(query, bsi.con_nav)
    return df

def get_udland_available_quantities() -> pd.DataFrame():
    """ Returns a dataframe with all available coffee from Udland."""
    query = """ SELECT PL.[Document No_] AS [Kontraktnummer],PL.[Location Code] AS [Lokation]
                    ,PL.[Outstanding Quantity] AS [Beholdning]
            FROM [dbo].[BKI foods a_s$Purchase Line] AS PL
            INNER JOIN [dbo].[BKI foods a_s$Purchase Header] AS PH
            	ON PL.[Document No_] = PH.[No_]
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON PL.[No_] = I.[No_]
            WHERE PL.[Type] = 2	AND PL.[Location Code] = 'UDLAND'
            	AND PL.[Outstanding Quantity] > 0 AND PH.[Kontrakt] = 1
            	AND I.[Item Category Code] = 'RÅKAFFE' """
    df = pd.read_sql(query, bsi.con_nav)
    return df

def get_afloat_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from AARHUSHAVN & EKSLAGER2."""
    query = """ SELECT ILE.[Coffee Batch No_] AS [Kontraktnummer]
                ,ILE.[Location Code] AS [Lokation] ,SUM(ILE.[Remaining Quantity]) AS [Beholdning]
            FROM [dbo].[BKI foods a_s$Item Ledger Entry] AS ILE
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON ILE.[Item No_]= I.[No_]
            WHERE ILE.[Remaining Quantity] > 0 AND ILE.[Location Code] = 'AFLOAT'
            	AND I.[Item Category Code] = 'RÅKAFFE'
            GROUP BY ILE.[Coffee Batch No_] ,ILE.[Location Code] """
    df = pd.read_sql(query, bsi.con_nav)
    return df


def get_silos_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from 000 and 200-silos from Probat."""
    query = """ SELECT  'SILOER' AS [Lokation] ,[Kontrakt] AS [Kontraktnummer]
            ,[Modtagelse] ,SUM([Kilo]) AS [Beholdning]
            FROM [dbo].[Newest total inventory]
            WHERE [Placering] = '0000' OR [Placering] LIKE '2__'
            GROUP BY [Kontrakt],[Modtagelse] """
    df = pd.read_sql(query, bsi.con_probat)
    return df

def get_warehouse_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from Warehouse from Probat."""
    query = """ SELECT  'WAREHOUSE' AS [Lokation] ,[Kontrakt] AS [Kontraktnummer]
            ,[Modtagelse] ,SUM([Kilo]) AS [Beholdning]
            FROM [dbo].[Newest total inventory]
            WHERE [Placering] = 'Warehouse'
            GROUP BY [Kontrakt],[Modtagelse] """
    df = pd.read_sql(query, bsi.con_probat)
    return df


def get_all_available_quantities(request_dataframe) -> pd.DataFrame():
    """Returns a dataframe with all available coffee from all locations that have been
        selected when the request was made.
        Variable 'request_dataframe' must contain all columns from the request log.
        If input dataframe contains multiple rows, only the first row is used."""
    # Create dataframe with all available coffees
    df = pd.concat([
        get_spot_available_quantities(),
        get_havn_available_quantities(),
        get_udland_available_quantities(),
        get_afloat_available_quantities(),
        get_silos_available_quantities(),
        get_warehouse_available_quantities()
        ])
    # Set variables for which locations are to be included.
    dict_locations = {
        'SILOER': request_dataframe['Lager_siloer'].iloc[0],
        'WAREHOUSE': request_dataframe['Lager_warehouse'].iloc[0],
        'AARHUSHAVN': request_dataframe['Lager_havn'].iloc[0],
        'SPOT': request_dataframe['Lager_spot'].iloc[0],
        'AFLOAT': request_dataframe['Lager_afloat'].iloc[0],
        'UDLAND': request_dataframe['Lager_udland'].iloc[0]
        }
    # Minimum available amount of coffee for an item to be included
    min_quantity = request_dataframe['Minimum_lager'].iloc[0]
    # Map dictionary to dataframe and filter dataframe on locations and min. available amounts
    df['Lokation_filter'] = df['Lokation'].map(dict_locations)
    df = df.loc[(df['Lokation_filter'] == 1) & (df['Beholdning'] >= min_quantity)]
    
    






get_all_available_quantities(get_ds_blend_request())


























