import pandas as pd
import json
from Models.Asset import Asset
import requests
import asyncio
from aiohttp import ClientSession
import time
import numpy

class Tda:
    def __init__(self):
        json_key = json.load(open('Exchanges/api_set.json'))
        self.api_key = json_key['tda']['api_key']
        self.refresh_token = json_key['tda']['refresh_token']
        oauth_token = self.get_auth_token(self.api_key, self.refresh_token)

        self.api_url = "https://api.tdameritrade.com/v1/{0}?apikey=" + self.api_key + "{1}"
        self.request_header = {'Authorization': 'Bearer {0}'.format(oauth_token)}
        self.all_asset_dataframe = None

    def get_auth_token(self, api_key, refresh_token):
        token_url = 'https://api.tdameritrade.com/v1/oauth2/token'
        response = requests.post(token_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri': 'http://localhost',
            'client_id': api_key
        })
        return response.json()['access_token']


    def get_all_symbols(self):
        response = requests.get(self.api_url.format('instruments', '&symbol=F.*&projection=symbol-regex'))
        if response is not None:
            result = []
            response_json = response.json()
            for symbol in response_json:
                instrument = response_json[symbol]
                if instrument['exchange'] == 'NASDAQ' and instrument['description'].find('Warrant') == -1 and (instrument['assetType'] == 'EQUITY' or instrument['assetType'] == 'FOREX'):
                    result.append(response_json[symbol])
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
                df = pd.DataFrame(klineData)
                #df.columns = ['open', 'high', 'low', 'close', 'volume', 'datetime']

                df = df.rename(columns={"volume": "vol"})
                df = df.rename(columns={"datetime": "date"})

                #f = df.tail(limit_count)
                df = df.reset_index()  # !!! IMPORTANT, otherwise 2nd axes will start from the middle
                df['index'] = df.index

                # formatting column
                df.date = pd.to_datetime(df.date, unit='ms')
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

            freq = {
                "d": "daily",
                "w": "weekly",
                "m": "monthly"
            }

            frequencyType = freq[param["Interval"][1]]
            frequency = param["Interval"][0]

            prd = {
                "d": "day",
                "m": "month",
                "y": "year"
            }

            periodType = prd[param["CountLimit"][1]]
            period = param["CountLimit"][0]

            url = self.api_url.format('marketdata/{0}/pricehistory'.format(symbol['symbol']),
                                      '&periodType={0}&'
                                      'period={1}&'
                                      'frequencyType={2}&'
                                      'frequency={3}&'
                                      'needExtendedHoursData=true'.format(periodType, period, frequencyType, frequency))
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
        sem = asyncio.Semaphore(400)

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