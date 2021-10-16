from config import API_KEY, IEX_KEY_SANDBOX, IEX_KEY
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import threading
import requests
import json
import time


class IEXCloud(object):

    def __init__(self,):

        self.base = 'https://cloud.iexapis.com/stable'
        self._cache = defaultdict(dict)
        self.key = IEX_KEY

    def latest_price(self, symbol):
        if symbol in self._cache and 'last' in self._cache[symbol]:
            return self._cache[symbol]['last']
        req_url = f'{self.base}/stock/{symbol}/quote/latestPrice?token={self.key}'
        p = float(requests.get(req_url).text)
        self._cache[symbol]['last'] = p
        return self._cache[symbol]['last']

    def get_stats(self, symbol):
        bars = self._get_aggregate(symbol)
        o, h, l, c = [], [], [], []
        for b in bars:
            o.append(b['open'])
            h.append(b['high'])
            l.append(b['low'])
            c.append(b['close'])
        return (o, h, l, c), (o[0], max(h), min(l), c[-1])

    def _get_aggregate(self, symbol):
        if symbol in self._cache and 'ibars' in self._cache[symbol]:
            return self._cache[symbol]['ibars']
        req_url = f'{self.base}/stock/{symbol}/intraday-prices?token={self.key}'
        bars = requests.get(req_url).json()
        self._cache[symbol]['ibars'] = bars
        return self._cache[symbol]['ibars']

    def _clear_cache(self, interval=60):
        while True:
            self._cache.clear()
            time.sleep(interval)

    def run(self):
        threading.Thread(target=self._clear_cache).start()


if __name__ == '__main__':
    stocks = IEXCloud()
    stocks.run()
    print(stocks.get_stats('aapl'))
    time.sleep(2)
    print(stocks.latest_price('aapl'))