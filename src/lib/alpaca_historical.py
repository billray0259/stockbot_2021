import requests
import datetime as dt
import pytz
import json
import pandas as pd
import pytz
from tqdm import tqdm

class AlpacaData():
    def __init__(self, keys_file_name):
        with open(keys_file_name, "r") as keys_file:
            keys = json.load(keys_file)
            self.alpaca_api_key = keys["ALPACA_API_KEY"]
            self.alpaca_secret_key = keys["ALPACA_SECRET_KEY"]
            self.headers = {
                "APCA-API-KEY-ID": self.alpaca_api_key,
                "APCA-API-SECRET-KEY": self.alpaca_secret_key
            }

    def get_data(self, symbol, start, end, datatype='bars', logs=True, timeframe='1Min'):
        """
            get_data gets quotes, trades, or bars for a given security and timeframe

            symbol: The stock symbol to query for
            start: Start time, datetime object
            end: End time, datetime object
            datatype: 'bars', 'quotes', or 'trades'
            logs: boolean, states if we want to output some log messages
            timeframe: string, Timeframe for the aggregation. Available values are: 1Min, 1Hour, 1Day.
        """
        # If we are logging, calculate the total seconds we have asked for
        if logs:
            total_seconds = (end-start).total_seconds()
        # Format the url and dataframe columns based on datatype
        if datatype == 'bars':
            url = "https://data.alpaca.markets/v2/stocks/"+symbol+"/bars"
            columns = ["time",'open','high','low','close','volume', "trades", "vwap"]
        elif datatype == 'quotes':
            url = "https://data.alpaca.markets/v2/stocks/"+symbol+"/quotes"
            columns = ["time",'ask_exchange','ask_price','ask_size','bid_exchange','bid_price','bid_size','quote_conditions', "z"]
        elif datatype == 'trades':
            url = "https://data.alpaca.markets/v2/stocks/"+symbol+"/trades"
            columns = ["time",'exchange','price','size','conditions','trade_id','tape']
        else:
            return "Invalid datatype, bars, quotes, trades"
        true_df = pd.DataFrame(columns=columns)
        complete = False
        page = None

        # Progress bar
        pbar = tqdm(total=100)
        last_p_complete = 0
        while not complete:
            # Structure the payload
            payload = {
                "start": start.replace(tzinfo=pytz.UTC).isoformat(),
                "end": end.replace(tzinfo=pytz.UTC).isoformat(),
                "limit": 10000
            }
            
            # If the page token is not none (alpaca had more data for us) set the page to the page token
            if page is not None:
                payload['page_token'] = page
            # If using bars we need to specify a timeframe, this can be changed
            if datatype == 'bars':
                payload['timeframe'] = timeframe
            # Send a data request
            response = requests.get(url, headers=self.headers, params=payload)
            if response.status_code != 200:
                return "Failed to get data, status code %d" % response.status_code
            a_data = response.json()
            a_df = []
            # Get the page token and shove the data into a dataframe.
            page = a_data['next_page_token']
            for item in a_data[datatype]:
                a_df.append(item.values())
            a_df = pd.DataFrame(data=a_df, columns=columns)
            # Because bars are minutely, the last time will be in a minute format and will not have microseconds.
            try:
                if datatype == 'bars':
                    last_trade_time = dt.datetime.strptime(a_df['time'].iloc[-1], "%Y-%m-%dT%H:%M:%SZ")
                else:
                    last_trade_time = dt.datetime.strptime(a_df['time'].iloc[-1], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                print("Unable to get last_trade_time")
                last_trade_time = False
            # Add this particular dataset to the larger datasert
            true_df = true_df.append(a_df, ignore_index=True)
            # If the page is none (alpaca has no more data for us) we are done and can quit
            if page is None:
                complete = True
            # Handle logging of last trade and percentage completed.
            if logs and last_trade_time:
                diff = total_seconds-(end-last_trade_time).total_seconds()
                p_complete = round((diff/total_seconds)*100, 2)
                pbar.update(p_complete - last_p_complete)
                last_p_complete = p_complete
                pbar.set_description(str(last_trade_time))
                # print(last_trade_time, perc_completed)
        true_df.index = pd.to_datetime(true_df["time"])
        true_df.drop("time", inplace=True, axis=1)

        pbar.close()
        return true_df

    # These three are pretty self explanitory
    def get_bars(self, symbol, start, end, log=True, timeframe="1Min"):
        return self.get_data(symbol, start, end, 'bars', log, timeframe=timeframe)

    def get_quotes(self, symbol, start, end, log=True):
        return self.get_data(symbol, start, end, 'quotes', log)

    def get_trades(self, symbol, start, end, log=True):
        return self.get_data(symbol, start, end, 'trades', log)
