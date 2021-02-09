import pandas as pd
import json
from Models.Asset import Asset
import requests
import asyncio
from aiohttp import ClientSession


class Idx:
    def __init__(self):
        self.all_symbols = json.load(open('Exchanges/idx_symbols.json'))
        self.all_asset_dataframe = None
        #pd.options.display.float_format = '{:.0f}'.format

    def get_all_dataframe(self, param):
        result = []

        if param.__contains__('Symbols') and isinstance(param['Symbols'], list) and len(param['Symbols']) > 0:
            allSymbols = param['Symbols']
        else:
            allSymbols = self.all_symbols['symbols']

        limit_count = param['CountLimit']

        interval_map = {
            '1d': 'I',
            '1w': 'J',
            '1m': 'M'
        }
        param['Interval'] = interval_map[param['Interval']]

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        allKlines_json = []
        for data in allKlines:
            allKlines_json.append(json.loads(data.decode('utf-8')))

        for klines in allKlines_json:
            if klines:
                result_set = klines['B'].split('&')
                df = pd.DataFrame([sub.split("|") for sub in result_set],
                                  columns=["date", "empty1", "open", "high", "low", "close",
                                           "dummy1", "dummy2", "zero", "vol", "ignore", "empty2"])

                df.drop(df[df.date == ''].index, inplace=True)

                if param['Interval'] == 'M':
                    df.date = ["{0}01".format(d[:-2]) for d in df.date]

                df = df.tail(limit_count)
                df = df.reset_index()           # !!! IMPORTANT, otherwise 2nd axes will start from the middle
                df['index'] = df.index

                # formatting column
                df.date = pd.to_datetime(df.date, format='%Y%m%d')
                df.open = df.open.astype(float)
                df.high = df.high.astype(float)
                df.low = df.low.astype(float)
                df.close = df.close.astype(float)
                df.vol = df.vol.astype(float)

                df['is_up'] = df.open - df.close <= 0

                #df.set_index('date', inplace=True)
                asset = Asset(klines['A'].replace('1', ''), df, param['Interval'])
                result.append(asset)

        self.all_asset_dataframe = result
        return result

    def get_all_depths(self, bottom_limit):
        pass

    async def get_symbol_prices(self, session, symbol, param):
        print(symbol)
        url = "https://www.miraeasset.co.id/tr/cpstChartAjaxTR.do?StockCode={0}&periodBit={1}".format(symbol, param['Interval'])
        async with session.get(url) as response:
            return await response.read()

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
