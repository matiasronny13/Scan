from binance import AsyncClient, Client
import pandas as pd
import json
from Models.Asset import Asset
import requests
import asyncio
from aiohttp import ClientSession

class Iex:
    def __init__(self):
        json_key = json.load(open('Exchanges/api_set.json'))
        self.api_url = "https://cloud.iexapis.com/v1{0}?token=" + json_key['iex']['api_key']
        self.all_asset_dataframe = None
        # pd.options.display.float_format = '{:.0f}'.format

    def get_all_symbols(self):
        response = requests.get(self.api_url.format('/ref-data/iex/symbols'))
        info = [a for a in response.json() if a['isEnabled'] == True]
        result = []
        for symbol in info:
            result.append(symbol)

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

        limit_count = param['CountLimit']

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]['symbol']
            klineData = json.loads(klines[1].decode('utf-8'))

            if klines:
                df = pd.DataFrame(klineData,
                                  columns=['date', 'open', 'close', 'high', 'low', 'volume', 'uOpen', 'uClose', 'uHigh', 'uLow', 'uVolume', 'change', 'changePercent', 'label', 'changeOverTime'])

                df = df.rename(columns={"volume": "vol"})
                df.drop(df[df.date == ''].index, inplace=True)

                df = df.tail(limit_count)
                df = df.reset_index()  # !!! IMPORTANT, otherwise 2nd axes will start from the middle
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

    async def get_symbol_prices(self, session, symbol, param):
        if symbol is not None:
            print(symbol)
            url = self.api_url.format('/stock/' + symbol['symbol'] + '/chart/1h')
            async with session.get(url) as response:
                response = await response.read()
                return symbol, response

    async def bound_fetch(self, session, sem, coro, symbol, param):
        async with sem:
            return await coro(session, symbol, param)

    async def run(self, coro, all_symbols, param):
        tasks = []
        sem = asyncio.Semaphore(600)

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
