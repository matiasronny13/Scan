import talib as ta
import pandas as pd
import AppConstants


class IndicatorLoader:
    def __init__(self, param):
        self.param = param
        self.functions = {
            AppConstants.INDICATORS.BBANDS.name: self.load_bbands,
            AppConstants.INDICATORS.MACD.name: self.load_macd,
            AppConstants.INDICATORS.SAR.name: self.load_sar,
            AppConstants.INDICATORS.CCI.name: self.load_cci,
            AppConstants.INDICATORS.OBV.name: self.load_obv,
            AppConstants.INDICATORS.MA.name: self.moving_average,
            AppConstants.INDICATORS.EMA.name: self.exponential_moving_average,
            AppConstants.INDICATORS.FIBONACCI.name: self.fibonacci
        }

    def load_indicators(self, assets):
        indicators = self.param['chart']['indicators']
        for asset in assets:
            for indicator in indicators:
                indicator_output = None
                func = self.functions.get(indicator['id'])
                if func is not None:
                    indicator_output = func(asset.klines, indicator['parameter'])
                asset.indicators.update({indicator['id']: indicator_output})

    def fibonacci(self, klines, parameter):
        fibonacci_result = []
        fib_index = [0, 0.236, 0.382, 0.500, 0.618, 0.786, 1]
        fib_colors = ["blue", "blue", "yellow", "green", "red", "yellow", "blue"]
        is_calculate = False

        fib_interval = parameter['barCount']
        fib_direction = parameter['direction']
        current_bar = klines.iloc[-1]
        bars = klines[-fib_interval:-1]  # exclude the last one
        highest_bar = bars[bars.high == bars.high.max()].iloc[-1]
        lowest_bar = bars[bars.low == bars.low.min()].iloc[-1]
        diff = highest_bar.high - lowest_bar.low

        if fib_direction == "down" and highest_bar.high >= current_bar.low >= lowest_bar.low and highest_bar["index"] > lowest_bar["index"]:
            is_calculate = True
        elif fib_direction == "up" and highest_bar.high >= current_bar.high >= lowest_bar.low and highest_bar["index"] < lowest_bar["index"]:
            fib_index = fib_index[::-1]
            is_calculate = True

        if is_calculate:
            for idx in range(len(fib_index)):
                if fib_direction == "down":
                    fibonacci_result.append({"price": highest_bar.high - fib_index[idx] * diff, "percent": fib_index[idx], "color": fib_colors[idx]})
                elif fib_direction == "up":
                    fibonacci_result.append({"price": lowest_bar.low + fib_index[idx] * diff, "percent": fib_index[idx], "color": fib_colors[idx]})
            return fibonacci_result

    def exponential_moving_average(self, klines, parameter):
        fast = ta.EMA(klines.close, timeperiod=parameter['fast'])
        medium = ta.EMA(klines.close, timeperiod=parameter['medium'])
        long = ta.EMA(klines.close, timeperiod=parameter['long'])
        return pd.DataFrame({'fast': fast, 'medium': medium, 'long': long})

    def moving_average(self, klines, parameter):
        fast = ta.MA(klines.close, timeperiod=parameter['fast'], matype=0)
        medium = ta.MA(klines.close, timeperiod=parameter['medium'], matype=0)
        long = ta.MA(klines.close, timeperiod=parameter['long'], matype=0)
        return pd.DataFrame({'fast': fast, 'medium': medium, 'long': long})

    def load_bbands(self, klines, parameter):
        result_set = ta.BBANDS(klines.close, timeperiod=parameter['timeperiod'], nbdevup=parameter['nbdevup'], nbdevdn=parameter['nbdevdn'])
        return pd.DataFrame({'lower': result_set[2], 'middle': result_set[1], 'upper': result_set[0]})

    def load_cci(self, klines, parameter):
        result_set = ta.CCI(klines.high, klines.low, klines.close, timeperiod=parameter['timeperiod'])
        return pd.DataFrame({'real': result_set})

    def load_macd(self, klines, parameter):
        macd, macdsignal, macdhist = ta.MACD(klines.close, fastperiod=parameter['fastperiod'], slowperiod=parameter['slowperiod'], signalperiod=parameter['signalperiod'])
        return pd.DataFrame({'macd': macd, 'macdsignal': macdsignal, 'macdhist': macdhist})

    def load_sar(self, klines, parameter):
        real = ta.SAR(klines.high, klines.low, acceleration=parameter['acceleration'], maximum=parameter['maximum'])
        return pd.DataFrame({'real': real})

    def load_obv(self, klines, parameter):
        obv = ta.OBV(klines.close, klines.vol)
        return pd.DataFrame({'real': obv})