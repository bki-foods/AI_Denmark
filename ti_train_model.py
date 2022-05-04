#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import time
import ti_data_preprocessing as tdp
import bki_functions as bf


# Grab Currrent Time Before Running the Code for logging of total execution time
start_time = time.time()
# Write into log that script has started
bf.log_insert("ti_train_model.py", "Training of model has started.")


# Function to swap rows to create more data for training of model
def row_swapper(x):
    row_len = (len(x)-1)//7
    new_row_order = list(range(0,7))
    random.shuffle(new_row_order)
    return np.append(np.array([x[i*row_len:(i+1)*row_len] for i in new_row_order]).flatten(), x[-1])


model_name = "flavor_predictor_robusta.sav"


X,Y = tdp.get_blend_grade_data()

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
perm = np.random.permutation(len(X_train)) # Shuffle data, bare for god ordens skyld..
X_train = X_train[perm, :]
y_train = y_train[perm, :]



X_swapped = [[row_swapper(X_train[i,:]) for i in range(len(X_train))] for j in range(4)] # Byt rundt på rækkefølgen af komponenterne i datasættet, for at skabe "mere" data
X_swapped.append(X_train)
X_augmented = np.concatenate(X_swapped)
y_augmented = np.tile(y_train, (5, 1))
perm = np.random.permutation(len(X_augmented))
X_train_ext = X_augmented[perm, :]
y_train_ext = y_augmented[perm, :]
# Train model
regr = MLPRegressor(hidden_layer_sizes=(300, 200, 100, 100), alpha=0.01, activation="tanh", max_iter=2000).fit(X_train_ext, y_train_ext)
# Save trained model
joblib.dump(regr, model_name)


# Evaluate model
n = len(X_test)
y_hat = regr.predict(X_test[0:n,:])
print("NN: \t\tMSE: {0}, \n\t\tMAE: {1}"\
      .format(mean_squared_error(y_test, y_hat, multioutput="raw_values"),
              mean_absolute_error(y_test, y_hat, multioutput="raw_values")))
    
    
# Grab Currrent Time After Running the Code for logging of total execution time
end_time = time.time()
total_time = end_time - start_time
#Subtract Start Time from The End Time
total_time_seconds = int(total_time) % 60
total_time_minutes = total_time // 60
total_time_hours = total_time // 60
execution_time = str("%d:%02d:%02d" % (total_time_hours, total_time_minutes, total_time_seconds))
# Write into log that script has completed
bf.log_insert("ti_train_model.py", f"Training of model has completed. Total time: {execution_time}")
    
    