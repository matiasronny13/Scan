import talib as ta
import pandas as pd
import AppConstants
from stocktrends import Renko
import numpy as nm


class IndicatorLoader:
    def __init__(self, assets):
        self.assets = assets

    def load_indicators(self, indicator_names):
        for asset in self.assets:
            for indicatorName in indicator_names:
                if indicatorName == AppConstants.INDICATORS.BBANDS.name:
                    self.load_bbands(asset)
                elif indicatorName == AppConstants.INDICATORS.MACD.name:
                    self.load_macd(asset)
                elif indicatorName == AppConstants.INDICATORS.SAR.name:
                    self.load_sar(asset)
                elif indicatorName == AppConstants.INDICATORS.EMA.name:
                    self.load_ema(asset)
                elif indicatorName == AppConstants.INDICATORS.DEMA.name:
                    self.load_dema(asset)
                elif indicatorName == AppConstants.INDICATORS.RENKO.name:
                    self.load_renko(asset)
                elif indicatorName == AppConstants.INDICATORS.CCI.name:
                    self.load_cci(asset)
                elif indicatorName == AppConstants.INDICATORS.ANNO_3CROWS.name:
                    self.anno_3crows(asset)
                elif indicatorName == AppConstants.INDICATORS.ANNO_CDLEVENINGSTAR.name:
                    self.anno_cdleveningstar(asset)
                elif indicatorName == AppConstants.INDICATORS.ANNO_CDLABANDONEDBABY.name:
                    self.anno_cdlabandonedbaby(asset)
                elif indicatorName == AppConstants.INDICATORS.OBV.name:
                    self.load_obv(asset)
                elif indicatorName == AppConstants.INDICATORS.SPRS.name:
                    self.support_resistance(asset)
                elif indicatorName == AppConstants.INDICATORS.TRIPLE_MA.name:
                    self.triple_moving_average(asset)

    def get_count(self, param, klines):
        print(param.y)
        return len(klines[(klines.low <= param.y) & (param.y <= klines.high)])

    def triple_moving_average(self, asset):
        ma1 = ta.MA(asset.klines.close, timeperiod=50, matype=0)
        ma2 = ta.MA(asset.klines.close, timeperiod=100, matype=0)
        ma3 = ta.MA(asset.klines.close, timeperiod=200, matype=0)
        df = pd.DataFrame({'ma1': ma1, 'ma2': ma2, 'ma3': ma3})
        asset.indicators.update({AppConstants.INDICATORS.TRIPLE_MA.name: df})

    def support_resistance(self, asset):
        maxima = asset.klines.high.max() * 100
        minima = asset.klines.low.min() * 100

        df = pd.DataFrame(list(nm.arange(minima, maxima)), columns=['y'])
        df.y = df.y * 0.01
        num = df.apply(self.get_count, axis=1, args=[asset.klines])
        df['num'] = num

        distinct = list(set(num))
        distinct.sort()
        top = distinct[-3:]

        asset.indicators.update({AppConstants.INDICATORS.SPRS.name: df[df.num.isin(top)]})

    def anno_3crows(self, asset):
        result_set = ta.CDLIDENTICAL3CROWS(asset.klines.open, asset.klines.high, asset.klines.low, asset.klines.close)
        df = pd.DataFrame({'integer': result_set})
        asset.indicators.update({AppConstants.INDICATORS.ANNO_3CROWS.name: df})

    def anno_cdleveningstar(self, asset):
        result_set = ta.CDLEVENINGSTAR(asset.klines.open, asset.klines.high, asset.klines.low, asset.klines.close, penetration=0)
        df = pd.DataFrame({'integer': result_set})
        asset.indicators.update({AppConstants.INDICATORS.ANNO_CDLEVENINGSTAR.name: df})

    def anno_cdlabandonedbaby(self, asset):
        result_set = ta.CDLABANDONEDBABY(asset.klines.open, asset.klines.high, asset.klines.low, asset.klines.close, penetration=0)
        df = pd.DataFrame({'integer': result_set})
        asset.indicators.update({AppConstants.INDICATORS.ANNO_CDLABANDONEDBABY.name: df})

    def load_renko(self, asset):
        # still need more research
        renko = Renko(asset.klines[['date', 'open', 'high', 'low', 'close', 'vol']].copy())
        renko.brick_size = 0.0005434
        df = renko.get_ohlc_data()
        asset.indicators.update({AppConstants.INDICATORS.RENKO.name: df})

    def load_bbands(self, asset):
        result_set = ta.BBANDS(asset.klines.close, timeperiod=21, nbdevup=2, nbdevdn=2)
        df = pd.DataFrame({'lower': result_set[2], 'middle': result_set[1], 'upper': result_set[0]})
        asset.indicators.update({AppConstants.INDICATORS.BBANDS.name: df})

    def load_cci(self, asset):
        result_set = ta.CCI(asset.klines.high, asset.klines.low, asset.klines.close, timeperiod=20)
        df = pd.DataFrame({'real': result_set})
        asset.indicators.update({AppConstants.INDICATORS.CCI.name: df})

    def load_macd(self, asset):
        macd, macdsignal, macdhist = ta.MACD(asset.klines.close, fastperiod=12, slowperiod=26, signalperiod=9)
        df = pd.DataFrame({'macd': macd, 'macdsignal': macdsignal, 'macdhist': macdhist})
        asset.indicators.update({AppConstants.INDICATORS.MACD.name: df})

    def load_sar(self, asset):
        real = ta.SAR(asset.klines.high, asset.klines.low, acceleration=0.02, maximum=0.2)
        df = pd.DataFrame({'real': real})
        asset.indicators.update({AppConstants.INDICATORS.SAR.name: df})

    def load_ema(self, asset):
        fast = ta.EMA(asset.klines.high, timeperiod=7)
        medium = ta.EMA(asset.klines.high, timeperiod=25)
        long = ta.EMA(asset.klines.high, timeperiod=99)
        df = pd.DataFrame({'fast': fast, 'medium': medium, 'long': long})
        asset.indicators.update({AppConstants.INDICATORS.EMA.name: df})

    def load_obv(self, asset):
        obv = ta.OBV(asset.klines.close, asset.klines.vol)
        df = pd.DataFrame({'real': obv})
        asset.indicators.update({AppConstants.INDICATORS.OBV.name: df})

    def load_dema(self, asset):
        fast = ta.DEMA(asset.klines.high, timeperiod=7)
        medium = ta.DEMA(asset.klines.high, timeperiod=25)
        long = ta.DEMA(asset.klines.high, timeperiod=99)
        df = pd.DataFrame({'fast': fast, 'medium': medium, 'long': long})
        asset.indicators.update({AppConstants.INDICATORS.DEMA.name: df})
