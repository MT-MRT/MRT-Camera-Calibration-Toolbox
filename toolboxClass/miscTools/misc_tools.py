import itertools
import operator as op
from functools import reduce
from numpy.random import permutation
import numpy as np

def ncr(n, r):
    '''Function to get maximum possible combinations given n and r'''
    # https://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function
    # -in-python
    r = min(r, n - r)
    numer = reduce(op.mul, range(n, n - r, -1), 1)
    denom = reduce(op.mul, range(1, r + 1), 1)
    return int(numer / denom)


def get_one_combination(n, r):
    '''Function to calculate one possible combination given n and r'''
    for item in itertools.combinations(permutation(n), r):
        sample = list(item)
        sample.sort()
        return sample


def get_all_combinations(n, r):
    '''Function to get all possible combinations given n and r'''
    samples = []
    for item in itertools.combinations(list(range(n)), r):
        item_s = list(item)
        item_s.sort()
        samples.append(item_s)
    return samples


def validate(action, index, value_if_allowed, prior_value, text,
             validation_type, trigger_type, widget_name, allowed):
    '''Function to check if entry value is correct'''
    # https://stackoverflow.com/questions/8959815/
    # restricting-the-value-in-tkinter-entry-widget
    if (action == '1'):
        if text in allowed:
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False
    else:
        return True


def float2StringVar(string, value, decimals=5):
    '''Function to set string given its value'''
    if value == 0 or value is None:
        string.set('-')
    else:
        string.set(str(round(value, decimals)))

def get_indices_to_average(rms, percentile = 75):
    '''Function to obtain array indices within percentile'''
    rms_max = np.percentile(rms, percentile)
    indices = [i for i,v in enumerate(rms) if v < rms_max]
    return indices