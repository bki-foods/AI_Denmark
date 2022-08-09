#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib
from sqlalchemy import create_engine


# =============================================================================
# Variables for query connections
# =============================================================================
server_04 = "sqlsrv04"
db_ds = "BKI_Datastore"
params_ds = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={server_04};DATABASE={db_ds};trusted_connection=yes"
con_ds = create_engine('mssql+pyodbc:///?odbc_connect=%s' % urllib.parse.quote_plus(params_ds))

server_nav = r"SQLSRV03\NAVISION"
db_nav = "NAV100-DRIFT"
params_nav = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={server_nav};DATABASE={db_nav};trusted_connection=yes"
con_nav = create_engine('mssql+pyodbc:///?odbc_connect=%s' % urllib.parse.quote_plus(params_nav))

server_probat = "192.168.125.161"
db_probat = "BKI_IMP_EXP"
params_probat = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={server_probat};DATABASE={db_probat};uid=bki_read;pwd=Probat2016"
con_probat = create_engine('mssql+pyodbc:///?odbc_connect=%s' % urllib.parse.quote_plus(params_probat))

# =============================================================================
# Filepaths
# =============================================================================
filepath_report = r"\\appsrv07\Python filer\Receptforslag"


