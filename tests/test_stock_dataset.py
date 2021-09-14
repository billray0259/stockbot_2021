import random
from dateutil import parser
import pandas as pd

from src.lib.stock_dataset import *
from src.lib.price_history import read_price_history



def test_read_stock_dataset():
    symbols = ["SPY", "SPXS"]
    dataset = read_stock_dataset(symbols, "close", 64, transform=False, data_dir="tests/test_data")
    assert dataset.symbols == symbols, "Unexpected symbols"
    assert (dataset.X.index == dataset.y.index).all(), "X and y have different indecies"
    
    with open("tests/test_data/SPY/SPY_1Min.csv", "r") as f:
        lines = f.readlines()

    for _ in range(100):
        random_line = random.choice(lines)
        items = random_line.split(",")
        date = parser.parse(items[0])
        row = dataset.X.loc[date]
        for i, col in enumerate([col for col in dataset.X.columns if col.startswith("SPY_")]):
            assert row[col] == float(items[i+1]), f"Unexpected value at {col} {items[0]}"



def test_get_batch():
    symbols = ["SPY", "SPXS"]
    dataset = read_stock_dataset(symbols, "oc_ret", 64, transform=True, data_dir="tests/test_data")

    X, y = dataset.get_batch(1, [64])

    for i, symbol in enumerate(symbols):
        inds = np.where([col.startswith(f"{symbol}_") for col in dataset.X.columns])[0]
        X_data = X[0][:, inds]
        y_data = y[0][i]

        history = read_price_history(symbol, data_dir="tests/test_data")
        historyt = transform_price_history(history)

        assert (historyt.data.to_numpy()[:64] == X_data).all(), "Unexpected X values"
        assert historyt.data["oc_ret"].to_numpy()[64] == y_data, "Unexpected y value"
