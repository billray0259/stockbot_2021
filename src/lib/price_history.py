import os

import pandas as pd
import numpy as np
import pandas_ta as ta

import pandas_market_calendars as mcal

from src.lib.util import trim_nan_rows


def read_price_history(symbol, data_dir=None, path=None):
    """ Reads a CSV from the `data_dir`/`symbol`/`symbol`_1Min.csv file with a DateTimeIndex

    Args:
        symbol (str): Stock market symbol to read ex. SPY
        data_dir (str, optional): Directory to look for extracted/`symbol`/`symbol`_1Min.csv path. Defaults to data/
        path (str, optional): Full path to the data file. If None the full path is created from the symbol and data_dir

    Returns:
        PriceHistory: DataFrame with DateTimeIndex and columns [open, high, low, close, volume, trades, vwap]
    """

    data_path = path or os.path.join(data_dir or "data/", symbol, f"{symbol}_1Min.csv")
    data = pd.read_csv(data_path, index_col="time")
    data.index = pd.to_datetime(data.index)

    candle_cols = set(["open", "high", "low", "close", "volume", "trades", "vwap"])
    assert set(data.columns) == candle_cols, "Candles data file has unexpected columns"

    return PriceHistory(data, symbol)


def transform_price_history(price_history, **kwargs):
    """ Transforms candle-stick data
    * Isolates market hours
    * Fills NaN values with sensible values
    * Adds technical analysis indicators
    * Removes columns that cannot be scaled [open, high, low, close]
    * Trims leading and trailing rows containing NaNs

    Args:
        candles (DataFrame): DataFrame with columns [open, high, low, close, volume, vwap]
    
    kwargs:
        calendar (str, optional): The [pandas_market_calendars](https://pandas-market-calendars.readthedocs.io/en/latest/) calendar to use. Defaults to "NYSE".
        indicators (str list, optional): List of indicators to get. If None [log_rets_close, ma_50, ma_200, rsi, macd, bbands].
        main_column (str, optional): The column to calculate the indicators with. Defaults to close.

    Returns:
        DataFrame: DataFrame with only market hour index, no NaNs, and technical indicators
    """

    calendar = "NYSE"
    indicators = None
    main_column = "close"

    if kwargs is not None:
        if "calendar" in kwargs:
            calendar = kwargs["calendar"]

        if "indicators" in kwargs:
            indicators = kwargs["indicators"]

        if "main_column" in kwargs:
            main_column = kwargs["main_column"]

    return price_history \
        .isolate_market_hours(calendar=calendar) \
        .fill_nan_candles() \
        .add_ta_indicators(indicators=indicators, main_column=main_column) \
        .drop_non_scalable() \
        .trim_nan_rows()



class PriceHistory:

    def __init__(self, data, symbol):
        assert len(data) > 0, "Can not accept empty data"
        
        self.data = data
        self.start_date = data.index[0]
        self.end_date = data.index[-1]
        self.symbol = symbol
    

    def trim_nan_rows(self):
        """ Removes any continuous sections of NaN-containing rows at the beginning and end of the data

        Args:
            data (DataFrame): DataFrame that may have leading or trailing rows containing NaN

        Returns:
            DataFrame: Subset of input data that does not have leading or trailing rows containing NaN
        """
        data = trim_nan_rows(self.data)
        return PriceHistory(data, self.symbol)


    def isolate_market_hours(self, calendar="NYSE"):
        """ Reindexes the data with every on-hour (weekdays 9:30 am EST - 4:00 pm EST] minutely time in the data range.
        * Does not include minutes for holidays or weekends.
        * Does not pad the data by inserting times before or after the first or last time in the original data.

        Args:
            data (DataFrame): DataFrame with datetime index
            calendar (str, optional): The [pandas_market_calendars](https://pandas-market-calendars.readthedocs.io/en/latest/) calendar to use. Defaults to "NYSE".

        Returns:
            DataFrame: Reindexed data to contain market hour timestamps. No more, no less.
        """
        start_date = self.data.index[0]
        end_date = self.data.index[-1]

        nyse = mcal.get_calendar(calendar)

        schedule = nyse.schedule(start_date=start_date, end_date=end_date)
        date_range = mcal.date_range(schedule, frequency="1T")
        market_hours = self.data.reindex(date_range)[self.start_date: self.end_date]
        return PriceHistory(market_hours, self.symbol).trim_nan_rows()
    
    
    def fill_nan_candles(self):
        '''
        Replaces NaN values in candle-stick data with sensible values
        * OHLC and vwap get filled with the previouse close
        * volume and trades get filled with 0

        Args:
            data (DataFrame): Candle stick data with columns [open, high, low, close, vwap, volume, trades]
        
        Returns:
            DataFrame: Data without NaNs in columns [open, high, low, close, vwap, volume, trades]
        '''
        filled_data = self.data.copy()
        
        filled_data['close'] = filled_data['close'].fillna(method='ffill')

        for col in ["open", "high", "low", "vwap"]:
            filled_data[col] = filled_data[col].fillna(filled_data['close'])
        
        for col in ["volume", "trades"]:
            filled_data[col] = filled_data[col].fillna(0)

        return PriceHistory(filled_data, self.symbol)
    

    def add_ta_indicators(self, indicators=None, main_column="close"):
        """ Creates a DataFrame containing the specified indicators. Does not contain original columns.

        Indicators:
        * rets_`*`: Calculates the simple returns of the column with name `*`
        * log_rets_`*`: Calculates the log returns of the column with name `*`
        * pdiff_`*`: Calculates the percent change from `main_column` to the column with name `*`
        * ma`*`: Calculates the n=`*` time step moving average of the `main_column`
        * rsi: Calculates the RSI using the `main_column`
        * macd: Calculates the MACDh_12_26_9 using the `main_column`
        * bbands: Calculates the BBB_5_2.0 and BBP_5_2.0 using the `main_column`


        Args:
            data (DataFrame): Close column
            indicators (str list, optional): List of indicators to get. If None [oc_ret, log_ret_close, pdiff_open, pdiff_high, pdiff_low, ma_50, ma_200, rsi, macd, bbands].
            main_column (str, optional): The column to calculate the indicators with. Defaults to close.

        Returns:
            DataFrame: Dataframe of indicators derived from provided data
        """
        if indicators is None:
            indicators = [
                "oc_ret", # close/open - 1
                "log_ret_close",
                "pdiff_open",
                "pdiff_high",
                "pdiff_low",
                "pdiff_vwap",
                "ma_50",
                "ma_200",
                "rsi",
                "macd",
                "bbands"
            ]
        
        indicator_data = {}

        for indicator in indicators:
            if indicator == "oc_ret":
                indicator_data[indicator] = self.data["close"]/self.data["open"] - 1

            elif indicator == "rsi":
                indicator_data[indicator] = ta.rsi(self.data[main_column])
            
            elif indicator == "macd":
                indicator_data[indicator] = ta.macd(self.data[main_column])["MACDh_12_26_9"]
            
            elif indicator == "bbands":
                bbands = ta.bbands(self.data[main_column])
                bbands.fillna(method="ffill", axis=0, inplace=True)
                indicator_data["bbands_b"] = bbands["BBB_5_2.0"]
                indicator_data["bbands_p"] = bbands["BBP_5_2.0"]

            elif indicator.startswith("log_rets_"):
                column = indicator[len("log_rets_"):]
                log_rets = np.zeros(len(self.data))
                log_rets[0] = np.nan
                log_rets[1:] = np.diff(np.log(self.data[column]))
                indicator_data[indicator] = log_rets
            
            elif indicator.startswith("rets_"):
                column = indicator[len("rets_"):]
                rets = np.zeros(len(self.data))
                rets[0] = np.nan
                column_values = self.data[column].to_numpy()
                rets[1:] = column_values[1:]/column_values[:-1] - 1
                indicator_data[indicator] = rets

            elif indicator.startswith("ma_"):
                length = int(indicator[len("ma_"):])
                # moving_average = self.data[main_column].rolling(window=length, min_periods=length).mean()
                moving_average = ta.sma(self.data[main_column], length)
                indicator_data[indicator] = moving_average/self.data[main_column] - 1
            
            elif indicator.startswith("pdiff_"):
                column = indicator[len("pdiff_"):]
                indicator_data[indicator] = self.data[column]/self.data[main_column] - 1
        
        indicator_data = pd.DataFrame(indicator_data)

        return PriceHistory(self.data.join(indicator_data), self.symbol)

    def drop_non_scalable(self, columns=None):
        """ Drops the specified columns

        Args:
            data (DataFrame): Data with unscalable columns
            columns (str list, optional): [description]. If None, [open, high, low, close, vwap].

        Returns:
            DataFrame: Data without specified columns
        """
        if columns is None:
            columns = [
                "open",
                "high",
                "low",
                "close",
                "vwap"
            ]
        
        return PriceHistory(self.data.drop(columns, axis=1), self.symbol)