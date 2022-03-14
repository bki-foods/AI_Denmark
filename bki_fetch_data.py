#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import pyodbc


# =============================================================================
# Variables for query connections
# =============================================================================
server_04 = 'sqlsrv04'
db_ds = 'BKI_Datastore'
con_ds = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server_04};DATABASE={db_ds};autocommit=True')
params_ds = urllib.parse.quote_plus(f'DRIVER=SQL Server Native Client 11.0;SERVER={server_04};DATABASE={db_ds};Trusted_Connection=yes')
engine_ds = create_engine(f'mssql+pyodbc:///?odbc_connect={params_ds}')
cursor_ds = con_ds.cursor()

server_nav = r'SQLSRV03\NAVISION'
db_nav = 'NAV100-DRIFT'
con_nav = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server_nav};DATABASE={db_nav};Trusted_Connection=yes')
params_nav = urllib.parse.quote_plus(f'DRIVER=SQL Server Native Client 11.0;SERVER={server_nav};DATABASE={db_nav};Trusted_Connection=yes')
engine_nav = create_engine(f'mssql+pyodbc:///?odbc_connect={params_nav}')

server_probat = '192.168.125.161'
db_probat = 'BKI_IMP_EXP'
con_probat = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server_probat};DATABASE={db_probat};uid=bki_read;pwd=Probat2016')
params_probat = urllib.parse.quote_plus(f'DRIVER=SQL Server Native Client 11.0;SERVER={server_probat};DATABASE={db_probat};Trusted_Connection=yes')
engine_probat = create_engine(f'mssql+pyodbc:///?odbc_connect={params_probat}')


    
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

# Get info from assembly and production orders in Navision
query_order_info = """ SELECT PAH.[No_] AS [Ordrenummer],PAH.[Item No_] AS [Varenummer]
                        FROM [dbo].[BKI foods a_s$Posted Assembly Header] AS PAH
                        INNER JOIN [dbo].[BKI foods a_s$Item] AS I
                            ON PAH.[Item No_] = I.[No_]
                        WHERE I.[Item Category Code] = 'FÆR KAFFE'
                            AND I.[Display Item] = 1
                        UNION ALL
                        SELECT PO.[No_],PO.[Source No_]
                        FROM [dbo].[BKI foods a_s$Production Order] AS PO
                        INNER JOIN [dbo].[BKI foods a_s$Item] AS I
                            ON PO.[Source No_] = I.[No_]
                        WHERE PO.[Status] IN (2,3,4) AND I.[Item Category Code] <> 'RÅKAFFE' """
df_order_info = pd.read_sql(query_order_info, con_nav)
def get_nav_order_info(order_no: str) -> str:
    """
    Input order number and get the item number returned based on production and assembly orders in Navision.
    Query is executed upon import of script, and not each time this function is called.
    """
    df_temp = df_order_info[df_order_info['Ordrenummer'] == order_no]
    if len(df_temp) > 0:
        return df_temp['Varenummer'].iloc[0]


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
    df = pd.read_sql(query, con_nav)
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
    df = pd.read_sql(query, con_nav)
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
    df = pd.read_sql(query, con_ds)
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
    df = pd.read_sql(query, con_ds)
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
    df_nav_order_related = pd.read_sql(query_nav_order_related, con_nav)  
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
    df = pd.read_sql(query, con_probat)
    return df








# =============================================================================
# 
# df_temp = pd.concat([get_nav_order_related(), get_probat_orders_related()])
# temp_list = get_list_of_missing_values(get_finished_goods_grades()
#                                         ,'Ordrenummer'
#                                         ,df_temp
#                                         ,'Ordre')
# print(temp_list)
# 
# =============================================================================




# Get roasting orders from grinding orders from Probat
def get_order_relationships_final() -> pd.DataFrame():
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
    df_orders = pd.read_sql(query, con_probat)
    # Get a dataframe with Probat and Navision relationships unioned.
    df_orders_total = pd.concat([get_nav_order_related(), get_probat_orders_related()])
    # Left join roasting orders on df_orders_total
    df_with_roasting_orders = pd.merge(
                                df_orders_total
                                ,df_orders
                                ,left_on='Relateret ordre'
                                ,right_on='ORDER_NAME'
                                ,how='left')
    #df_with_roasting_orders['Final_order'] = df_with_roasting_orders['S_ORDER_NAME'].combine_first(df_with_roasting_orders['Relateret ordre'])

    df_orders_final = pd.DataFrame()
    df_orders_final[['Ordre','Relateret ordre']] = df_with_roasting_orders[['Ordre','S_ORDER_NAME']]
    df_orders_final.dropna(inplace=True)
    return df_orders_final
    

df_temp = get_order_relationships_final()



temp_list = get_list_of_missing_values(get_finished_goods_grades()
                                        ,'Ordrenummer'
                                        ,get_order_relationships_final()
                                        ,'Ordre')
print(temp_list)



# WIP below







def get_probat_orders_direct(order_no):
    query_probat_orders = f""" SELECT DISTINCT
                        	PG.[ORDER_NAME] AS [Ordre]
                        	,LG.[S_ORDER_NAME] AS [Relateret ordre]
                        FROM [dbo].[PRO_EXP_ORDER_SEND_PG] AS PG
                        INNER JOIN [dbo].[PRO_EXP_ORDER_LOAD_G] AS LG
                        	ON PG.[S_ORDER_NAME] = LG.[ORDER_NAME]
                        WHERE PG.[ORDER_NAME] IN ({order_no})
                        	AND PG.[S_ORDER_NAME] NOT IN ('Retour Ground','REWORK ROAST' )
                        
                        UNION
                        
                        SELECT DISTINCT
                        	PB.[ORDER_NAME]
                        	,ULR.[ORDER_NAME]
                        FROM [dbo].[PRO_EXP_ORDER_SEND_PB] AS PB
                        INNER JOIN [dbo].PRO_EXP_ORDER_UNLOAD_R AS ULR
                        	ON PB.[S_ORDER_NAME] = ULR.[ORDER_NAME]
                        WHERE PB.[ORDER_NAME] IN( {order_no}) """
    return pd.read_sql(query_probat_orders, con_probat)


    


df_order_relations_total = pd.DataFrame()

# # Using only Probat and only NAV direct
# df_order_relations_total = pd.concat([df_order_relations_total 
#                                      ,get_probat_orders_direct(po_sql_string)
#                                      ,get_nav_orders(po_sql_string, 'df')
#                                      ])
#     # # Using Probat by using NAv for first step
#     # for order_nav in get_nav_orders(order, 'liste'):
#     #     df_order_relations_total = pd.concat( [df_order_relations_total
#     #                                            ,get_probat_orders_using_nav(order_nav)
#     #                                            ])


# df_order_relations_total.reset_index(inplace=True)
# df_order_relations_total.drop_duplicates(subset=['Ordre','Relateret ordre'], inplace=True)
# df_order_relations_total['Varenr'] = df_order_relations_total['Relateret ordre'].apply(lambda x: get_nav_order_info(x))
# df_order_relations_total.dropna(inplace=True)
               
                     
                     
                     
                     
                     
                     
    