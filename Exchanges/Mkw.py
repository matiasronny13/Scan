import pandas as pd
import AppConstants
from Models.Asset import Asset
import asyncio
from aiohttp import ClientSession
import math
import http.client
import json

class Mkw:
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

        result = [{
                       "exchange": a["exchange_trans"],
                       "country": a["viewData"]["flag"],
                       "symbol": a["viewData"]["symbol"] if "_" not in a["viewData"]["symbol"] else self.cleanup_fund_symbol(a["viewData"]["symbol"])
                   } for a in
                  all_hits]

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
                if("error" in response):
                    print("ERROR: " + response["error"])
                else:
                    if (response["TimeInfo"]["Ticks"] is not None and response["Series"][0]["DataPoints"][0] != [None, None, None, None]):
                        ticksDf = pd.DataFrame(response["TimeInfo"]["Ticks"], columns=['tick'])
                        ohlcDf = pd.DataFrame(response["Series"][0]["DataPoints"], columns=["open", "high", "low", "close"])
                        if param["ChartType"] == AppConstants.CHART_TYPE.HEIKIN_ASHI.name:
                            ohlcDf = self.heikin_ashi(ohlcDf)
                        volDf = pd.DataFrame(response["Series"][1]["DataPoints"], columns=["vol"])

                        firstJoinDf = ticksDf.join(ohlcDf, lsuffix="_left", rsuffix="_right", how="left")
                        df = firstJoinDf.join(volDf, lsuffix="_left", rsuffix="_right", how="left")

                        #remove row where all columns are null
                        df = df[df.open.notna() & df.high.notna() & df.low.notna() & df.close.notna() & df.vol.notna()]

                        if df.isnull().values.any():
                            df = df.fillna(0)

                        df.columns = ["date", "open", "high", "low", "close", "vol"]
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

                        asset = Asset(klineSymbol, df, param['Step'])
                        result.append(asset)

        self.all_asset_dataframe = result
        return result

    def heikin_ashi(self, ohlc_df) -> pd.DataFrame:
        df = ohlc_df.copy()
        df['close'] = round(((ohlc_df['open'] + ohlc_df['high'] + ohlc_df['low'] + ohlc_df['close']) / 4), 2)
        for i in range(len(ohlc_df)):
            if i == 0:
                df.iloc[0, 0] = round(((ohlc_df['open'].iloc[0] + ohlc_df['close'].iloc[0]) / 2), 2)
            else:
                df.iat[i, 0] = round(((df.iat[i - 1, 0] + df.iat[i - 1, 3]) / 2), 2)
        df['high'] = df.loc[:, ['open', 'close']].join(ohlc_df['high']).max(axis=1)
        df['low'] = df.loc[:, ['open', 'close']].join(ohlc_df['low']).min(axis=1)
        return df

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

        url = ("https://api-secure.wsj.net/api/michelangelo/timeseries/history?ckey=cecc4267a0")
        payload = {
                    "Step": param['Step'],
                    "TimeFrame": param['TimeFrame'],
                    "IncludeMockTick": "true",
                    "FilterNullSlots": "false",
                    "FilterClosedPoints": "true",
                    "IncludeClosedSlots": "false",
                    "IncludeOfficialClose": "true",
                    "InjectOpen": "false",
                    "ShowPreMarket": "false",
                    "ShowAfterHours": "false",
                    "UseExtendedTimeFrame": "true",
                    "WantPriorClose": "false",
                    "IncludeCurrentQuotes": "false",
                    "ResetTodaysAfterHoursPercentChange": "false",
                    "Series": [{
                            "Key": self.get_key(symbol, param),
                            "Dialect": "Charting",
                            "Kind": "Ticker",
                            "SeriesId": "s1",
                            "DataTypes": ["Open", "High", "Low", "Last"],
                            "Indicators": [{
                                    "Parameters": [],
                                    "Kind": "Volume",
                                    "SeriesId": "vol"
                                }
                            ]
                        }
                    ]
                }

        async with session.post(url, data=json.dumps(payload)) as response:
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

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Dylan2010.EntitlementToken': 'cecc4267a0194af89ca343805a3e57af'
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
