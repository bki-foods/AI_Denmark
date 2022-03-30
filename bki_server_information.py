#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib
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

server_probat = '192.168.125.161'
db_probat = 'BKI_IMP_EXP'
con_probat = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server_probat};DATABASE={db_probat};uid=bki_read;pwd=Probat2016')

# =============================================================================
# Filepaths
# =============================================================================
filepath_report = r'\\appsrv07\Python filer\Receptforslag'
