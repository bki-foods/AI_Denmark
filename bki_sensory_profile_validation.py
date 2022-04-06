#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import bki_functions as bf



# Get grades for finished goods
df_fp = bf.get_finished_goods_grades()
df_fp['Type'] = 'f'
fp_value_count = pd.DataFrame(df_fp['Ordrenummer'].value_counts())
# df_fp['Count'] = df_fp.add(fp_value_count, axis=1)
# Get grades for green coffees
df_rp = bf.get_gc_grades()
# Måske merge med kontraktnummer???
df_rp['Type'] = 'r'
# Concat dataframes
df_profiles = pd.concat([df_fp,df_rp])

print(df_profiles)





#df.apply(pd.Series.value_counts





