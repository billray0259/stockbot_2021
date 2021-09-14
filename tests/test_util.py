from src.lib.util import *

import pandas as pd
import numpy as np

def test_trim_nan_rows():

    df = pd.DataFrame(data=np.random.random((10, 3)), index=np.arange(10), columns=["A", "B", "C"])
    df.iloc[0, :] = np.nan
    df.iloc[1, 0] = np.nan
    df.iloc[-1, 1:3] = np.nan
    df.iloc[-2, 2] = np.nan
    
    trimmed = trim_nan_rows(df)

    assert trimmed.iloc[0].isna().sum() == 0, "There exists a leading NaN row"
    assert trimmed.iloc[-1].isna().sum() == 0, "There exists a trailing NaN row"
    assert len(trimmed) == 6, "Unexpected length"
    assert list(trimmed.columns) == list(df.columns), "Unexpected columns"
    assert (trimmed.to_numpy() == df.to_numpy()[2:-2]).all(), "Unexpected values"
    assert (trimmed.index == np.arange(2, 8)).all(), "Unexpected index"

    empty_df = pd.DataFrame(data=[])
    empty_trimmed = trim_nan_rows(empty_df)

    assert len(empty_trimmed) == 0, "Empty DataFrame comes back non-empty"

    
    
