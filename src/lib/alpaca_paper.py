import json
from os import P_OVERLAY
import pytz
import datetime as dt
import requests
from requests.api import head
from requests.models import Response

est = pytz.timezone('US/Eastern')

class AlpacaTrader():
    
    def __init__(self, keys_file_name, is_paper):
        with open(keys_file_name, "r") as keys_file:
            keys = json.load(keys_file)
        
        if is_paper:
            self.alpaca_api_key = keys["ALPACA_PAPER_KEY"]
            self.alpaca_secret_key = keys["ALPACA_PAPER_SECRET_KEY"]
            self.endpoint = keys["PAPER_ENDPOINT"]
        else:
            self.alpaca_api_key = keys["ALPACA_API_KEY"]
            self.alpaca_secret_key = keys["ALPACA_SECRET_KEY"]
            self.endpoint = keys["ENDPOINT"]
        self.headers = {
            "APCA-API-KEY-ID": self.alpaca_api_key,
            "APCA-API-SECRET-KEY": self.alpaca_secret_key
        }


    def get_orders(self, status, symbols, limit=100, after=None, until=None, direction="desc", nested=True):
        if after is None:
            after = dt.datetime.now(tzinfo=est)-dt.timedelta(years=1)
        if until is None:
            until = dt.datetime.now(tzinfo=est)
        payload = {
            "status": status,
            "limit": limit,
            "after": after.replace(tzinfo=pytz.UTC).isoformat(),
            "until": until.replace(tzinfo=pytz.UTC).isoformat(),
            "direction": direction,
            "nested": nested,
            "symbols": symbols,
        }
        return requests.get(self.endpoint+"/v2/orders", headers=self.headers, params=payload)


    def place_market_order(self, symbol, quantity, side, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": quantity,    
            "side": side,
            "type": "market",
            "time_in_force": time_in_force
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, params=payload)


    def place_limit_order(self, symbol, quantity, side, limit_price, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": quantity,    
            "side": side,
            "type": "limit",
            "time_in_force": time_in_force,
            "limit_price": limit_price
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, params=payload)


    def place_trailing_limit_price(self, symbol, quantity, side, trail_price, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": quantity,    
            "side": side,
            "type": "trailing_stop",
            "time_in_force": time_in_force,
            "trail_price": trail_price
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, params=payload)


    def place_trailing_limit_percentage(self, symbol, quantity, side, trailing_percentage, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": quantity,    
            "side": side,
            "type": "trailing_stop",
            "time_in_force": time_in_force,
            "trail_percent": trailing_percentage
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, params=payload)


    def get_order_by_id(self, order_id, nested=True):
        payload = {"nested":nested}
        return requests.get(self.endpoint+"/v2/orders/{order_id}".format(order_id), headers=self.headers, params=payload)


    def replace_order(self, order_id, quantity, time_in_force="day", limit_price=None, stop_price=None, trail=None):
        payload = {"qty": quantity, "time_in_force": time_in_force}
        if limit_price is not None:
            payload["limit_price"] = limit_price
        if stop_price is not None:
            payload["stop_price"] = stop_price
        if trail is not None:
            payload["trail"] = trail
        return requests.patch(self.endpoint+"/v2/orders/{order_id}".format(order_id), headers=self.headers, params=payload)


    def cancel_all_orders(self):
        return requests.delete(self.endpoint+"/v2/orders")


    def cancle_order(self, order_id):
        return requests.delete(self.endpoint+"/v2/orders/{order_id}".format(order_id))

    