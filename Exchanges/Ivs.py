import pandas as pd
import json
from Models.Asset import Asset
import asyncio
from aiohttp import ClientSession
from datetime import datetime, timedelta
import math
from pymongo import MongoClient
import http.client
import json

class Ivs:
    def __init__(self):
        self.all_asset_dataframe = None
        self.client = MongoClient('127.0.0.1', 27017)
        self.db = self.client.SymbolDatabase

    def convert_to_symbols(self, symbols):
        return symbols

    def get_all_symbols(self, query):
        result = list(self.db.Symbols.find(query))
        for r in result:
            r['symbol'] = r['full_name'].replace(":", "_").replace("/", "_") + ' ' + r['ticker']
        return result

    async def coro_scanner(self, session, page, param):
        print("Page: ", page)
        async with session.post(param['url'], headers=param['headers'], data=param['payload'].format(page)) as response:
            response = await response.read()
            if response is not None:
                result = json.loads(response.decode('utf-8'))
                return result

    def get_from_screener(self, param):
        all_hits = []
        page = 1

        conn = http.client.HTTPSConnection("www.investing.com")
        payload = param['Filter'] + "&pn={0}&order[col]=viewData.symbol&order[dir]=a"
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.56',
            'x-requested-with': 'XMLHttpRequest'
        }
        conn.request("POST", "/stock-screener/Service/SearchStocks", payload.format(page), headers)
        res = conn.getresponse()
        data = res.read()
        temp = data.decode("utf-8")

        if temp is not None:
            response = json.loads(temp)
            total = int(response['totalCount'])
            total_page = math.ceil(total / 50)
            print("Total Hits: ", total)
            print("Total Pages: ", total_page)
            coro_result = self.loop_all_symbols(self.coro_scanner, list(range(1, total_page + 1)), {"payload": payload, "headers": headers, "url": "https://www.investing.com/stock-screener/Service/SearchStocks"})

            for h in coro_result:
                if 'hits' in h:
                    all_hits.extend(h['hits'])
                else:
                    print('HITS NOT FOUND')

        result = [{"ticker": str(a["pair_ID"]),
                   "symbol": "{0}_{1} {2}".format(a["exchange_trans"], a["stock_symbol"], str(a["pair_ID"]))} for a in
                  all_hits]

        return result


    def get_all_dataframe(self, param):
        result = []

        if param.__contains__('Symbols') and isinstance(param['Symbols'], list) and len(param['Symbols']) > 0:
            allSymbols = self.convert_to_symbols(param['Symbols'])
        elif param.__contains__('Filter') and param['Filter'] is not None:
            allSymbols = self.get_from_screener(param)
        else:
            allSymbols = self.get_all_symbols(param['Query'])

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]
            klineData = klines[1]

            if klineData is not None and klineData['s'] == 'ok':
                df = pd.DataFrame(klineData)

                if df.isin(['n/a']).values.any():
                    df = df.replace('n/a', 0)

                df.columns = ["date", "close", "open", "high", "low", "vol", "vol_total", "status"]
                df = df.reset_index()
                df['index'] = df.index

                # formatting column
                df.date = pd.to_datetime(df.date, unit='s')
                df.open = df.open.astype(float)
                df.high = df.high.astype(float)
                df.low = df.low.astype(float)
                df.close = df.close.astype(float)
                df.vol = df.vol.astype(float)

                df['is_up'] = df.open - df.close <= 0

                asset = Asset(klineSymbol, df, param['Interval'])
                result.append(asset)

        self.all_asset_dataframe = result
        return result

    def get_all_depths(self, bottom_limit):
        pass

    async def get_symbol_prices(self, session, symbol, param):
        print(symbol)

        end = datetime.now().timestamp()
        delta = timedelta(param['CountLimit'])

        if param['Interval'] == 'W':
            delta = timedelta(weeks=param['CountLimit'])
        elif param['Interval'] == 'M':
            delta = timedelta(weeks=5*param['CountLimit'])

        start = (datetime.now() - delta).timestamp()

        url = "https://tvc4.forexpros.com/41fd7132c82a9acabc36cfb9279ba1a8/1568985768/1/1/8/history?symbol={0}&resolution={1}&from={2}&to={3}".format(symbol['ticker'], param["Interval"], math.ceil(start), math.ceil(end))
        async with session.get(url) as response:
            response = await response.read()
            if response is not None:
                candles = json.loads(response.decode('utf-8'))
                return symbol['symbol'], candles

    async def bound_fetch(self, session, sem, coro, symbol, param):
        async with sem:
            return await coro(session, symbol, param)

    async def run(self, coro, all_symbols, param):
        tasks = []
        sem = asyncio.Semaphore(1000)

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
