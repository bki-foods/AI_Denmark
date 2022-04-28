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

# Write into dbo.log
def log_insert(event: str, note: str):
    """Inserts a record into BKI_Datastore dbo.log with event and note."""
    dict_log = {'Note': note
                ,'Event': event}
    pd.DataFrame(data=dict_log, index=[0]).to_sql('Log', con=bsi.engine_ds, schema='dbo', if_exists='append', index=False)

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
def update_request_log(request_id: int, status: int, filename: str = '', filepath: str = ''):
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
    bsi.cursor_ds.execute(f"""UPDATE [cof].[Receptforslag_log]
                          SET [Status] = {status}, [Filsti] = '{filepath}'
                          , [Filnavn] = '{filename}'
                          WHERE [Id] = {request_id} """)
    bsi.cursor_ds.commit()

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
    df.to_sql('Email_log', con=bsi.engine_ds, schema='cof', if_exists='append', index=False)

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
            ,I.[Description] AS [Varenavn]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%FAIR%' THEN 1 ELSE 0 END AS [Fairtrade]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%ØKO%' THEN 1 ELSE 0 END AS [Økologi]
			,CASE WHEN UPPER(I.[Mærkningsordning]) LIKE '%RFA%' THEN 1 ELSE 0 END AS [Rainforest]
			,CASE WHEN UPPER(I.[Mærkningsordning]) = '' THEN 1 ELSE 0 END AS [Konventionel]
			,CASE WHEN UPPER(I.[Description]) LIKE '%ROBUSTA%' THEN 'R' ELSE 'A' END AS [Kaffetype]
            FROM [dbo].[BKI foods a_s$Purchase Header] AS PH
            INNER JOIN [dbo].[BKI foods a_s$Purchase Line] AS PL
            	ON PH.[No_] = PL.[Document No_]
            	AND [PL].[Line No_] = 10000
				AND PL.[Type] = 2
            LEFT JOIN [dbo].[BKI foods a_s$Item] AS I
            	ON PL.[No_] = I.[No_]
            LEFT JOIN [dbo].[BKI foods a_s$Country_Region] AS CR
            	ON PH.[Pay-to Country_Region Code] = CR.[Code]
            WHERE PH.[Kontrakt] = 1"""
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
    df['Kontraktnummer'] = df['Kontraktnummer'].str.upper() # Upper case to prevent join issues
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
    df['Kontraktnummer'] = df['Kontraktnummer'].str.upper() # Upper case to prevent join issues
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

def get_all_available_quantities(location_filter: dict, min_quantity: float, certifications: dict) -> pd.DataFrame():
    """
    Returns a dataframe with all available coffee contracts which adhere to criteria regarding
    locations, min. quantity as well as any certifications.
    A list of select item numbers which should never be included are removed. This list is maintained in this function.
    Parameters
    ----------
    location_filter : dict
        A dictionary with keys == SPOT,AARHUSHAVN,UDLAND,AFLOAT,SILOER,WAREHOUSE. 0/1 whether to include or not
    min_quantity : float
        The minimum quantity that must be available for a contract to be considered for use.
    certifications : dict
        A dctionary with keys == Fairtrade,Konventionel,Rainforest,Sammensætning,Økologi 0/1 whether to include or not
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
    df['Modtagelse'].fillna(value='', inplace=True)
    df['Kontraktnummer'] = df['Kontraktnummer'].str.upper() # Upper case to prevent join issues
    # Map dictionary to dataframe and filter dataframe on locations and min. available amounts
    df['Lokation_filter'] = df['Lokation'].map(location_filter)
    df = df.loc[(df['Lokation_filter'] == 1) & (df['Beholdning'] >= min_quantity)]

    # Read green coffee grades into dataframe and calculate mean values
    df_grades = get_gc_grades()
    df_grades['Modtagelse'].fillna(value='', inplace=True)
    # Calculate mean value grouped by kontrakt and modtagelse, merge with original dataframe
    df_grades_del = df_grades.groupby(['Kontraktnummer','Modtagelse'], dropna=False).agg(
        {'Syre': 'mean'
        ,'Krop': 'mean'
        ,'Aroma': 'mean'
        ,'Eftersmag': 'mean'
        ,'Robusta': 'mean'
        }).reset_index()
    df = pd.merge(
        left= df
        ,right= df_grades_del
        ,how= 'left'
        ,on= ['Kontraktnummer','Modtagelse']
        )
    # Calculate mean value grouped by kontrakt, merge with original dataframe
    df_grades_con = df_grades.groupby(['Kontraktnummer'], dropna=False).agg(
        {'Syre': 'mean'
        ,'Krop': 'mean'
        ,'Aroma': 'mean'
        ,'Eftersmag': 'mean'
        ,'Robusta': 'mean'
        }).reset_index()
    df = pd.merge(
        left= df
        ,right= df_grades_con
        ,how= 'left'
        ,on= 'Kontraktnummer'
        )
    # Get target values from Navision and add to dataframe
    df_grades_targets = get_target_cupping_profiles()
    df = pd.merge(
        left = df
        ,right = df_grades_targets
        ,how = 'left'
        ,on= 'Kontraktnummer')
    # Get available grades into a single column
    df['Syre'] = df['Syre_x'].combine_first(df['Syre_y']).combine_first(df['Syre'])
    df['Aroma'] = df['Aroma_x'].combine_first(df['Aroma_y']).combine_first(df['Aroma'])
    df['Krop'] = df['Krop_x'].combine_first(df['Krop_y']).combine_first(df['Krop'])
    df['Eftersmag'] = df['Eftersmag_x'].combine_first(df['Eftersmag_y']).combine_first(df['Eftersmag'])
    df['Robusta'] = df['Robusta_x'].combine_first(df['Robusta_y']).combine_first(df['Robusta'])
    # Add information regarding certifications of each contract
    df_contract_info = get_coffee_contracts()
    df = pd.merge(
        left = df
        ,right = df_contract_info
        ,how = 'left'
        ,on= 'Kontraktnummer')
    # Filter dataframe down to relevant rows for certifications. If include == False, only then filter
    if certifications['Fairtrade'] == 0:
        df = df.loc[(df['Fairtrade'] == 0)]
    if certifications['Økologi'] == 0:
        df = df.loc[(df['Økologi'] == 0)]
    if certifications['Rainforest'] == 0:
        df = df.loc[(df['Rainforest'] == 0)]
    if certifications['Konventionel'] == 0:
        df = df.loc[(df['Konventionel'] == 0)]
    # Remove or add Arabica/Robusta if chosen
    if certifications['Sammensætning'] == 'Ren Arabica':
        df = df.loc[(df['Kaffetype'] == 'A')]
    if certifications['Sammensætning'] == 'Ren Robusta':
        df = df.loc[(df['Kaffetype'] == 'R')]
    # Remove specific items that should never be included, defined by item numbers.
    customer_item_numbers = ['10104210','10104211','10104212','10104213'    # Sofiero
                             ,'10104310','10104311','10104312'              # Wilson
                             ,'10104240','10104241','10104242','10104243'   # SLOW
                             ,'10104244','10104245'
                             ,'10104110','10104111','10104112','10104113'   # Kontra
                             ,'10104116']
    df = df[~df['Sort'].isin(customer_item_numbers)]
    # Remove any unnecesary columns from dataframe | Sofiero, SLOW, Wilson
    df.drop(['Syre_x','Aroma_x','Krop_x','Eftersmag_x','Robusta_x'
             ,'Syre_y','Aroma_y','Krop_y','Eftersmag_y','Robusta_y'
             ,'Lokation_filter', 'Leverandør', 'Høst', 'Høstår', 'Metode'
             ,'Fairtrade', 'Økologi', 'Rainforest', 'Konventionel', 'Kaffetype']
            ,inplace=True, axis=1)
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
