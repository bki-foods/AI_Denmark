#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import ti_data_preprocessing as tdp


def row_swapper(x):
    row_len = (len(x)-1)//7
    new_row_order = list(range(0,7))
    random.shuffle(new_row_order)
    return np.append(np.array([x[i*row_len:(i+1)*row_len] for i in new_row_order]).flatten(), x[-1])


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
joblib.dump(regr, "bki_flavor_predictor_robusta.sav")



# Evaluate model
n = len(X_test)
y_hat = regr.predict(X_test[0:n,:])
print("NN: \t\tMSE: {0}, \n\t\tMAE: {1}"\
      .format(mean_squared_error(y_test, y_hat, multioutput='raw_values'),
              mean_absolute_error(y_test, y_hat, multioutput='raw_values')))
    
    
    
    
    
    
    
    