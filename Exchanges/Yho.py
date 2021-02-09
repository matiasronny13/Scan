import pandas as pd
import json
from Models.Asset import Asset
import pandas_datareader.data as web
import asyncio
from datetime import datetime, timedelta

class Yho:
    def __init__(self):
        json_key = json.load(open('Exchanges/api.json'))
        self.all_asset_dataframe = None
        pd.options.display.float_format = '{:.8f}'.format

    def convert_to_symbols(self, symbols):
        result = []
        for item in symbols:
            result.append({'symbol': item})
        return result

    def get_all_dataframe(self, param):
        result = []

        allSymbols = self.convert_to_symbols(param['Symbols'])

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]['symbol']
            klineData = klines[1]

            if len(klineData) > 0:
                df = klineData
                df = df.reset_index()
                df['index'] = df.index
                df = df.rename(columns={"High": "high"})
                df = df.rename(columns={"Low": "low"})
                df = df.rename(columns={"Open": "open"})
                df = df.rename(columns={"Close": "close"})
                df = df.rename(columns={"Volume": "vol"})
                df = df.rename(columns={"Date": "date"})

                # formatting column
                df.date = pd.to_datetime(df.date, unit='ms')
                df.open = df.open.astype(float)
                df.high = df.high.astype(float)
                df.low = df.low.astype(float)
                df.close = df.close.astype(float)
                df.vol = df.vol.astype(float)

                df['is_up'] = df.open - df.close <= 0

                if len(df) > 1 and df.iloc[-1].date == df.iloc[-2].date:
                    print('remove duplicate date')
                    df.drop(df.tail(1).index, inplace=True)

                asset = Asset(klineSymbol, df, param['Interval'])
                result.append(asset)

        self.all_asset_dataframe = result
        return result

    async def get_symbol_prices(self, symbol, param):
        print(symbol['symbol'])
        start = datetime.now() - timedelta(param['CountLimit'])
        end = datetime.now()
        #response = web.DataReader(symbol['symbol'], 'yahoo', start, end)
        response = web.get_data_yahoo(symbols=symbol['symbol'], start=start, end=end, pause=0, interval=param['Interval'][1])
        return symbol, response

    async def bound_fetch(self, sem, coro, symbol, param):
        async with sem:
            return await coro(symbol, param)

    async def run(self, coro, all_symbols, param):
        tasks = []
        sem = asyncio.Semaphore(80)

        for symbol in all_symbols:
            task = asyncio.ensure_future(self.bound_fetch(sem, coro, symbol, param))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses

    def loop_all_symbols(self, coro, allSymbols, param):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run(coro, allSymbols, param))
        return loop.run_until_complete(future)
