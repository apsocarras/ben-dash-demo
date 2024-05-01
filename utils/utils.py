import os
import datetime as dt 
import json
import yaml
import pandas as pd 
import numpy as np
from scipy.signal import argrelextrema

### ------------------------------------------------------------------------------ ###
### --- GENERAL UTILS  --- ###

def print_df(df):
    for line in df.to_csv(index=False).splitlines(): 
        print(line.replace(',',', '))

def combine_dicts(*dicts):
    combined_dict = {}
    for d in dicts:
        combined_dict.update(d)
    return combined_dict

def get_hourly_wage(annual):
    # Assuming you work a 40 hour week, 52 weeks in a year 
    return f"${(annual/52)/40:.2f}"

def format_int_dollars(n:int) -> str: 
    return '${:,.7}'.format(float(n)).rstrip('0').rstrip('.')

def find_derivative(x,y, non_negative=True) -> tuple: 
    """Find derivative & relative minima """
    ## Derivative  
    derivative = np.gradient(y,x)
    derivative_rel_minima = argrelextrema(derivative, np.less)[0]
    if non_negative:
        derivative_rel_minima = derivative_rel_minima[derivative_rel_minima > 0] # non-negative
    return derivative, derivative_rel_minima

def find_zero_intercepts(ls:list):
    """Get points (indices) of curve (iterable) which first intersect with x-axis (0) (i.e. previous value must be non-zero)""" 

    zero_indices = []
    on_zero = True  # treat first element in list as if we're already on zero (there's no previous point)
    for n in range(len(ls)):
        if ls[n] == 0:
            if not on_zero: # i.e. we found a zero and we're not already on the axis 
                zero_indices.append(n)
                on_zero = True
            else: 
                continue
        else: 
            on_zero = False

    return zero_indices

### ------------------------------------------------------------------------------ ###
### --- BENEFITS FUNCTIONS --- ###

def filter_benefits(df, include_eitc=True, include_ctc=True): 
    """Filter df to relevant benefits columns"""
    df_benefits = df.loc[:, ((df != 0).any(axis=0) & (df == 0).any(axis=0))]\
            .filter(regex='value') # Must have non-zero and zero values to potentially cause a cliff
    if not include_eitc: 
        df_benefits = df_benefits[[col for col in df_benefits.columns if 'eitc' not in col]]
    if not include_ctc: 
        df_benefits = df_benefits[[col for col in df_benefits.columns if 'ctc' not in col]]
    return df_benefits


def find_benefits_cliffs(df, derivative_rel_minima, mode='peak') -> dict: 
    """Find benefits cliffs from zeros in benefits curves and the minima of the derivative of the income vs. net resources curve
    
    Args

    df (dataframe): Dataframe with benefits columns recognized in filter_benefits()

    mode (str): 'peak' (return index of peak of cliff) or 'valley' (return index of bottom of cliff)
    
    Returns 

    cliffs (dict): {<benefits_column>:[<cliff-1>,...,<cliff-n>]}
    
    """

    if mode == 'peak': 
        offset = 1
    elif mode == 'valley': 
        offset = 0
    else: 
        raise Exception("'mode' must be one of 'peak' or 'valley'")
 
    df_benefits = filter_benefits(df, include_eitc=False)
    cliffs = {}

    for col in df_benefits.columns: 
        zeros = find_zero_intercepts(df_benefits[col].tolist())
        col_cliffs = [x - offset for x in zeros if any(x in range(e,e+2) for e in derivative_rel_minima)] # pd.Interval(e-1,e+1, closed='both') -- since derivative curve is discrete I don't think this is need
        if len(col_cliffs) > 0:
            cliffs[col] = col_cliffs

    return cliffs 


### ------------------------------------------------------------------------------ ###
## --- DEPRECATED: Used for illustration in identify-cliffs-plotly.ipynb only ---  ##

def find_zeros(df,include_first=False) -> list: 
    """Find the first index of zero in each column of a dataframe"""
    if include_first: 
        zeros = [{col:df[col].to_list().index(0)} for col in df.columns]
    else: 
        zeros = []
        for col in df.columns: 
            idx_first_nonzero = -1
            for n,v in enumerate(df[col].values): 
                if v > 0:
                    idx_first_nonzero = n
                    break      
            try: 
                zero = df[col][idx_first_nonzero:].to_list().index(0)
            except ValueError: 
                continue # no zero in rest of the column
            if zero != -1: 
                zeros.append({col:zero})
    zeros.sort(key=lambda x: list(x.values())[0])
    return zeros 