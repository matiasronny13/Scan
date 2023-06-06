from AppConstants import StrategyCode
from AppConstants import INDICATORS


class Scanner:
    def __init__(self, param):
        self.param = param
        self.functions = {
            StrategyCode.ALL_NEGATIVE.name: self.all_negative,
            StrategyCode.FIB_RETRACE.name: self.fibonacci_retracement
        }

    def scan(self, asset_list):
        strategy = self.param['strategy']
        executor = self.functions.get(strategy['name'], lambda a, b: True)

        for asset in asset_list:
            if len(asset.klines) > 5:
                asset.is_displayed = executor(asset, strategy)
                if asset.is_displayed:
                    print(f"Output => {asset.symbol}")

    def macd_hist_negative(self, asset) -> bool:
        macd_df = asset.indicators[INDICATORS.MACD.name]

        idx = -1
        hist = []
        while macd_df.iloc[idx].macdhist <= 0:
            hist.append(macd_df.iloc[idx].macdhist) #stored in reversed order
            idx = idx - 1

        if len(hist) > 4:
            min_index = hist.index(min(hist))
            if 1 < min_index < len(hist) - 2:
                if hist[min_index-2] > hist[min_index] and \
                   hist[min_index-1] > hist[min_index] and \
                   hist[min_index] < hist[min_index+1] and \
                   hist[min_index] < hist[min_index+2]:
                    return True

    def all_negative(self, asset, strategy) -> bool:
        sar = asset.indicators[INDICATORS.SAR.name]
        bb = asset.indicators[INDICATORS.BBANDS.name]

        if self.macd_hist_negative(asset):
            high = asset.klines.iloc[-1].high
            if high < bb.iloc[-1].middle and high < sar.iloc[-1].real:
                return True

    def fibonacci_retracement(self, asset, strategy) -> bool:
        fibonacci = asset.indicators[INDICATORS.FIBONACCI.name]
        if fibonacci is None:
            return False

        last_bar = asset.klines.iloc[-1]
        target_level = strategy["fibonacciLevel"]
        fib_direction = "down" if fibonacci[0]['percent'] < fibonacci[-1]['percent'] else "up"

        if fib_direction == "down" and fibonacci[target_level - 1]["price"] >= last_bar.low >= fibonacci[target_level]["price"]:
            return True
        elif fib_direction == "up" and fibonacci[target_level - 1]["price"] >= last_bar.high >= fibonacci[target_level]["price"]:
            return True

