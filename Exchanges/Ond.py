import pandas as pd
import json
from Models.Asset import Asset
import asyncio
from aiohttp import ClientSession
import requests

class Ond:
    def __init__(self):
        json_key = json.load(open('Exchanges/api_set.json'))
        self.api_key = json_key['ond']['api_key']
        self.account_id = json_key['ond']['account_id']

        self.api_url = "https://api-fxtrade.oanda.com/v3{0}"
        self.request_header = {'Authorization': 'Bearer {0}'.format(self.api_key)}
        self.all_asset_dataframe = None

    def get_all_symbols(self):
        response = requests.get(self.api_url.format('/accounts/{0}/instruments'.format(self.account_id)), headers=self.request_header)
        response = response.json()
        result = []
        if response is not None:
            for ins in response['instruments']:
                result.append({'symbol': ins['name']})
        return result

    def convert_to_symbols(self, symbols):
        result = []
        for item in symbols:
            result.append({'symbol': item})
        return result

    def get_all_dataframe(self, param):
        result = []

        if param.__contains__('Symbols') and isinstance(param['Symbols'], list) and len(param['Symbols']) > 0:
            allSymbols = self.convert_to_symbols(param['Symbols'])
        else:
            allSymbols = self.get_all_symbols()

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]['symbol']
            klineData = klines[1]

            if len(klineData) > 0:
                df = pd.DataFrame([[quote['time'], quote['mid']['o'], quote['mid']['h'], quote['mid']['l'] , quote['mid']['c'], quote['volume']] for quote in klineData])
                df.columns = ["date", "open", "high", "low", "close", "vol"]
                df = df.reset_index()
                df['index'] = df.index

                # formatting column
                df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
                df.open = df.open.astype(float)
                df.high = df.high.astype(float)
                df.low = df.low.astype(float)
                df.close = df.close.astype(float)
                df.vol = df.vol.astype(float)

                df['is_up'] = df.open - df.close <= 0

                # df.set_index('date', inplace=True)
                asset = Asset(klineSymbol, df, param['Interval'])
                result.append(asset)

        self.all_asset_dataframe = result
        return result

    def get_all_depths(self, bottom_limit):
        pass

    async def get_symbol_prices(self, session, symbol, param):
        print(symbol)
        url = self.api_url.format("/instruments/{0}/candles?count={1}&price=M&granularity={2}&smooth=True".format(symbol['symbol'], param["CountLimit"], param['Interval'][1].upper()))
        async with session.get(url, headers=self.request_header) as response:
            response = await response.read()
            if response is not None:
                candles = json.loads(response.decode('utf-8'))['candles']
                return symbol, candles

    async def bound_fetch(self, session, sem, coro, symbol, param):
        async with sem:
            return await coro(session, symbol, param)

    async def run(self, coro, all_symbols, param):
        tasks = []
        sem = asyncio.Semaphore(60)

        async with ClientSession() as session:
            for symbol in all_symbols:
                # pass Semaphore and session to every GET request
                task = asyncio.ensure_future(self.bound_fetch(session, sem, coro, symbol, param))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            return responses

    def loop_all_symbols(self, coro, allSymbols, param):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run(coro, allSymbols, param))
        return loop.run_until_complete(future)
