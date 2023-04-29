from AppConstants import StrategyCode
from AppConstants import INDICATORS
import math

class Scanner:
    def __init__(self, param):
        self.param = param

    @staticmethod
    def is_bullish_candle(tick):
        return tick.close > tick.open

    def bb_reversal(self, asset, strategy):
        df = asset.indicators[INDICATORS.BBANDS.name]
        tick_count = 0 - int(strategy["TickCount"])
        if len(df) > 5 \
                and asset.klines.iloc[tick_count].low <= df.iloc[tick_count].lower \
                and self.is_bullish_candle(asset.klines.iloc[-1]) \
                and asset.klines.iloc[-1].low > df.iloc[-1].lower \
                and asset.klines.iloc[tick_count].low < asset.klines.iloc[-1].low:
            print("== " + asset.symbol)
            #return True
            return self.obv_up(asset)
        else:
            return False

    def bb_break(self, asset, strategy):
        last_id = -1
        beginning_id = -4
        distance_percentage = 0.03

        df = asset.indicators[INDICATORS.BBANDS.name]

        result = False
        for i in range(last_id, (last_id + beginning_id), -1):
            if asset.klines.iloc[i].low < df.iloc[i-1].lower:
                result = True
            else:
                result = False
                break

        if result == True:
            print("== " + asset.symbol)
            return self.obv_up(asset)
        else:
            return False

    def sar_reversal(self, asset, strategy):
        df = asset.indicators[INDICATORS.SAR.name]
        if len(df) > 5 \
                and asset.klines.iloc[-2].high <= df.iloc[-2].real \
                and asset.klines.iloc[-1].low > df.iloc[-1].real:
            print("== " + asset.symbol)
            return True
        else:
            return False


    def sar_rev_bear(self, asset, strategy):
        df = asset.indicators[INDICATORS.SAR.name]
        if len(df) > 5 \
                and asset.klines.iloc[-1].high <= df.iloc[-1].real \
                and asset.klines.iloc[-2].low > df.iloc[-2].real:
            print("== " + asset.symbol)
            return True
        else:
            return False

    def cci_reversal(self, asset, strategy):
        cci = asset.indicators[INDICATORS.CCI.name]
        if len(cci) > 5 \
                and cci.iloc[-2].real < cci.iloc[-1].real < -1:
            print("== " + asset.symbol)
            return True
        else:
            return False

    def obv_up(self, asset):
        obv = asset.indicators[INDICATORS.OBV.name]
        if obv.iloc[-1].real > obv.iloc[0].real:
            print("== " + asset.symbol)
            return True
        else:
            return False

    def scan_pattern(self, asset, strategy):
        series = asset.indicators[strategy['Name']]
        tick = int(strategy['TickCount'])
        occur = series.loc[series['integer'] != 0]

        if len(occur) > 0 and series.tail(1).index[0] - occur.tail(1).index[0] <= tick:
            print("== " + asset.symbol)
            return True
        else:
            return False

    def sar_break(self, asset, strategy):
        sar = asset.indicators[INDICATORS.SAR.name]
        bb = asset.indicators[INDICATORS.BBANDS.name]

        if asset.klines.iloc[-1].high <= sar.iloc[-1].real \
                and not math.isnan(bb.iloc[-1].middle) \
                and asset.klines.iloc[-1].is_up \
                and sar.iloc[-1].real < bb.iloc[-1].middle \
                and asset.klines.iloc[-2].high <= asset.klines.iloc[-1].high:
            print("== " + asset.symbol)
            return self.obv_up(asset)
        else:
            return False

    def macd_negative(self, asset):
        macd_df = asset.indicators[INDICATORS.MACD.name]

        idx = -1
        hist = []
        while macd_df.iloc[idx].macdhist <= 0:
            hist.append(macd_df.iloc[idx].macdhist)
            idx = idx - 1

        if len(hist) > 4:
            idx = -1
            bottom = []
            while idx - 2 >= -len(hist):
                if macd_df.iloc[idx].macdhist > macd_df.iloc[idx - 1].macdhist < macd_df.iloc[idx - 2].macdhist:
                    bottom.append(idx - 1)
                idx = idx - 1

            return len(bottom) > 2
        else:
            return False

    def macd_rev(self, asset, strategy):
        macd_df = asset.indicators[INDICATORS.MACD.name]
        if self.macd_negative(asset):
            if (macd_df.iloc[-2].macdsignal - macd_df.iloc[-2].macd) > (macd_df.iloc[-1].macdsignal - macd_df.iloc[-1].macd):
                print("== " + asset.symbol)
                # return True
                return self.obv_up(asset)
            else:
                return False
        else:
            return False

    def macd_cross(self, asset, strategy):
        macd_df = asset.indicators[INDICATORS.MACD.name]
        if len(macd_df) > 5 and macd_df.iloc[-3].macdhist < macd_df.iloc[-2].macdhist < macd_df.iloc[-1].macdhist < 0:
            distance = macd_df.iloc[-2].macdhist - macd_df.iloc[-1].macdhist
            if (macd_df.iloc[-1].macdhist - distance) >= 0:
                print("== " + asset.symbol)
                #return True
                return self.obv_up(asset)
            else:
                return False
        else:
            return False

    def gap(self, asset, strategy):
        distance = ((asset.klines.iloc[-1].open - asset.klines.iloc[-2].close) / asset.klines.iloc[-2].close) * 100
        if distance > 5:
            print("== " + asset.symbol)
            return True
        else:
            return False

    def all_negative(self, asset, strategy):
        sar = asset.indicators[INDICATORS.SAR.name]
        bb = asset.indicators[INDICATORS.BBANDS.name]
        if self.macd_negative(asset):
            high = asset.klines.iloc[-1].high
            if high < bb.iloc[-1].middle and high < sar.iloc[-1].real:
                return True
        return False

    def scan(self, asset_list):
        strategy = self.param['Strategy']
        for asset in asset_list:
            if len(asset.klines) > 5:
                if strategy["Name"] == StrategyCode.BB_REV.name:
                    asset.is_displayed = self.bb_reversal(asset, strategy)
                elif strategy["Name"] == StrategyCode.MACD_CROSS.name:
                    asset.is_displayed = self.macd_cross(asset, strategy)
                elif strategy["Name"] == StrategyCode.MACD_REV.name:
                    asset.is_displayed = self.macd_rev(asset, strategy)
                elif strategy["Name"] == StrategyCode.SAR_REV.name:
                    asset.is_displayed = self.sar_reversal(asset, strategy)
                elif strategy["Name"] == StrategyCode.CCI_REV.name:
                    asset.is_displayed = self.cci_reversal(asset, strategy)
                elif strategy["Name"] == StrategyCode.ANNO_3CROWS.name:
                    asset.is_displayed = self.scan_pattern(asset, strategy)
                elif strategy["Name"] == StrategyCode.ANNO_CDLEVENINGSTAR.name:
                    asset.is_displayed = self.scan_pattern(asset, strategy)
                elif strategy["Name"] == StrategyCode.ANNO_CDLABANDONEDBABY.name:
                    asset.is_displayed = self.scan_pattern(asset, strategy)
                elif strategy["Name"] == StrategyCode.OBV_UP.name:
                    asset.is_displayed = self.obv_up(asset, strategy)
                elif strategy["Name"] == StrategyCode.SAR_BREAK.name:
                    asset.is_displayed = self.sar_break(asset, strategy)
                elif strategy["Name"] == StrategyCode.BB_BREAK.name:
                    asset.is_displayed = self.bb_break(asset, strategy)
                elif strategy["Name"] == StrategyCode.SAR_REV_BEAR.name:
                    asset.is_displayed = self.sar_rev_bear(asset, strategy)
                elif strategy["Name"] == StrategyCode.GAP.name:
                    asset.is_displayed = self.gap(asset, strategy)
                elif strategy["Name"] == StrategyCode.ALL_NEGATIVE.name:
                    asset.is_displayed = self.all_negative(asset, strategy)
                else:
                    asset.is_displayed = True


