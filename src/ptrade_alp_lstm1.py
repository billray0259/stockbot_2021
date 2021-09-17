""" Alpaca Paper Trade with the 1st LSTM """

import os
import json

import time
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone
import pickle

import pandas_market_calendars as mcal
from keras.models import load_model

from lib.alpaca_historical import AlpacaData
from lib.alpaca_paper import AlpacaTrader
from lib.activations import negative_softmax
from lib.price_history import transform_price_history
from lib.stock_dataset import StockDataset



path = "results/1_lstm_msla/"
keys = "alpaca_config.json"
isPaper = True

def now_utc():
    return datetime.now().astimezone(tz=timezone("UTC"))


def get_next_trading_minute():
    nyse = mcal.get_calendar("NYSE")
    now = now_utc()
    lookahead = timedelta(days=0)
    while True:
        lookahead += timedelta(hours=1)
        schedule = nyse.schedule(start_date=now, end_date=now + lookahead)
        valid_minutes = mcal.date_range(schedule, frequency="1T")
        where_future = np.where(valid_minutes > now)[0]
        if len(where_future) > 0:
            break

    # return valid_minutes[where_future[0]]
    return (now + timedelta(minutes=1)).replace(second=0)

api_data = AlpacaData(keys)
api_trade = AlpacaTrader(keys, isPaper)
model = load_model(
    os.path.join(path, "model.h5"),
    custom_objects={
        "negative_softmax": negative_softmax
    }
)

with open(os.path.join(path, "config.json"), "r") as f:
    config = json.load(f)

n_time_steps = config["n_time_steps"]
symbols = config["symbols"]
target_column = config["target_column"]

with open(os.path.join(path, "scaler.pkl"), "rb") as f:
    scaler = pickle.load(f)

def trade_loop():
    # Sleep until next trading time
    next_trade_time = get_next_trading_minute()
    print("Sleeping for %.2f seconds" % (next_trade_time - now_utc()).total_seconds())
    time.sleep((next_trade_time - now_utc()).total_seconds())

    # Get the last 64 candles
    data_start_time = next_trade_time - timedelta(minutes=1) * n_time_steps
    price_histories = []
    for symbol in symbols:
        history = api_data.get_bars(symbol, data_start_time, next_trade_time, logs=True)
        # TODO accept **kwargs here
        history = transform_price_history(history)
        price_histories.append(history)
    
    # Process the candes
    dataset = StockDataset(price_histories, target_column, n_time_steps)
    dataset.apply_standard_scaler(scaler)
    print(dataset.data)
    X = dataset.prediction_X(n_time_steps)
    
    # Model makes predictions
    next_holdings = model.predict(X)[0]

    print(next_holdings)

    # api_trade.update_holdings(next_holdings)

while True:
    trade_loop()