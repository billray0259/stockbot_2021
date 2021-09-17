import json
# from os import P_OVERLAY
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
    
    def get_current_price(self, symbol):
        url = "https://data.alpaca.markets/v2/stocks/{symbol}/snapshot".format(symbol=symbol)
        print(url)
        return requests.get(url, headers=self.headers)
    
    def get_account(self):
        return requests.get(self.endpoint+"/v2/account", headers=self.headers)

    def get_positions(self):
        return requests.get(self.endpoint+"/v2/positions", headers=self.headers)

    def get_holdings(self, raw=False, total_value=False):
        cash_amount = float(self.get_account().json()['cash'])
        total_value = cash_amount
        positions = self.get_positions().json()
        holdings = {}
        for position in positions:
            market_value = float(position["market_value"])
            total_value += market_value
            holdings[position["symbol"]] = market_value
        holdings["cash"] = cash_amount
        if not raw:
            for key in holdings.keys():
                holdings[key] = holdings[key]/total_value
            holdings["cash"] = cash_amount/total_value
        return holdings, total_value

    def update_holdings(self, dersired_holdings, cancel_orders=True, verbose=False):
        current_holdings_raw, total_value = self.get_holdings(raw=True, total_value=True)
        responses = []
        orders = self.get_orders().json()
        orders_dict = {}
        for order in orders:
            symbol = order["symbol"]
            if symbol in orders_dict:
                orders_dict[symbol].append(order)
            else:
                orders_dict[symbol] = [order]
        for key in dersired_holdings.keys():
            if key in orders_dict:
                if cancel_orders:
                    for order in orders_dict[key]:
                        responses.append(self.cancle_order(order["id"]))
                else:
                    if order["notional"] is not None:
                        current_holdings_raw[key] = float(order["notional"])
                    elif order["qty"] is not None:
                        current_holdings_raw[key] = float(self.get_current_price(key).json()["latestQuote"]["ap"]) * float(order["qty"])
            if key in current_holdings_raw:
                symbol_amount = (total_value*dersired_holdings[key]) - current_holdings_raw[key]
                share_price = float(self.get_current_price(key).json()["latestQuote"]["ap"])
                share_qty = round(symbol_amount/share_price)
                if symbol_amount > 0:
                    responses.append(self.place_market_order(key, share_qty, "buy", verbose=verbose))
                elif symbol_amount < 0:
                    responses.append(self.place_market_order(key, abs(share_qty), "sell", verbose=verbose))
            else:
                symbol_amount = total_value*dersired_holdings[key]
                share_price = float(self.get_current_price(key).json()["latestQuote"]["ap"])
                share_qty = round(symbol_amount/share_price)
                if symbol_amount > 0:
                    responses.append(self.place_market_order(key, share_qty, "buy", verbose=verbose))
                elif symbol_amount < 0:
                    responses.append(self.place_market_order(key, abs(share_qty), "sell", verbose=verbose))
        return responses

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
        # if after is None:
        #     after = dt.datetime.now(tzinfo=est)-dt.timedelta(years=1)
        # if until is None:
        #     until = dt.datetime.now(tzinfo=est)
        payload = {
            "status": status,
            "limit": limit,
            # "after": after.replace(tzinfo=pytz.UTC).isoformat(),
            # "until": until.replace(tzinfo=pytz.UTC).isoformat(),
            "direction": direction,
            "nested": nested,
        }
        if symbols is not None:
            payload["symbols"] = symbols
        return requests.get(self.endpoint+"/v2/orders", headers=self.headers, json=payload)

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

    