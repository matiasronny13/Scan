import pandas as pd
import json
from Models.Asset import Asset
from binance import AsyncClient, Client
import asyncio

class Bnb:
    def __init__(self):
        json_key = json.load(open('Exchanges/api.json'))
        self.asyncClient = {}
        self.client = Client(json_key['api_key'], json_key['api_secret'])
        self.quoteAsset = 'BTC'
        self.all_asset_dataframe = None
        pd.options.display.float_format = '{:.8f}'.format

    def get_all_symbols(self):
        info = self.client.get_exchange_info()
        result = []
        for symbol in info['symbols']:
            if symbol['quoteAsset'] == self.quoteAsset and symbol['status'] != 'BREAK':
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

        allKlines = self.loop_all_symbols(self.get_symbol_prices, allSymbols, param)

        for klines in allKlines:
            klineSymbol = klines[0]['symbol']
            klineData = klines[1]

            if len(klineData) > 0:
                df = pd.DataFrame(klineData)
                df.columns = ["date", "open", "high", "low", "close", "vol", "close_ts", "quote_vol",
                              "numb_trades", "buy_base_vol", "buy_quote_vol", "ignore"]
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

                #df.set_index('date', inplace=True)
                asset = Asset(klineSymbol, df, param['Interval'])
                result.append(asset)

        self.all_asset_dataframe = result
        return result

    def get_all_depths(self, param):
        displayed_asset = filter(lambda x: x.is_displayed, self.all_asset_dataframe)
        symbol_to_search = list(a.symbol for a in displayed_asset)

        if len(symbol_to_search) > 0:
            all_depth_response = self.loop_all_symbols(self.get_symbol_depth, symbol_to_search, param)
            all_depth = dict(zip(list(a[0] for a in all_depth_response),     #symbol
                                 list(a[1] for a in all_depth_response)))    #data

        for asset in filter(lambda x: x.is_displayed, self.all_asset_dataframe):
            asset.depth = all_depth[asset.symbol]

    async def get_symbol_depth(self, symbol, param):
        print('depth => ' + symbol)
        client_result = await self.asyncClient.get_order_book(symbol=symbol, limit=1000)
        join_result = client_result['bids'] + client_result['asks']
        depth_df = pd.DataFrame(join_result, columns=['price', 'qty'])
        depth_df.price = depth_df.price.astype(float)
        depth_df.qty = depth_df.qty.astype(float)

        max = depth_df.qty.max()
        min = depth_df.qty.min()
        distance = max - min
        bottom_limit = param['Depth']['BottomThresholdPercentage']
        limit_distance = distance * (int(bottom_limit) / 100)
        threshold = min + limit_distance

        depth = depth_df[depth_df.qty > threshold]

        return (symbol, depth)

    async def get_symbol_prices(self, symbol, param):
        print(symbol['symbol'])
        response = await self.asyncClient.get_klines(symbol=symbol['symbol'], interval=param['Interval'], limit=param['CountLimit'])
        return symbol, response

    async def bound_fetch(self, sem, coro, symbol, param):
        async with sem:
            return await coro(symbol, param)

    async def run(self, coro, all_symbols, param):
        self.asyncClient = await AsyncClient.create()
        tasks = []
        sem = asyncio.Semaphore(80)

        for symbol in all_symbols:
            task = asyncio.ensure_future(self.bound_fetch(sem, coro, symbol, param))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        await self.asyncClient.session.close()
        return responses

    def loop_all_symbols(self, coro, allSymbols, param):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run(coro, allSymbols, param))
        return loop.run_until_complete(future)
