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
    # Set variables for which locations are to be included.
    dict_locations = {
        'SILOER': request_dataframe['Lager_siloer'].iloc[0],
        'WAREHOUSE': request_dataframe['Lager_warehouse'].iloc[0],
        'AARHUSHAVN': request_dataframe['Lager_havn'].iloc[0],
        'SPOT': request_dataframe['Lager_spot'].iloc[0],
        'AFLOAT': request_dataframe['Lager_afloat'].iloc[0],
        'UDLAND': request_dataframe['Lager_udland'].iloc[0]
        }
    # Remove dictionary keys where value == 0
    for key,value in list(dict_locations.items()):
        if value == 0:
           del dict_locations[key]

    print(dict_locations)

    min_quantity = request_dataframe['Minimum_lager'].iloc[0]
    
    df = pd.DataFrame(columns=['Lokation','Kontrakt','Modtagelse','Beholdning'])
    
    df = pd.concat([
        get_spot_available_quantities(),
        get_havn_available_quantities(),
        get_udland_available_quantities(),
        get_afloat_available_quantities(),
        get_silos_available_quantities(),
        get_warehouse_available_quantities()
        ])

    
    print(df)
    # Lager_siloer | Lager_warehouse | Lager_havn | Lager_spot | Lager_afloat | Lager_udland





get_all_available_quantities(get_ds_blend_request())


























