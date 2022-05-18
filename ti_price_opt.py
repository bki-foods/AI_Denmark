#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import statistics
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
    hof = tools.HallOfFame(50, blends_too_similar)
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
    """
    Create the initial blend consisting of components between MIN_C and MAX_C with proportions
    between MIN_P and MAX_P. If no of components is below MIN_C the blend is padded with -1
    as placeholder values.
    """
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
    """
    Changes a random number of components in an input blend.
    """
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
    """
    Function to either do nothing to a blend, remove a random component or add a random component.
    """
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
    """
    Change the proportions of a blend, but keep the komponents the same.
    """
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    num_components = len(components)

    old_p = [individual[i][1] for i in range(num_components)]
    mutated_p = [p + random.gauss(mu, sigma) for p in old_p]

    for i in range(num_components):
        individual[i] = (individual[i][0], mutated_p[i])

    return individual,


def mutate_blend(individual, p_drop, p_mutp, p_mutc, N, mu=0, sigma=0.1, MIN_C=1, MAX_C=7, MIN_P=0.06, MAX_P=1.00):
    """
    Randomly decide whether a blend is to have its components changed, proportions changed or added/removed components.
    A blend may also have nothing done to it.
    """
    # Maybe
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
    """
    Calculates the aboslut difference between the calculated taste profile of a blend and the target values.
    """
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

    # Do no rounding of the predicted flavor to ensure that the tolerances of deviation from target values are not unintentionally inflated.
    model_output = flavor_model.predict(np.array(model_input).reshape(1, -1))
    return np.abs(target - model_output)


def blend_cost(individual, prices):
    """
    Calculated the cost of any input blend using the prices as input.
    """
    size = len(individual)
    components = [individual[i][0] for i in range(size) if individual[i][0] != -1]
    proportions = [individual[i][1] for i in range(size) if individual[i][0] != -1]
    costs = [prices[c] * p for c, p in zip(components, proportions)]

    return sum(costs)


def blend_fitness(individual, prices, flavor_model, candidates, target, color, MAX_C=7):
    """
    Returns a value of a scale 0-1 which indicates the proposed blends overall fitness as a candidate.
    The closer the value is to 1 the better fitness.
    """
    min_max_scaler = preprocessing.MinMaxScaler()
    prices = min_max_scaler.fit_transform(prices)
    diff = taste_diff(individual, flavor_model, candidates, target, color, MAX_C)
    cost = blend_cost(individual, prices)
    flavor_bound = 1 / (2 ** np.mean(diff ** 3))
    
    bki_blend_fitness =  flavor_bound - ( cost * 0.005)
    
    return bki_blend_fitness


def blends_too_similar(blend1, blend2) -> bool:
    """
    Compares two proposed blends of coffees. If they do not contain exactly the same components,
    they are deemed different. If they contain the exact same components, they are deemed different enough
    if the mean ABS differences in proportions are >= 0.1.
    Returns bool | True if blends are too equal
    """
    # Get list of components in each blend, -1 to remove placeholder values
    blend_1_components = [blend1[i][0] for i in range(len(blend1)) if blend1[i][0] != -1]
    blend_2_components = [blend2[i][0] for i in range(len(blend2)) if blend2[i][0] != -1]
    # Do blends contain same items. If not they are different already
    blends_too_similar = set(blend_1_components) == set(blend_2_components)
    # If both blends contain same items, compare proportions
    if blends_too_similar:
        # Get lists of proportions for each blend
        blend_1_proportions = [blend1[i][1]  for i in range(len(blend1)) if blend1[i][0] != -1]
        blend_2_proportions = [blend2[i][1]  for i in range(len(blend2)) if blend2[i][0] != -1]
        # Get the ABS difference between the blends. Round to prevent issues with floats
        blends_differences = [round(abs(b1 - b2),2) for b1, b2 in zip(blend_1_proportions, blend_2_proportions)]
        # Blends are different enough if the mean ABS change is >= 0.1 across components
        blends_too_similar = statistics.mean(blends_differences) < 0.1
    return blends_too_similar


#TODO predict taste profile of each blend suggestion
#Blend = først levels i hall of fame, flavor model = model, component_flavors = numpy array med kontrakternes smagsprofil, color = farve
#OBS OBS OBS!!!! Component flavors skal være en liste over samtlige kontrakter med deres smag!!!
def taste_pred(blend, flavor_model, component_flavors, color):
    """
    Predict a flavor profile of a given input blend.
    Parameters
    ----------
    blend : A nested list containing component id and proportion.
    flavor_model : The full name and path of the trained model used to predict flavor profile.
    component_flavors : A full list of flavors for all components available, not just those included in the blend.
    color : The target color of the blend.
    Returns
    -------
    A list with the predicted flavor profile of the input blend.
    """
    
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

    predicted_flavors = np.round(flavor_model.predict(np.array(model_input).reshape(1, -1)) ,1)

    return predicted_flavors[0]



