#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import itertools
import pandas as pd
import bki_server_information as bsi
import ti_price_opt as tpo



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
        return ""
    else:
        return "'{}'".format("','".join(list_with_values))


# Check if script is supposed to exit. 0 value = exit
def get_exit_check(value: int):
    """Calls sys.exit() if input value == 0"""
    if value == 0:
        sys.exit()
    else:
        pass

# Write into dbo.log
def log_insert(event: str, note: str):
    """Inserts a record into BKI_Datastore dbo.log with event and note."""
    dict_log = {"Note": note
                ,"Event": event}
    pd.DataFrame(data=dict_log, index=[0]).to_sql("Log", con=bsi.con_ds, schema="dbo", if_exists="append", index=False)

# Write dataframe into Excel sheet
def insert_dataframe_into_excel (engine, dataframe, sheetname: str, include_index: bool = False):
    """
    Inserts a dataframe into an Excel sheet
    \n Parameters
    ----------
    engine : Excel engine
    dataframe : Pandas dataframe
        Dataframe containing data supposed to be inserted into the Excel workbook.
    sheetname : str (max length 31 characters)
        Name of sheet created where dataframe will be inserted into.
    include_index : bool
        True if index is supposed to be included in insert into Excel, False if not.
    """
    dataframe.to_excel(engine, sheet_name=sheetname, index=include_index)

# Update BKI_Datastore with input ID with a new status
def update_request_log(request_id: int, status: int, filename: str = "", filepath: str = ""):
    """
    Updates request log with input status, and possibly filname and -path.
    Parameters
    ----------
    request_id : int
        Request id that is to be updated.
    status : int
        Statuscode for the record
    filename : str, optional
        Name of the workbook generated. The default is ''.
    filepath : str, optional
        The filepath for the workbook generated. The default is ''."""
    bsi.con_ds.execute(f"""UPDATE [cof].[Receptforslag_log]
                          SET [Status] = {status}, [Filsti] = '{filepath}'
                          , [Filnavn] = '{filename}'
                          WHERE [Id] = {request_id} """)

# Write into section log
def insert_into_email_log(dictionary: dict):
    """
    Writes into BKI_Datastore cof.Receptforslag_log. \n
    Parameters
    ----------
    dictionary : dict
        Dictionary containing keys matching field names in table in the database.
    """
    df = pd.DataFrame(data= dictionary ,index= [0])
    df.to_sql("Email_log", con=bsi.con_ds, schema="cof", if_exists="append", index=False)

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

# Get a calculated price of a given input recipe
def get_recipe_calculated_costs(recipe:str) -> float:
    """
    Returns a dictionary with calculated prices for the input recipe.
    The prices for the recipe is calculated using the standard cost price and forecast prices for the green coffees in the recipe
    The green coffee prices that are used are the 1010 prices, to ensure a comparable price with recipe suggestions from NN.
    Dictionary keys: Price | Price +1M | Price +2M | Price +3M
    """
    query = f""" WITH BOM_VER AS (
                SELECT TOP 1 PBV.[Production BOM No_] ,[Version Code]
                FROM [dbo].[BKI foods a_s$Production BOM Version] AS PBV
                INNER JOIN [dbo].[BKI foods a_s$Item] AS I
                	ON PBV.[Production BOM No_] = I.[Production BOM No_]
                WHERE PBV.[Status] = 1 AND I.[No_] = '{recipe}'
                ORDER BY PBV.[Starting Date] DESC )
                SELECT
                	ISNULL(SUM(PBL.[Quantity] * I.[Standard Cost]),0) AS [Price]
					,ISNULL(SUM(PBL.[Quantity] * FUC.[Forecast Unit Cost +1M]),0) AS [Price +1M]
					,ISNULL(SUM(PBL.[Quantity] * FUC.[Forecast Unit Cost +2M]),0) AS [Price +2M]
					,ISNULL(SUM(PBL.[Quantity] * FUC.[Forecast Unit Cost +3M]),0) AS [Price +3M]
                FROM [dbo].[BKI foods a_s$Production BOM Line] AS PBL
                INNER JOIN BOM_VER
                	ON PBL.[Production BOM No_] = BOM_VER.[Production BOM No_]
                	AND PBL.[Version Code] = BOM_VER.[Version Code]
                INNER JOIN [dbo].[BKI foods a_s$Item] AS I
                	ON PBL.[No_] = I.[No_]
				LEFT JOIN [dbo].[BKI foods a_s$Forecast Item Unit Cost] AS FUC
					ON PBL.[No_] = FUC.[Item No_]
                WHERE I.[Item Category Code] = 'RÅKAFFE' """
    df = pd.read_sql(query, bsi.con_nav)
    
    prices = {
        "Price": float(df["Price"].iloc[0])
        ,"Price +1M": float(df["Price +1M"].iloc[0])
        ,"Price +2M": float(df["Price +2M"].iloc[0])
        ,"Price +3M": float(df["Price +3M"].iloc[0])}
    
    return prices 

# Get information from coffee contracts from Navision
def get_coffee_contracts() -> pd.DataFrame():
    """
    Returns information from Navision for coffee contracts as a Pandas DataFrame.
    """
    query = """ SELECT PH.[No_] AS [Kontraktnummer]
        	,CASE WHEN PH.[Washed Coffee] = 1 THEN 'Vasket'
                WHEN PH.[Washed Coffee] = 0 AND PH.[No_] >= '21-037' THEN 'Ej vasket'
        		ELSE NULL END AS [Metode]
        	,I.[No_] AS [Sort] ,I.[Mærkningsordning] ,PH.[Differentials] AS [Differentiale]
            ,I.[Description] AS [Varenavn], I.[Unit Cost] AS [Kostpris], I.[Standard Cost]
			,FUC.[Forecast Unit Cost +1M], FUC.[Forecast Unit Cost +2M], FUC.[Forecast Unit Cost +3M]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%FAIR%' THEN 1 ELSE 0 END AS [Fairtrade]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%ØKO%' THEN 1 ELSE 0 END AS [Økologi]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%RFA%' THEN 1
            WHEN UPPER(I.[Mærkningsordning]) LIKE '%UTZ%' THEN 1 ELSE 0 END AS [Rainforest]
			,CASE WHEN UPPER(I.[Mærkningsordning]) = '' THEN 1 ELSE 0 END AS [Konventionel]
			,CASE WHEN UPPER(I.[Description]) LIKE '%ROBUSTA%' THEN 'R' ELSE 'A' END AS [Kaffetype]
			--,PRI.[DENSITY] AS [Volume sætpunkt],PRI.[HUMIDITY] AS [Vandprocent sætpunkt]
            FROM [dbo].[BKI foods a_s$Purchase Header] AS PH
            INNER JOIN [dbo].[BKI foods a_s$Purchase Line] AS PL
            	ON PH.[No_] = PL.[Document No_]
            	AND [PL].[Line No_] = 10000
				AND PL.[Type] = 2
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON '1020' + RIGHT(PL.[No_],4) = I.[No_]
			--INNER JOIN [dbo].[BKI foods a_s$PROBAT Item] AS PRI
				--ON I.[No_] = PRI.[CUSTOMER_CODE]
			LEFT JOIN [dbo].[BKI foods a_s$Forecast Item Unit Cost] AS FUC
				ON I.[No_] = FUC.[Item No_]
            WHERE PH.[Kontrakt] = 1
				AND I.[No_] NOT LIKE '1012%'
				AND I.[Sub Product Group Code] NOT IN ('111','112')
				AND I.[Withdrawal Status] <> 2 """
    df = pd.read_sql(query, bsi.con_nav)
    
    # Ensure forecast unit costs have a value, just punish the blend enough that it's obvious that there is an issue with prices
    df[["Forecast Unit Cost +1M","Forecast Unit Cost +2M","Forecast Unit Cost +3M"]].fillna(999, inplace=True)
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
    df["Kontraktnummer"] = df["Kontraktnummer"].str.upper() # Upper case to prevent join issues
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
                AND S.[Varenummer] NOT LIKE '1090%'
                AND S.[Smagningstype] = 4
                AND S.[Id_org_kildenummer] <> 10 """
    df = pd.read_sql(query, bsi.con_ds)
    return df

# Get all related orders from Navision for orders which have been given a grade
def get_nav_order_related() -> pd.DataFrame():
    """
    Returns a set of orders and the directly related orders from Navision returned as a pandas DataFrame.
    """
    # Get dataframe with orders given grades, convert til liste and string used for SQL query.
    df_orders = get_finished_goods_grades()
    graded_orders_list = df_orders["Ordrenummer"].unique().tolist()
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
                                                  ,"Ordrenummer"
                                                  ,get_nav_order_related()
                                                  ,"Ordre")
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
                                ,left_on="Relateret ordre"
                                ,right_on="ORDER_NAME"
                                ,how="left")
    # Prepare final dataframe
    df_orders_final = pd.DataFrame()
    df_orders_final[["Ordre","Relateret ordre"]] = df_with_roasting_orders[["Ordre","S_ORDER_NAME"]]
    df_orders_final.dropna(inplace=True)

    return df_orders_final


# Get input coffees used for roasting orders identified
def get_roaster_input() -> pd.DataFrame():
    """
    Returns the input of green coffee used for roasting orders identified as used in a finished product.
    """
    # Get dataframe, list and concatenated string for sql with relevant order numbers
    df_orders = get_order_relationships()
    orders_list = df_orders["Relateret ordre"].unique().tolist()
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
    df["Kontraktnummer"] = df["Kontraktnummer"].str.upper() # Upper case to prevent join issues
    return df


# Get input coffees used for roasting orders identified
def get_roaster_output() -> pd.DataFrame():
    """
    Returns the output of roasting orders identified as used in a finished product.
    """
    # Get dataframe, list and concatenated string for sql with relevant order numbers
    df_orders = get_order_relationships()
    orders_list = df_orders["Relateret ordre"].unique().tolist()
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
    query = "SELECT TOP 1 * FROM [cof].[Receptforslag_log] WHERE [Status] = 0"
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
            AND [Varenummer] NOT IN ('10204401','10204403','10204440','10204450','10204970','10204460','10209999')
            GROUP BY [Kontrakt],[Modtagelse] """
    df = pd.read_sql(query, bsi.con_probat)
    return df

def get_warehouse_available_quantities() -> pd.DataFrame():
    """Returns a dataframe with all available coffee from Warehouse from Probat."""
    query = """ SELECT  'WAREHOUSE' AS [Lokation] ,[Kontrakt] AS [Kontraktnummer]
            ,[Modtagelse] ,SUM([Kilo]) AS [Beholdning]
            FROM [dbo].[Newest total inventory]
            WHERE [Placering] = 'Warehouse'
            AND [Varenummer] NOT IN ('10204401','10204403','10204440','10204450','10204970','10204460','10209999')
            GROUP BY [Kontrakt],[Modtagelse] """
    df = pd.read_sql(query, bsi.con_probat)
    return df

def get_target_cupping_profiles() -> pd.DataFrame():
    """Returns a dataframe containing all target cupping profiles from Navision.
       Table id 27 = Item, 39 = purchase header."""
    query = """ WITH CP AS (
             SELECT [Table ID],[No_] ,[0] AS [Syre],[1] AS [Aroma]
             	,[2] AS [Krop],[3] AS [Eftersmag],[4] AS [Robusta]
             FROM (
                 SELECT [Table ID] ,[No_] ,[Type] ,[Value]
             FROM [dbo].[BKI foods a_s$Coffee Taste Profile]) AS TBL
             PIVOT (  
                 MAX([Value])  
                 FOR [Type] IN ([0],[1],[2],[3],[4])  
             ) AS PVT
            )
            SELECT [No_] AS [Kontraktnummer] ,[Syre] ,[Aroma] ,[Krop] ,[Eftersmag] ,[Robusta]
            FROM CP WHERE [Table ID] = 39
            UNION
            SELECT PL.[Document No_] ,CP.[Syre] ,CP.[Aroma] ,CP.[Krop] ,CP.[Eftersmag] ,CP.[Robusta]
            FROM [dbo].[BKI foods a_s$Purchase Line] AS PL
            INNER JOIN [dbo].[BKI foods a_s$Purchase Header] AS PH
            	ON PL.[Document No_] = PH.[No_]
            INNER JOIN CP
            	ON PL.[No_] = CP.[No_]
            	AND CP.[Table ID] = 27
            WHERE PH.[Kontrakt] = 1 AND PL.[Type] = 2 """
    df = pd.read_sql(query, bsi.con_nav)
    return df

def get_all_available_quantities(location_filter: dict, min_quantity: float, certifications: dict
                                 ,aggregate: bool) -> pd.DataFrame():
    """
    Returns a dataframe with all available coffee contracts which adhere to criteria regarding
    locations, min. quantity as well as any certifications.
    A list of select item numbers which should never be included are removed. This list is maintained in this function.
    Parameters
    ----------
    location_filter : dict
        A dictionary with keys == SPOT,AARHUSHAVN,UDLAND,AFLOAT,SILOER,WAREHOUSE. 0/1 whether to include or not.
        This criteria is used for filtering before any aggregation is done to the data.
    min_quantity : float
        The minimum quantity that must be available for a contract to be considered for use.
        This criteria is used for filtering before any aggregation is done to the data.
    certifications : dict
        A dctionary with keys == Fairtrade,Konventionel,Rainforest,Sammensætning,Økologi 0/1 whether to include or not
    aggregate : bool
        Boolean indicating whether or not to aggregate data before it is returned.
        If aggregated, several columns that are contract specific will be changed to 'n/a'.
        If True, all flavor profiles are weighted against the available quantity.
    Returns
    -------
    df : pd.DataFrame()
        A dataframe with all available coffee contracts.
        Cupping profiles are found in the following order:
        Mean grades per kontrakt/modtagelse --> Mean grades per Kontrakt --> Target values from Navision.
    """
    # Create dataframe with all available coffees
    df = pd.concat([
        get_spot_available_quantities()
        ,get_havn_available_quantities()
        ,get_udland_available_quantities()
        ,get_afloat_available_quantities()
        ,get_silos_available_quantities()
        ,get_warehouse_available_quantities()
        ])
    df["Modtagelse"].fillna(value="", inplace=True)
    df["Kontraktnummer"] = df["Kontraktnummer"].str.upper() # Upper case to prevent join issues
    # Map dictionary to dataframe and filter dataframe on locations and min. available amounts
    df["Lokation_filter"] = df["Lokation"].map(location_filter)
    df = df.loc[(df["Lokation_filter"] == 1) & (df["Beholdning"] >= min_quantity)]

    # Read green coffee grades into dataframe and calculate mean values
    df_grades = get_gc_grades()
    df_grades["Modtagelse"].fillna(value="", inplace=True)
    # Calculate mean value grouped by kontrakt and modtagelse, merge with original dataframe
    df_grades_del = df_grades.groupby(["Kontraktnummer","Modtagelse"], dropna=False).agg(
        {"Syre": "mean"
        ,"Krop": "mean"
        ,"Aroma": "mean"
        ,"Eftersmag": "mean"
        ,"Robusta": "mean"
        }).reset_index()
    df = pd.merge(
        left= df
        ,right= df_grades_del
        ,how= "left"
        ,on= ["Kontraktnummer","Modtagelse"]
        )
    # Calculate mean value grouped by kontrakt, merge with original dataframe
    df_grades_con = df_grades.groupby(["Kontraktnummer"], dropna=False).agg(
        {"Syre": "mean"
        ,"Krop": "mean"
        ,"Aroma": "mean"
        ,"Eftersmag": "mean"
        ,"Robusta": "mean"
        }).reset_index()
    df = pd.merge(
        left= df
        ,right= df_grades_con
        ,how= "left"
        ,on= "Kontraktnummer"
        )
    # Get target values from Navision and add to dataframe
    df_grades_targets = get_target_cupping_profiles()
    df = pd.merge(
        left = df
        ,right = df_grades_targets
        ,how = 'left'
        ,on= 'Kontraktnummer')
    # Get available grades into a single column
    df["Syre"] = df["Syre_x"].combine_first(df["Syre_y"]).combine_first(df["Syre"])
    df["Aroma"] = df["Aroma_x"].combine_first(df["Aroma_y"]).combine_first(df["Aroma"])
    df["Krop"] = df["Krop_x"].combine_first(df["Krop_y"]).combine_first(df["Krop"])
    df["Eftersmag"] = df["Eftersmag_x"].combine_first(df["Eftersmag_y"]).combine_first(df["Eftersmag"])
    df["Robusta"] = df["Robusta_x"].combine_first(df["Robusta_y"]).combine_first(df["Robusta"])
    # Remove rows with na, we need values for all parameters. Reset index afterwards
    df.dropna(subset=["Syre","Aroma","Krop","Eftersmag"],inplace=True)
    df["Robusta"].fillna(10, inplace=True)
    df.reset_index(drop=True, inplace=True)
    # Add information regarding certifications of each contract
    df_contract_info = get_coffee_contracts()
    df = pd.merge(
        left = df
        ,right = df_contract_info
        ,how = "left"
        ,on= "Kontraktnummer")
    # Filter dataframe down to relevant rows for certifications. If include == False, only then filter
    if certifications["Fairtrade"] == 0:
        df = df.loc[(df["Fairtrade"] == 0)]
    if certifications["Økologi"] == 0:
        df = df.loc[(df["Økologi"] == 0)]
    if certifications["Rainforest"] == 0:
        df = df.loc[(df["Rainforest"] == 0)]
    if certifications["Konventionel"] == 0:
        df = df.loc[(df["Konventionel"] == 0)]
    # Remove or add Arabica/Robusta if chosen
    if certifications["Sammensætning"] == "Ren Arabica":
        df = df.loc[(df["Kaffetype"] == "A")]
    if certifications["Sammensætning"] == "Ren Robusta":
        df = df.loc[(df["Kaffetype"] == "R")]
    # Remove specific items that should never be included, defined by item numbers.
    customer_item_numbers = ["10104210","10104211","10104212","10104213"    # Sofiero
                             ,"10104310","10104311","10104312"              # Wilson
                             ,"10104240","10104241","10104242","10104243"   # SLOW
                             ,"10104244","10104245"
                             ,"10104110","10104111","10104112","10104113"   # Kontra
                             ,"10104116"]
    df = df[~df["Sort"].isin(customer_item_numbers)]
    # Remove any unnecesary columns from dataframe | Sofiero, SLOW, Wilson
    df.drop(["Syre_x","Aroma_x","Krop_x","Eftersmag_x","Robusta_x"
             ,"Syre_y","Aroma_y","Krop_y","Eftersmag_y","Robusta_y"
             ,"Lokation_filter","Metode"
             ,"Fairtrade","Økologi","Rainforest","Konventionel","Kaffetype"]
            ,inplace=True, axis=1)
    # If the available amounts are requested as aggregated values, do this
    if aggregate:
        df[["Syre","Aroma","Krop","Eftersmag","Robusta"]] = df[["Syre","Aroma","Krop","Eftersmag","Robusta"]].multiply(df["Beholdning"], axis="index")
        # Change contract specific column values to n/a to allow for a group by
        df[["Kontraktnummer","Modtagelse","Lokation","Differentiale","Screensize","Oprindelsesland"]] = "n/a"
        # Calculate the flavor profiles as a weighted value
        df = df.groupby(["Kontraktnummer","Modtagelse","Lokation","Differentiale","Kostpris","Standard Cost"
                         ,"Forecast Unit Cost +1M","Forecast Unit Cost +2M","Forecast Unit Cost +3M","Sort","Varenavn"
                         ,"Screensize","Oprindelsesland","Mærkningsordning"], dropna=False).agg(
                             {"Beholdning": "sum"
                              ,"Syre": "sum"
                              ,"Aroma": "sum"
                              ,"Krop": "sum"
                              ,"Eftersmag": "sum"
                              ,"Robusta": "sum"}).reset_index()
        df[["Syre","Aroma","Krop","Eftersmag","Robusta"]] = df[["Syre","Aroma","Krop","Eftersmag","Robusta"]].divide(df["Beholdning"], axis="index")
    
    return df

# Get identical recipes
def get_identical_recipes(syre: int, aroma: int, krop: int, eftersmag: int) -> pd.DataFrame():
    """Returns a pandas dataframe with identical recipes when compared to input parameters.
    Also returns similar recipes where ABS(diff) for each parameter is allowed to be 1."""
    query = f"""WITH CP AS (
            SELECT [Table ID] ,[No_] ,[0] AS [Syre] ,[1] AS [Aroma]
            	,[2] AS [Krop] ,[3] AS [Eftersmag],[4] AS [Robusta]
            FROM (
                SELECT [Table ID] ,[No_] ,[Type] ,[Value]
            FROM [dbo].[BKI foods a_s$Coffee Taste Profile]) AS TBL
            PIVOT (  
                MAX([Value])  
                FOR [Type] IN ([0],[1],[2],[3],[4])  
            ) AS PVT
            WHERE [Table ID] = 27
            )
			,BOM_VERS AS (
			SELECT
				[Production BOM No_]
				,MAX([Version Code]) AS [Version]
			FROM [dbo].[BKI foods a_s$Production BOM Version]
			WHERE [Status] = 1
				AND [Starting Date] < GETDATE()
			GROUP BY [Production BOM No_]
			)
			,TILLÆG AS (
			SELECT 
				PBL.[Production BOM No_]
				,PBL.[Version Code]
				,SUM(PBL.[Quantity per] * (1 + PBL.[Scrap _] / 100.0) * I.[Unit Cost]) AS [Cost of not coffee]
			FROM [dbo].[BKI foods a_s$Production BOM Line] AS PBL
			INNER JOIN [dbo].[BKI foods a_s$Item] AS I
				ON PBL.[No_] = I.[No_]
			INNER JOIN BOM_VERS
				ON PBL.[Production BOM No_] = BOM_VERS.[Production BOM No_]
				AND PBL.[Version Code] = BOM_VERS.[Version]
			WHERE I.[Item Category Code] <> 'RÅKAFFE'
			GROUP BY
				PBL.[Production BOM No_]
				,PBL.[Version Code]
			)

            SELECT I.[No_] AS [Receptnummer] ,I.[Description] AS [Beskrivelse]
            	,I.[Mærkningsordning] ,I.[Standard Cost] AS [Kostpris]
				,I.[Standard Cost] - T.[Cost of not coffee] AS [Kost uden tillæg, gas mm.]
            	,PRI.[COLOR] AS [Farve] ,CP.[Syre] ,CP.[Aroma] ,CP.[Krop]
            	,CP.[Eftersmag] ,CP.[Robusta] ,'Identisk' AS [Sammenligning]
            FROM CP
            INNER JOIN [dbo].[BKI foods a_s$PROBAT Item] AS PRI
            	ON CP.[No_] = PRI.[CUSTOMER_CODE]
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON CP.[No_] = I.[No_]
			LEFT JOIN TILLÆG AS T
				ON I.[Production BOM No_] = T.[Production BOM No_]
            WHERE PRI.[ZONE] = 2 AND CP.[Aroma] = {aroma} AND CP.[Syre] = {syre}
            	AND CP.[Eftersmag] = {eftersmag} AND CP.[Krop] = {krop}
            UNION ALL
            SELECT I.[No_] AS [Receptnummer] ,I.[Description] AS [Beskrivelse]
            	,I.[Mærkningsordning] ,I.[Standard Cost] AS [Kostpris]
				,I.[Standard Cost] - T.[Cost of not coffee] AS [Kost uden tillæg, gas mm.]
            	,PRI.[COLOR] AS [Farve] ,CP.[Syre] ,CP.[Aroma] ,CP.[Krop]
            	,CP.[Eftersmag] ,CP.[Robusta],'Lignende'
            FROM CP
            INNER JOIN [dbo].[BKI foods a_s$PROBAT Item] AS PRI
            	ON CP.[No_] = PRI.[CUSTOMER_CODE]
            INNER JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON CP.[No_] = I.[No_]
			LEFT JOIN TILLÆG AS T
				ON I.[Production BOM No_] = T.[Production BOM No_]
            WHERE PRI.[ZONE] = 2
            	AND ABS(CP.[Aroma] - {aroma} ) <= 1
            	AND ABS(CP.[Syre] - {syre} ) <= 1
            	AND ABS(CP.[Eftersmag] - {eftersmag} ) <= 1
            	AND ABS(CP.[Krop] - {krop} ) <= 1
            	AND ( ABS(CP.[Aroma] - {aroma} ) + ABS(CP.[Syre] - {syre} ) + 
                      ABS(CP.[Eftersmag] - {eftersmag} ) + ABS(CP.[Krop] - {krop} ) ) > 0"""
    df = pd.read_sql(query, bsi.con_nav)
    return df

def get_blends_with_proportions(required_item:int, min_proportion:int, available_items:list, number_of_components:int) -> list:
    """
    Creates all possible combinations of available components and the required item with their respective proportions.
    Proportions are created in increments of 5, and the input min_proportion will be rounded to nearest multiple of 5.
    The following cases will yield and empty list due to lack of data or to prevent excessive amounts of data.
    - If more components are requested than coffee is avalable
    - If >6 components and >8 available items
    - If >5 components and >10 available items
    - If >4 components and >15 available items
    Parameters
    ----------
    required_item : int
        The item which is required to be part of all the created blends.
    min_proportion : int
        The min proportion which the required item must have.
        The required item will be in blends with proportions between this value are the theoretical max value.
        If this value is not input as an increment of 5, it will be rounded
    available_items : list
        A list of all the possible components to be included in the blends.
        The required item must be part of this list as well.
    number_of_components : int
        The number of components which the blend must have.
        Must be a value between 2 and 7.

    Returns
    -------
    A list of all possible blends that can be created with the input items and their respective proportions
    """
    
    if min_proportion < 5:
        min_proportion = 5
    elif min_proportion > 95:
        min_proportion = 95
    elif min_proportion % 5:
        min_proportion = round(min_proportion / 5 ,0) * 5

    
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
    Create a list of blends that have no differences to the target flavor profile greater than the cuf_off_value
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
                                     ,target_color:int, cut_off_value:float = 0.5) ->list:
    """
    Creates a list of all possible blends which fall within the input criteria.
    The list consists of blends of 2-7 components, unless no suitable candidates are found within these constraints.
    Parameters
    ----------
    required_item : int
        The component which must be present in all proposed blends.
    min_proportion : int
        The min proportion the required component must have in all proposed blends.
        Blends will be created with this proportion up to, and including, the theoretical max proportion
    available_items : list
        A list of all available components for the blends. List must include the required item as well.
    prices : TYPE
        A list of the prices of all available items, including required item.
    flavor_model : TYPE
        A trained neural network that can be used to predict the flavor profile of each blend.
    flavors_components : TYPE
        The known flavor profiles of all the available items.
    target_flavor : list
        The flavor profile which is required to be achived.
    target_color : int
        The degree of roast for the blend.
    cut_off_value : float, optional
        The max value any difference for each of the flavor profile values may have.
        If any of the values are greater than this value the blend will be discarded.
        The default is 0.75.

    Returns
    -------
    A list of all the blends that fall within the input criteria.

    """

    best_fitting_blends = []
    best_fitting_fitness = []
    
    # Use the number of components as iterator    
    for i in [2,3,4,5,6,7]:
        all_blends_incl_proportions = get_blends_with_proportions(
            required_item
            ,min_proportion
            ,available_items
            ,i)
        
        print("Components: " + str(i) + "\n" "Possible blends: " + str(len(all_blends_incl_proportions)))

        # Grab Currrent Time Before Running the Code for logging of total execution time
        start_time = time.time()        
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


    return best_fitting_blends,best_fitting_fitness


def get_blends_hof(blends:list, blends_eval_value:list, hof_size:int = 50) -> list:
    """
    Create a hall-of-fame of a list of blends that are not-too-similar.
    The hall-of-fame has the following logic flow, run per blend.
    - Is hof empty 
        yes --> add blend to hof
        no  --> is blend similar to another blend
            yes --> is blend fitness > similar blends fitness
                yes --> replace similar blend in hof
                no  --> pass
            no  --> is blends in hof < hof_size
                yes --> add blend to hof
                no  --> is blend fitness > min fitness in hof
                    yes --> replace blend in hof with min fitness
                    no  --> pass
 
    Parameters
    ----------
    blends : list
        A list with any number of blends of len 7, which contains tuples of components and proportions.
        Expected format: [[(),(),()],[(),(),()],[(),(),()]]
    blends_eval_value : list
        A list containing a value per blend, which is used to see which blend is to be prioritized over another.
        List must have the same length as the number of blends.
        The higher value the better
    hof_size : int, optional
        Setting of how many blends is to be returned in the final list.
        The default is 50.

    Returns
    -------
    A list with hof_size length of blends, which are the final result of the hof.
    """

    # Create a list of blend indexes to iterate over
    blend_numbers = list(range(len(blends_eval_value)))
    # Return none if no blends exist
    if not blend_numbers:
        return None
    
    best_fitting_hof = []
    while blend_numbers:
        # Add blend no to variable and remove from list, looking to exhaust list
        blend_no = blend_numbers[0]
        del blend_numbers[0]
        
        # If hof is empty, add the first blend to hof by default
        if not best_fitting_hof:
            best_fitting_hof.append(blend_no)
        # Check if any of the blends in the hof are too similar to the current blend
        blend_similar_to_hof = [tpo.blends_too_similar(blends[blend_no], blends[hof_blend]) for hof_blend in best_fitting_hof]
        # Get all fitness values of hof
        hof_fitness_total = [blends_eval_value[blend] for blend in best_fitting_hof]
        if not any(blend_similar_to_hof):
            # If hof has not reached max size yet, add the blend
            if len(best_fitting_hof) < hof_size:
                best_fitting_hof.append(blend_no)
            # If hof has reached max size, evaluate fitness value of current blend and 
            else:
                min_fitness_hof = min(hof_fitness_total)
                # If fitness of current blend is higher than the lowest in hof, replace
                if blends_eval_value[blend_no] > min_fitness_hof:
                    # Get the index of the worst fitness value
                    ix_worst_fitness = hof_fitness_total.index(min_fitness_hof)
                    # Replace worst fitness with current blend
                    best_fitting_hof[ix_worst_fitness] = blend_no
        # If current blend is similar to one or more in hof, we need to compare fitness values of these and replace the lowest one if current blend is better
        else:
            # Find worst fitness of the similar blends
            min_fitness_hof_similar = min([hof_fitness_total[i] if blend_similar_to_hof[i] else 1.0 for i in range(len(best_fitting_hof))])
            # If current blend is a better fit, replace the worse
            if blends_eval_value[blend_no] > min_fitness_hof_similar:
                # Get the index of the worst fitness value
                ix_worst_fitness_similar = hof_fitness_total.index(min_fitness_hof_similar)
                # Replace worst fitness with current blend
                best_fitting_hof[ix_worst_fitness_similar] = blend_no
        
    hof_blends = [blends[i] for i in best_fitting_hof]

    return hof_blends



def convert_blends_lists_to_dataframe(blends:list, blend_no_start:int=0)-> pd.DataFrame():
    """
    Converts a list of blends with components and proportions to a pandas DataFrame.

    Parameters
    ----------
    blends :
        A list containing all the blends to be evaluated containing index no of component and its proportion.
        Use -1 as placeholder for NULL components with a proportion of 0.
        Expected format: [[(),(),()],[(),(),()],[(),(),()]]
    blend_no_start :
        The index at which the blends are to be numbered.
        Default index is 0, which would mean that the blends will be numbered 1,2,3 etc.

    Returns
    -------
    A pandas DataFrame with all blends

    """
        
    df = pd.DataFrame(columns=["Blend_nr","Kontraktnummer_index","Proportion"])

    for blend in blends:
        blend_no_start +=1
        for component_line in blend:
            if not component_line[0] == -1: # -1 indicates a NULL placeholder value, these are ignored
            # Extract data for each component line for each blend suggestion and append to dataframe
                data = pd.DataFrame.from_dict(
                    {"Blend_nr": [blend_no_start]
                    ,"Kontraktnummer_index": [component_line[0]]
                    ,"Proportion": [component_line[1]]})
                df = pd.concat([df,data], ignore_index=True) # df.append(data, ignore_index = True)

    return df


def get_test_roastings(robusta:bool, start_tasting_id:int=0) -> pd.DataFrame():
    """
    Returns a pandas dataframe containing all test roastings which have been graded.
    The data is returned with the same columns as are used in ti_data_preprocessing, assuming no changes
    in the naming conventions.
    
    If robusta parameter is True, the returned data will contain the robusta parameter for green coffee and 
    final product. Both of these containing values with potential fillna(10).
    
    start_tasting_id indicates which number the tasting id sequence for data should start.
    Defaults to 0
    """

    query = """ SELECT
            	CAST(LEFT(BFK.[Registreringstidspunkt],11) AS DATETIME) AS [Dato_r]
            	,RRP.[Kontraktnummer]
            	,RRP.[Delivery] AS [Modtagelse]
            	,BFK.[Varenummer] AS [Sort]
            	,CAST(LEFT(BFH.[Registreringstidspunkt],11) AS DATETIME) AS [Dato_rist]
            	,6000000 + S.[Id_org] AS [Produktionsordre id]
            	,7000000 + S.[Id_org] AS [Batch id]
            	,COALESCE(BFK.[Vægt],BFK.[Proportion]) AS [Kilo_rist_input]
            	,8000000 + S.[Id_org] AS [Ordre_rist]
            	,BFH.[Reference_receptnummer] AS [Receptnummer]
            	,SUM(COALESCE(BFK.[Vægt],BFK.[Proportion])) OVER (PARTITION BY S.[Id]) AS [Kilo_rist_output]
            	,BFH.[Farvemåling] AS [Farve]
            	,S.[Dato] AS [Dato_p]
                ,9000000 + S.[Id_org] AS [Ordre_p]
                ,S.[Smag_Syre] AS [Syre_p]
                ,S.[Smag_Krop] AS [Krop_p]
                ,S.[Smag_Aroma] AS [Aroma_p]
                ,S.[Smag_Eftersmag] AS [Eftersmag_p]
                ,S.[Smag_Robusta] AS [Robusta_p]
            	,NULL AS [Smagningsid]
            	,1 AS [Faktorfelt]
            	,ROW_NUMBER() OVER (PARTITION BY BFK.[Id],S.[Id_org] ORDER BY BFK.[Id]) AS [Komponent id]
            FROM [cof].[Smageskema] AS S
            INNER JOIN [cof].[Blend_forsøg_hoved] AS BFH
            	ON S.[Id_org] = BFH.[Id]
            INNER JOIN [cof].[Blend_forsøg_komponenter] AS BFK
            	ON BFH.[Blend_id] = BFK.[Blend_id]
            INNER JOIN [cof].[Risteri_råkaffe_planlægning] AS RRP
            	ON BFK.[Modtagelses_id] = RRP.[Id]
            WHERE S.[Id_org_kildenummer] = 10
            	AND S.[Smag_Syre] + S.[Smag_Krop] + S.[Smag_Aroma] + S.[Smag_Eftersmag] IS NOT NULL """
    
    # Get data for finished products and grades for green coffees
    df = pd.read_sql(query, bsi.con_ds)
    tasting_ids = [i + start_tasting_id + 100000 for i in list(range(len(df)))]
    df["Smagningsid"] = tasting_ids
    
    df_grades = get_gc_grades()[["Kontraktnummer","Modtagelse","Syre","Krop","Aroma","Eftersmag","Robusta"]].rename(
        columns={
        "Syre": "Syre_r"
        ,"Krop": "Krop_r"
        ,"Aroma": "Aroma_r"
        ,"Eftersmag": "Eftersmag_r"
        ,"Robusta": "Robusta_r"})
    #Remove robusta columns to fit existing datamodel for 'true' data
    if not robusta:
        df_grades.drop(columns = ["Robusta_r"],inplace = True)
        df.drop(columns = ["Robusta_p"], inplace = True)
    else:
        df_grades["Robusta_r"].fillna(10,inplace = True)
        df["Robusta_p"].fillna(10,inplace = True)
        
    df = pd.merge(
        left = df
        ,right = df_grades
        ,how = "inner"
        ,on = ["Kontraktnummer", "Modtagelse"])
    
    return df

