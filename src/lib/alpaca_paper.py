import json
from os import stat
# from os import P_OVERLAY
import pytz
import datetime as dt
import requests
from requests.api import head
from requests.models import Response
from src.lib.alpaca_exceptions import *

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
    
    def get_current_price(self, symbol):
        url = "https://data.alpaca.markets/v2/stocks/{symbol}/snapshot".format(symbol=symbol)
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            handle_errors(response)
        return response
    
    def get_account(self):
        response = requests.get(self.endpoint+"/v2/account", headers=self.headers)
        if response.status_code != 200:
            handle_errors(response)
        return response

    def get_positions(self):
        response = requests.get(self.endpoint+"/v2/positions", headers=self.headers)
        if response.status_code != 200:
            handle_errors(response)
        return response

    def get_cash_amount(self):
        account = self.get_account()
        if account.status_code != 200:
            handle_errors(account)
        return float(account.json()['cash'])

    def calculate_raw_holdings(positions, total_value, cash_amount):
        holdings = {}
        for position in positions:
            market_value = float(position["market_value"])
            total_value += market_value
            holdings[position["symbol"]] = market_value
        holdings["cash"] = cash_amount
        return holdings

    def get_holdings(self, raw=False, total_value=False):
        cash_amount = self.get_cash_amount()
        total_value = cash_amount
        positions = self.get_positions().json()
        holdings = self.calculate_raw_holdings(positions, total_value, cash_amount)
        if not raw:
            for key in holdings.keys():
                holdings[key] = holdings[key]/total_value
            holdings["cash"] = cash_amount/total_value
        return holdings, total_value

    def parse_orders(self, orders):
        orders_dict = {}
        for order in orders:
            symbol = order["symbol"]
            if symbol in orders_dict:
                orders_dict[symbol].append(order)
            else:
                orders_dict[symbol] = [order]
    
    def update_current_holdings(self, current_holdings_raw, desired_holdings, orders_dict, cancel_orders):
        responses = []
        for key in desired_holdings.keys():
            if key in orders_dict:
                if cancel_orders:
                    for order in orders_dict[key]:
                        responses.append(self.cancle_order(order["id"]))
                else:
                    if order["notional"] is not None:
                        current_holdings_raw[key] = float(order["notional"])
                    elif order["qty"] is not None:
                        current_holdings_raw[key] = float(self.get_current_price(key).json()["latestQuote"]["ap"]) * float(order["qty"])

    def handle_order(self, symbol_amount, symbol, responses, verbose):
        share_price = float(self.get_current_price(symbol).json()["latestQuote"]["ap"])
        share_qty = round(symbol_amount/share_price)
        if symbol_amount > 0:
            responses.append(self.place_market_order(symbol, share_qty, "buy", verbose=verbose))
        elif symbol_amount < 0:
            responses.append(self.place_market_order(symbol, abs(share_qty), "sell", verbose=verbose))


    def parse_key(self, key, current_holdings_raw, total_value, desired_value, responses, verbose):
        if key in current_holdings_raw:
            symbol_amount = (total_value*desired_value) - current_holdings_raw[key]
            responses = self.handle_order(symbol_amount, key, responses, verbose)
        else:
            symbol_amount = total_value*desired_value
            responses = self.handle_order(symbol_amount, key, responses, verbose)
        return responses

    def update_holdings(self, desired_holdings, cancel_orders=True, verbose=False):
        current_holdings_raw, total_value = self.get_holdings(raw=True, total_value=True)
        orders = self.get_orders().json()
        orders_dict = self.parse_orders(orders)
        responses, current_holdings_raw = self.update_current_holdings(current_holdings_raw, desired_holdings, orders_dict, cancel_orders)
        for key in desired_holdings.keys():
            responses = self.parse_key(key, current_holdings_raw, total_value, desired_holdings[key], responses, verbose)
        return responses

    def get_oustanding_orders(self, days_look_back=365):
        orders = self.get_orders(status="open", after=dt.datetime.now().astimezone(tz=pytz.timezone("UTC"))-dt.timedelta(days=days_look_back)).json()
        return orders

    def get_closed_orders(self, days_look_back=365):
        orders = self.get_orders(status="closed", after=dt.datetime.now().astimezone(tz=pytz.timezone("UTC"))-dt.timedelta(days=days_look_back)).json()
        return orders

    def get_loggable_orders(self, logged_ids):
        loggable_orders = []
        orders = self.get_closed_orders()
        for order in orders:
            if order["order_id"] not in logged_ids:
                loggable_orders.append(order)
        return loggable_orders

    def place_dollar_order(self, symbol, amount, side, verbose=False):
        if verbose:
            print(side, symbol, amount)
        payload = {
            "symbol": symbol,
            "notional": str(amount),    
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

    def get_orders(self, status="all", symbols=None, limit=100, after=None, until=None, direction="desc", nested=True):
        if after is None:
            after = dt.datetime.now().astimezone(tz=pytz.timezone("UTC"))-dt.timedelta(days=365)
        if until is None:
            until = dt.datetime.now().astimezone(tz=pytz.timezone("UTC"))
        payload = {
            "status": status,
            "limit": limit,
            "after": after.replace(tzinfo=pytz.UTC).isoformat(),
            "until": until.replace(tzinfo=pytz.UTC).isoformat(),
            "direction": direction,
            "nested": nested,
        }
        if symbols is not None:
            payload["symbols"] = symbols
        response = requests.get(self.endpoint+"/v2/orders", headers=self.headers, json=payload)
        if response.status_code != 200:
            handle_errors(response)
        return response

    def place_market_order(self, symbol, quantity, side, time_in_force="day", verbose=False):
        if verbose:
            print(side, symbol, quantity)
        payload = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": side,
            "type": "market",
            "time_in_force": time_in_force
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

    def place_limit_order(self, symbol, quantity, side, limit_price, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": str(quantity),    
            "side": side,
            "type": "limit",
            "time_in_force": time_in_force,
            "limit_price": limit_price
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

    def place_trailing_limit_price(self, symbol, quantity, side, trail_price, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": str(quantity),    
            "side": side,
            "type": "trailing_stop",
            "time_in_force": time_in_force,
            "trail_price": trail_price
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

    def place_trailing_limit_percentage(self, symbol, quantity, side, trailing_percentage, time_in_force="day"):
        payload = {
            "symbol": symbol,
            "qty": str(quantity),    
            "side": side,
            "type": "trailing_stop",
            "time_in_force": time_in_force,
            "trail_percent": trailing_percentage
        }
        return requests.post(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

    def get_order_by_id(self, order_id, nested=True):
        payload = {"nested":nested}
        return requests.get(self.endpoint+"/v2/orders/{order_id}".format(order_id=order_id), headers=self.headers, json=payload)

    def replace_order(self, order_id, quantity, time_in_force="day", limit_price=None, stop_price=None, trail=None):
        payload = {"qty": str(quantity), "time_in_force": time_in_force}
        if limit_price is not None:
            payload["limit_price"] = limit_price
        if stop_price is not None:
            payload["stop_price"] = stop_price
        if trail is not None:
            payload["trail"] = trail
        return requests.patch(self.endpoint+"/v2/orders/{order_id}".format(order_id=order_id), headers=self.headers, json=payload)

    def cancel_all_orders(self):
        return requests.delete(self.endpoint+"/v2/orders", headers=self.headers)

    def cancle_order(self, order_id):
        return requests.delete(self.endpoint+"/v2/orders/{order_id}".format(order_id=order_id), headers=self.headers)

    