import itertools
import operator as op
from functools import reduce

from numpy.random import permutation

'''
Function to get maximum possible combinations given n and r
'''


def ncr(n, r):
    # https://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function-in-python
    r = min(r, n - r)
    numer = reduce(op.mul, range(n, n - r, -1), 1)
    denom = reduce(op.mul, range(1, r + 1), 1)
    return numer / denom


'''
Function to calculate different combinations sets 
'''


def combination(n, r, k):
    index = 0
    k = min(ncr(n, r), k)
    samples = []
    b_c = True
    while b_c:
        for item in itertools.combinations(permutation(n), r):
            if index == k - 1:
                b_c = False
            s_item = list(item)
            s_item.sort()
            if s_item not in samples:
                samples.append(s_item)
                index += 1
                break

    '''
    # Shows how many times each elements is used
    for i in range(n):
        counter = sum(x.count(i) for x in samples)
        print("%d is %d times"%(i,counter))
    '''
    return samples, k


'''
Function to check if entry value is correct
'''


def validate(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name, allowed):
    # https://stackoverflow.com/questions/8959815/restricting-the-value-in-tkinter-entry-widget
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


'''
Function to set string given its value
'''


def float2StringVar(string, value, decimals=5):
    if value == 0 or value is None:
        string.set('-')
    else:
        string.set(str(round(value, decimals)))
