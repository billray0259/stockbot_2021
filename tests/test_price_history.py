from src.lib.price_history import *
import random
from dateutil import parser
import pandas as pd

# TODO test_fill_nan_candles
# TODO test_add_ta_indicators
# TODO test_drop_non_scalable

ph = read_price_history("SPY", data_dir="tests/test_data")


def test_read_price_history():
    price_history = read_price_history("SPY", data_dir="tests/test_data")
    assert price_history.symbol == "SPY", f"Unexpected symbol {price_history.symbol}"
    assert price_history.data is not None, "Data is None"

    df = price_history.data

    assert len(df) == 1127435, "Unexpected data length"
    assert list(df.columns) == ["open", "high", "low", "close", "volume", "trades", "vwap"], "Unexpected columns"

    with open("tests/test_data/SPY/SPY_1Min.csv", "r") as f:
        lines = f.readlines()
    
    for _ in range(100):
        random_line = random.choice(lines)
        items = random_line.split(",")
        date = parser.parse(items[0])
        row = df.loc[date]
        for i, col in enumerate(df.columns):
            assert row[col] == float(items[i+1]), f"Unexpected value at {col} {items[0]}"


def test_transform_price_history():
    transformed = transform_price_history(ph)

    assert transformed is not ph, "Did not return new object"
    assert transformed.data is not ph.data, "The data of the PriceHistory returned was same object as the oiriginal data"
    assert transformed.symbol == ph.symbol, "Unexpected symbol"

    with open("tests/test_data/SPY/SPY_1Min.csv", "r") as f:
        lines = f.readlines()
    
    n_trials = 0
    while n_trials < 100:
        random_line = random.choice(lines)
        items = random_line.split(",")
        date = parser.parse(items[0])

        if not date in transformed.data.index:
            continue
        n_trials += 1

        row = transformed.data.loc[date]

        txt_cols = ["open","high","low","close","volume","trades","vwap"]
        values = dict(zip(txt_cols, map(float, items[1:])))

        assert row["volume"] == values["volume"], "Unexpected volume"
        assert row["trades"] == values["trades"], "Unexpected trades"
        assert row["oc_ret"] == values["close"]/values["open"] - 1, "Unexpected oc_ret"
        assert row["pdiff_high"] == values["high"]/values["close"] - 1, "Unexpected pdiff_high"
        assert row["pdiff_vwap"] == values["vwap"]/values["close"] - 1, "Unexpected pdiff_vwap"

def test_trim_nan_rows():
    df = ph.data.copy()
    df.iloc[0, 0] = np.nan
    trimmed = ph.trim_nan_rows()

    assert trimmed is not ph, "Did not return new object"
    assert trimmed.data is not ph.data, "The data of the PriceHistory returned was same object as the oiriginal data"
    assert trimmed.symbol == ph.symbol, "Unexpected symbol"

    assert trimmed.data.iloc[0].isna().sum() == 0, "There exists a leading NaN row"
    assert trimmed.data.iloc[-1].isna().sum() == 0, "There exists a trailing NaN row"


def test_isolate_market_hours():
    isolated = ph.isolate_market_hours()

    assert isolated is not ph, "Did not return new object"
    assert isolated.data is not ph.data, "The data of the PriceHistory returned was same object as the oiriginal data"
    assert isolated.symbol == ph.symbol, "Unexpected symbol"

    assert isolated.data.index[0] >= ph.data.index[0], "The first date is earlier after isolation"
    assert isolated.data.index[-1] <= ph.data.index[-1], "The last date is later after isolation"