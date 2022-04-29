#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import numpy as np
from deap import base, creator, tools, algorithms
from sklearn import preprocessing


def ga_cheapest_blend(contracts, flavors, prices, flavor_model, target_flavor, roast_color, MIN_C=1, MAX_C=7,
                      MIN_P=0.06, MAX_P=1.00):
    """
    This function finds the cheapest coffee blend that is within a tolerance of +/- 1 of each dimension of the
    target taste.

    :param contracts:  A list of contract numbers/ids of length n
    :param flavors: An array of dimension n x d, where n is the number of contracts and d is the number of flavor dimensions
        (typically 5)
    :param prices: A list of prices on an arbitrary scale with length n. The program will standardize these to have mean 0 and
        variance 1.
    :param flavor_model: A model that takes as input a (MAX_C + 1) * d + 1 size input, which is the result of concatenating the flavor
        vectors and proportions of the given components, padding with 0 and finally tacking the roast color on the end
        of the vector. The model returns a prediction of the flavor vector of the given blend. These models are
        typically loaded from a .sav file with joblib.load()
    :param target_flavor: A numpy array of length d which corresponds to the targeted flavor for the blend.
    :param roast_color: The roast color of the blend
    :param MIN_C: The minimum number of components in a blend. Defaults to 1 and should probably not be changed.
    :param MAX_C: The maximum number of components in a blend. Defaults to 7 and cannot be set higher. Should probably not be
        changed.
    :param MIN_P: The minimum proportion of a single component. Default to 0.06, but can be changed to allow even smaller
        proportions or require larger ones.
    :param MAX_P: The maximum proportion of a single component. Defaults to 1.00 and should probably not be changed.
    :return pop, logbook, hof: The final population of optimized blends, the logbook containing statistics of the
        optimization run, and the hall of fame containing best individuals seen.
    """

    # Check that everything is of the right sizes
    assert (len(contracts) == len(flavors))
    assert (len(contracts) == len(prices))

    N = len(contracts)

    # Start initializing the optimization problem as a maximization problem
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    # Register the functions for the evolutionary algorithm
    toolbox = base.Toolbox()
    toolbox.register("indices", initial_blend, N=N)
    toolbox.register("individual", tools.initIterate, creator.Individual,
                     toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutate_blend, p_drop=0.5, p_mutp=0.5, p_mutc=0.5, N=N, MIN_C=MIN_C, MAX_C=MAX_C,
                     MIN_P=MIN_P, MAX_P=MAX_P)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", blend_fitness, prices=prices, flavor_model=flavor_model, candidates=flavors, target=target_flavor,
                     color=roast_color, MAX_C=MAX_C)

    # Add the normalize_p function to mate and mutate to make sure, that the blends are still valid after changes
    toolbox.decorate("mate", normalize_p(N=N, MIN_C=MIN_C, MIN_P=MIN_P, MAX_P=MAX_P))
    toolbox.decorate("mutate", normalize_p(N=N, MIN_C=MIN_C, MIN_P=MIN_P, MAX_P=MAX_P))

    # Initialize a hall of fame, a population of 1000 blends, and some relevant statistics
    pop = toolbox.population(n=1000)
    hof = tools.HallOfFame(20, equal_blends)
    stats_fit = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats_flavor = tools.Statistics(key=lambda ind: sum(taste_diff(ind, flavor_model, candidates=flavors,
                                                                   target=target_flavor, color=roast_color,
                                                                   MAX_C=MAX_C)))
    mstats = tools.MultiStatistics(fitness=stats_fit, flavor_diff=stats_flavor)
    mstats.register("avg", np.mean)
    mstats.register("std", np.std)
    mstats.register("max", np.max)

    # Run a simple evolutionary algorithm for 50 generations
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.3, mutpb=0.6, ngen=50, halloffame=hof, stats=mstats,
                                       verbose=True)

    # Return the final population, the logbook with stats and information about the run, and the hall of fame.
    return pop, logbook, hof


def initial_blend(N, MIN_C=1, MAX_C=7, MIN_P=0.06, MAX_P=1.00):
    components = random.randint(MIN_C, MAX_C)
    indices = random.sample(range(N), components)
    missing = MAX_C - components
    indices = indices + [-1] * missing

    proportions = []
    for i in range(components - 1, 0, -1):
        proportions.append(random.uniform(MIN_P, MAX_P - MIN_P * i - sum(proportions)))

    proportions = [max(round(p, 2), MIN_P) for p in proportions]
    proportions = proportions + [round(MAX_P - sum(proportions), 2)] + [0] * missing

    return (zip(indices, proportions))


def mutate_comp(individual, N):
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    num_components = len(components)

    num_randomize = random.randint(0, num_components)
    if num_randomize == 0:
        return individual,

    rand_comp = random.sample(range(num_randomize), num_randomize)
    stable_comp = [components[i] for i in range(len(components)) if i not in rand_comp]

    for i in rand_comp:
        new_comp = random.sample([j for j in range(N) if j not in stable_comp], 1)
        stable_comp.append(new_comp)
        individual[i] = (new_comp[0], individual[i][1])

    return individual,


def drop_add_comp(individual, N, MIN_C=1, MAX_C=7, MIN_P=0.06, MAX_P=1.00):
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    num_components = len(components)

    target_components = random.randint(MIN_C, MAX_C)
    comp_difference = target_components - num_components
    if comp_difference == 0:
        return individual,
    elif comp_difference < 0:
        rand_comps = random.sample(individual[0:num_components], target_components)
    else:
        potentials = [(j, random.uniform(MIN_P, MAX_P)) for j in range(N) if j not in components]
        rand_comps = individual[0:num_components] + random.sample(potentials, comp_difference)

    for i in range(target_components):
        individual[i] = rand_comps[i]

    for i in range(target_components, size):
        individual[i] = (-1, 0)

    return individual,


def mutate_p(individual, mu, sigma):
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    num_components = len(components)

    old_p = [individual[i][1] for i in range(num_components)]
    mutated_p = [p + random.gauss(mu, sigma) for p in old_p]

    for i in range(num_components):
        individual[i] = (individual[i][0], mutated_p[i])

    return individual,


def mutate_blend(individual, p_drop, p_mutp, p_mutc, N, mu=0, sigma=0.1, MIN_C=1, MAX_C=7, MIN_P=0.06, MAX_P=1.00):
    if (random.random() < p_drop):
        individual, = drop_add_comp(individual, N, MIN_C=MIN_C, MAX_C=MAX_C, MIN_P=MIN_P, MAX_P=MAX_P)

    if (random.random() < p_mutp):
        individual, = mutate_p(individual, mu, sigma)

    if (random.random() < p_mutc):
        individual, = mutate_comp(individual, N)

    return individual,


def normalize_p(N, MIN_C=1, MIN_P=0.06, MAX_P=1.00):
    def decorator(func):
        def wrapper(*args, **kwargs):

            offspring = func(*args, **kwargs)

            for child in offspring:

                size = len(child)
                components = [child[i][0] for i in range(size)]
                unique_comps = list(set(components))
                proportions = [child[components.index(uc)][1] for uc in unique_comps if uc != -1]
                components = [child[components.index(uc)][0] for uc in unique_comps if uc != -1]
                num_components = len(components)

                if num_components < MIN_C:
                    potentials = [(j, random.uniform(MIN_P, MAX_P)) for j in range(N) if j not in components]
                    child[1] = random.sample(potentials, 1)[0]

                    components = [child[i][0] for i in range(size)]
                    unique_comps = list(set(components))
                    proportions = [child[components.index(uc)][1] for uc in unique_comps if uc != -1]
                    components = [child[components.index(uc)][0] for uc in unique_comps if uc != -1]
                    num_components = len(components)

                for i in range(num_components):
                    child[i] = (components[i], proportions[i])

                for i in range(num_components, size):
                    child[i] = (-1, 0)

                old_p = [child[i][1] for i in range(num_components)]

                # Bind the proportions
                bounded_p = [min(max(round(p, 2), MIN_P), MAX_P) for p in old_p]

                diff_from_min = (sum(bounded_p) - MIN_P * num_components)
                if diff_from_min == 0.0:
                    normalized_p = [round(1.00 / num_components, 2) for p in bounded_p]
                else:
                    normalized_p = [round((p - MIN_P) * (1.00 - MIN_P * num_components) / \
                                          diff_from_min + MIN_P, 2) for p in bounded_p]

                max_index = normalized_p.index(max(normalized_p))
                normalized_p[max_index] = round(normalized_p[max_index] + 1.00 - sum(normalized_p), 2)

                for i in range(num_components):
                    child[i] = (child[i][0], normalized_p[i])

            return offspring

        return wrapper

    return decorator


def taste_diff(individual, flavor_model, candidates, target, color, MAX_C=7):
    D = len(candidates[0, :])
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    proportions = [individual[i][1] for i in range(size) if individual[i][0] != -1]
    num_components = len(components)

    model_input = np.array([])
    for c, p in zip(components, proportions):
        model_input = np.concatenate((model_input, candidates[c, :]))
        model_input = np.concatenate((model_input, [p]))
    model_input = np.concatenate((model_input, [0] * ((D + 1) * (size - num_components))))
    model_input = np.concatenate((model_input, [color]))

    # model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1))) # Dette er hvad vi "tror" input individual vil smage som - Let til tests
    # model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) * 2) / 2 # Round to .5 values
    # model_output = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) * 4) / 4 # Round to .25 values
    model_output = flavor_model.predict(np.array(model_input).reshape(1, -1))
    return np.abs(target - model_output)


def blend_cost(individual, prices):
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    proportions = [individual[i][1] for i in range(size) if individual[i][0] != -1]
    costs = [prices[c] * p for c, p in zip(components, proportions)]

    return sum(costs)


def blend_fitness(individual, prices, flavor_model, candidates, target, color, MAX_C=7):
    min_max_scaler = preprocessing.MinMaxScaler()
    prices = min_max_scaler.fit_transform(prices)
    diff = taste_diff(individual, flavor_model, candidates, target, color, MAX_C)
    cost = blend_cost(individual, prices)
    flavor_bound = 1 / (2 ** np.mean(diff ** 3)) # Evt. opløft i 4 eller 5 - ret i 2 eller 3
    
    bki_blend_fitness =  flavor_bound - ( cost * 0.0003)
    
    return bki_blend_fitness
    # return flavor_bound * (1.0 - cost) # Senest aktuelle return value!
    #return flavor_bound / (1.2 ** cost), # Skalering af deres andel bør ikke være nødvendig når der er styr på de mere ekstreme profiler


def equal_blends(ind1, ind2):
    #TODO: Blends er identiske hvis de indeholder de samme kontrakter, uagtet proportionerne
    comp1 = [ind1[i][0] for i in range(len(ind1)) if ind1[i][0] != -1]
    comp2 = [ind2[i][0] for i in range(len(ind2)) if ind2[i][0] != -1]
    return set(comp1) == set(comp2)



#TODO predict taste profile of each blend suggestion
#Blend = først levels i hall of fame, flavor model = model, component_flavors = numpy array med kontrakternes smagsprofil, color = farve
#OBS OBS OBS!!!! Component flavors skal være en liste over samtlige kontrakter med deres smag!!!
def taste_pred(blend, flavor_model, component_flavors, color):
    D = len(component_flavors[0, :])
    size = len(blend)
    components = [blend[i][0] for i in range(size) if blend[i][0] != -1]
    proportions = [blend[i][1] for i in range(size) if blend[i][0] != -1]
    num_components = len(components)

    model_input = np.array([])
    for c, p in zip(components, proportions):
        model_input = np.concatenate((model_input, component_flavors[c, :]))
        model_input = np.concatenate((model_input, [p]))

    model_input = np.concatenate((model_input, [0] * ((D + 1) * (size - num_components))))
    model_input = np.concatenate((model_input, [color]))

    predicted_flavors = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) * 4) / 4 # Round to .25 values

    return predicted_flavors













