import numpy as np


def trim_nan_rows(data):
    """ Removes any continuous sections of NaN-containing rows at the beginning and end of the data

    Args:
        data (DataFrame): DataFrame that may have leading or trailing rows containing NaN

    Returns:
        DataFrame: Subset of input data that does not have leading or trailing rows containing NaN
    """
    
    nan_sum = data.isna().sum(1)
    has_nan = nan_sum > 0
    any_nan = has_nan.replace(True, np.nan)
    first_valid = any_nan.first_valid_index()
    last_valid = any_nan.last_valid_index()

    if first_valid is None and last_valid is not None:
        data.loc[:last_valid]
    elif first_valid is not None and last_valid is None:
        return data.loc[first_valid:]
    elif first_valid is None and last_valid is None:
        return data
    
    return data.loc[first_valid: last_valid]