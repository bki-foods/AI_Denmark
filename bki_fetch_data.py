#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib
import pandas as pd
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

# server_probat = '192.168.125.161'
# db_probat = 'BKI_IMP_EXP'
# con_probat = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server_probat};DATABASE={db_probat};uid=bki_read;pwd=Probat2016')
# params_probat = urllib.parse.quote_plus(f'DRIVER=SQL Server Native Client 11.0;SERVER={server_probat};DATABASE={db_probat};Trusted_Connection=yes')
# engine_probat = create_engine(f'mssql+pyodbc:///?odbc_connect={params_probat}')


    
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
    


df_temp = get_finished_goods_grades()
print(df_temp)






















# Get info from assembly and production orders in Navision
def get_nav_order_info(order_no):
    df_temp = df_nav_order_info[df_nav_order_info['Ordrenummer'] == order_no]
    if len(df_temp) > 0:
        return df_temp['Varenummer'].iloc[0]

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

def get_nav_orders(order_no, return_type):
    # Get related orders from Navision
    query_nav_order_related = f"""
                           SELECT [Prod_ Order No_] AS [Ordre] 
                           ,[Reserved Prod_ Order No_] AS [Relateret ordre]
                           FROM [dbo].[BKI foods a_s$Reserved Prod_ Order No_]
                           WHERE [Prod_ Order No_] IN ({order_no})
                           AND [Invalid] = 0 """
    df_nav_order_related = pd.read_sql(query_nav_order_related, con_nav)  
    if return_type == 'liste':
        return df_nav_order_related['Relateret ordre'].to_list()
    if return_type == 'df':
        return df_nav_order_related
    
    
def get_probat_orders_using_nav(order_no):
    query_probat_lg = f""" SELECT DISTINCT
                    	[ORDER_NAME] AS [Ordre]
                    	,[S_ORDER_NAME] AS [Relateret ordre]
                    FROM [dbo].[PRO_EXP_ORDER_LOAD_G]
                    WHERE [ORDER_NAME] = '{order_no}' 
                        AND [S_ORDER_NAME] <> 'REWORK ROAST' """
    df_query_probat_lg = pd.read_sql(query_probat_lg, con_probat)
    return df_query_probat_lg


# Query for NAV order info
query_nav_order_info = """ SELECT PAH.[No_] AS [Ordrenummer]
                       ,PAH.[Item No_] AS [Varenummer]
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
                       WHERE PO.[Status] IN (2,3,4)
                           AND I.[Item Category Code] <> 'RÅKAFFE' """
df_nav_order_info = pd.read_sql(query_nav_order_info, con_nav)

# Query to get all relevant orders from BKI_Datastore
query_ds_orders = """SELECT	DISTINCT [Referencenummer] AS [Ordrenummer]
                     FROM [cof].[Smageskema] AS S
                     WHERE COALESCE(S.[Smag_Syre],S.[Smag_Krop],S.[Smag_Aroma],S.[Smag_Eftersmag],S.[Smag_Robusta]) IS NOT NULL
                     AND S.[Referencetype] = 2 AND S.[Referencenummer] IS NOT NULL
                     AND S.[Varenummer] NOT LIKE '1090%' """
df_ds_orders = pd.read_sql(query_ds_orders, con_ds)        
                     
ds_orders_list = df_ds_orders['Ordrenummer'].to_list()
po_sql_string = string_to_sql(ds_orders_list)

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


# # Print de ordrer der ikke er i endelig dataframe
# missing_orders = list(set(ds_orders_list) - set(df_order_relations_total['Ordre']))
# print(missing_orders)

               
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     
                     