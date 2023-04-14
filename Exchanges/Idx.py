import pandas as pd
from Models.Asset import Asset
import asyncio
from aiohttp import ClientSession
import math
import http.client
import json
import datetime

class Idx:
    def __init__(self):
        self.all_asset_dataframe = None

    def convert_to_symbols(self, symbols):
        return symbols

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

        result = [a["viewData"]["symbol"] for a in all_hits]

        return result

    def cleanup_fund_symbol(self, input):
        return input.split("_")[0]

    def get_all_dataframe(self, param):
        result = []

        if param.__contains__('Symbols') and isinstance(param['Symbols'], list) and len(param['Symbols']) > 0:
            allSymbols = self.convert_to_symbols(param['Symbols'])
        elif param.__contains__('Filter') and param['Filter'] is not None:
            allSymbols = self.get_from_screener(param)

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]
            response = klines[1]

            if (response is not None):
                if(response['s'] != 'ok'):
                    print("Error with response for " + klineSymbol)
                else:
                    response.pop('s')
                    df = pd.DataFrame(response)

                    #remove row where all columns are null
                    df = df[df.o.notna() & df.h.notna() & df.l.notna() & df.c.notna() & df.v.notna()]

                    if df.isnull().values.any():
                        df = df.fillna(0)

                    df.columns = ["date", "close", "open", "high", "low", "vol"]
                    df = df.reset_index()
                    df['index'] = df.index

                    # formatting column
                    df.date = pd.to_datetime(df.date, unit='ms')
                    df.open = df.open.astype(float)
                    df.high = df.high.astype(float)
                    df.low = df.low.astype(float)
                    df.close = df.close.astype(float)
                    df.vol = df.vol.astype(float)

                    df['is_up'] = df.open - df.close <= 0

                    asset = Asset(klineSymbol, df, param['Resolution'])
                    result.append(asset)

        self.all_asset_dataframe = result
        return result

    def get_all_depths(self, bottom_limit):
        pass

    def get_key(self, input, param):
        result = "STOCK"
        result += "/" + param["CountryMapping"][input["country"]]
        result += "/" + param["ExchangeMapping"][input["exchange"]]
        result += "/" + input["symbol"]
        return result

    async def get_symbol_prices(self, session, symbol, param):
        print(symbol)

        start_date = int(datetime.datetime.strptime(param["StartDate"], '%d%m%Y').timestamp())
        to_date = int(datetime.datetime.now().timestamp())
        url = (f"https://chart-cloud.poems.co.id/iface/history?symbol={symbol}&resolution={param['Resolution']}&from={start_date}&to={to_date}")
        async with session.get(url) as response:
            response = await response.read()
            if response is not None:
                candles = json.loads(response.decode('utf-8'))
                return symbol, candles

    async def bound_fetch(self, session, sem, coro, symbol, param):
        async with sem:
            return await coro(session, symbol, param)

    async def run(self, coro, all_symbols, param):
        tasks = []
        sem = asyncio.Semaphore(1000)

        headers = {
            'Cookie': '_gcl_au=1.1.726795822.1681469770; _ga=GA1.3.290348481.1681469771; _gid=GA1.3.169319800.1681469771; _fbp=fb.2.1681469770981.1187568877; __zlcmid=1FNlkJx6uljViw4; POEMSChartCookie=s%3AVQiMsvJ5ocgSi4QrKBO003idzLIaFTaT.dEgz%2FyApNiRQraHpVf5hEA142OvKa2JC%2FXMrypImSAo'
        }
        async with ClientSession(headers=headers) as session:
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
