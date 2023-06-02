import datetime
import pandas as pd
import AppConstants
from Models.Asset import Asset
import asyncio
from aiohttp import ClientSession
from datetime import datetime, timedelta
import json
import httpx
from Utils import Utils

class Yho:
    def __init__(self, param):
        self.param = param

    # region screener
    def get_total_screener(self):
        response = httpx.post(f"https://query2.finance.yahoo.com/v1/finance/screener/total",
                              params={"crumb": self.param['exchange']["crumb"]},
                              headers={"content-type": "application/json", "cookie": self.param['exchange']["cookie"]},
                              data=json.dumps(self.param['query']["screener"]))

        if response.status_code == 200:
            total = int(response.json()["finance"]["result"][0]["total"])
            print(f"Total screener page: {total}")
            return total
        else:
            print(f"Screener error: {response.json()['finance']['error']['description']}")
            return 0
    async def post_screener(self, session, url, payload):
        async with session.post(url, data=payload) as response:
            response_json = await response.json()
            if response.status == 200:
                print(f'Record count: {response_json["finance"]["result"][0]["count"]}')
                return [q["symbol"] for q in response_json["finance"]["result"][0]["quotes"]]
            else:
                print(f"Screener error: {response_json['finance']['error']['description']}")
                return None
    async def loop_screener_page(self, offsets):
        async with ClientSession(headers={"content-type": "application/json", "cookie": self.param['exchange']["cookie"]}) as session:
            url = f"https://query1.finance.yahoo.com/v1/finance/screener?crumb={self.param['exchange']['crumb']}"
            payload = self.param['query']["screener"]
            payload["size"] = self.param['query']["pageSize"]
            tasks = []

            for offset in offsets:
                payload["offset"] = offset
                task = asyncio.ensure_future(self.post_screener(session, url, json.dumps(payload)))
                tasks.append(task)
            coro_results = await asyncio.gather(*tasks)

            result = []
            if len(coro_results) > 0:
                for x in coro_results:
                    result += x
            return result
    def get_from_screener(self):
        result_count = self.get_total_screener()
        if result_count > 0:
            if result_count > 700:
                if input(f"Screener results in {result_count} records which is more than 700, continue (y/enter)? ") != "y":
                    print("Scan aborted")
                    return []

            page_size = self.param['query']["pageSize"]
            print(f"Fetching {result_count} symbols with page size of {page_size}")
            offsets = range(0, result_count, page_size)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.loop_screener_page(offsets))
    #endregion

    #region historical
    def get_url(self, symbol):
        interval = self.param['query']["interval"]
        interval_url = "1h" if interval == "4h" else interval   #change 4h to 1h as workaround
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval_url}&includePrePost=false"

        interval_6mo = "&range=6mo"
        interval_timestamp = "&period1={0}&period2={1}"

        is_weekend = False if datetime.today().weekday() < 5 else True
        end_timestamp = datetime.now()

        if interval.endswith("m"):
            url = url + interval_6mo
        elif interval == "1h":
            start_timestamp = end_timestamp - timedelta(hours=400 if is_weekend else 300)
        elif interval == "4h":
            start_timestamp = end_timestamp - timedelta(hours=1600 if is_weekend else 1200)
        elif interval == "1d":
            start_timestamp = end_timestamp - timedelta(days=250)
        elif interval == "1wk":
            start_timestamp = end_timestamp - timedelta(weeks=250)
        elif interval == "1mo":
            start_timestamp = end_timestamp - timedelta(weeks=250)

        if start_timestamp is not None:
            url = (url + interval_timestamp).format(int(start_timestamp.timestamp()), int(end_timestamp.timestamp()))

        return url
    async def get_ticks(self, session, url):
        async with session.get(url) as response:
            response_json = await response.json()
            if response.status == 200:
                print(f'get_ticks for {response_json["chart"]["result"][0]["meta"]["symbol"]}')
                return response_json["chart"]["result"][0]
            else:
                print(f"get_ticks error: {response_json['chart']['error']['description']}")
    async def loop_historical_data(self, symbols):
        async with ClientSession(headers={"content-type": "application/json", "cookie": self.param['exchange']["cookie"]}) as session:
            tasks = []
            for symbol in symbols:
                task = asyncio.ensure_future(self.get_ticks(session, self.get_url(symbol)))
                tasks.append(task)
            return await asyncio.gather(*tasks)
    def get_historical_data(self, symbols):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.loop_historical_data(symbols))
    #endregion

    def get_all_dataframe(self):
        result = []
        all_symbols = []

        if 'symbols' in self.param['query'] and len(self.param['query']['symbols']) > 0:
            all_symbols = self.param['query']['symbols']
        elif 'screener' in self.param['query'] and self.param['query']['screener'] is not None:
            all_symbols = self.get_from_screener()

        all_klines = self.get_historical_data(all_symbols)

        for kline in all_klines:
            if kline is None:
                continue

            klineSymbol = kline["meta"]["symbol"]

            ticksDf = pd.DataFrame(kline["timestamp"])
            ohlcDf = pd.DataFrame(kline["indicators"]["quote"][0], columns=["open", "high", "low", "close", "volume"])

            if self.param['chart']['type'] == AppConstants.CHART_TYPE.HEIKIN_ASHI.name:
                ohlcDf = Utils.heikin_ashi(ohlcDf)

            df = ticksDf.join(ohlcDf, lsuffix="_left", rsuffix="_right", how="left")

            df.columns = ["date", "open", "high", "low", "close", "vol"]

            # formatting column
            df.date = pd.to_datetime(df.date, unit='s')
            df.open = df.open.astype(float)
            df.high = df.high.astype(float)
            df.low = df.low.astype(float)
            df.close = df.close.astype(float)
            df.vol = df.vol.astype(float)

            if self.param['query']["interval"] == "4h":
                df = Utils.convert_to_4hours(df)

            df['is_up'] = df.open - df.close <= 0

            df.reset_index(inplace=True)
            df['index'] = df.index

            asset = Asset(klineSymbol, df, self.param['query']['interval'])
            result.append(asset)

        return result