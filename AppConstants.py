from enum import Enum

class Exhange(Enum):
    BNB = 0,
    IDX = 1

class StrategyCode(Enum):
    NONE = 0,
    BB_REV = 1,
    MACD_CROSS = 2,
    SAR_REV = 3,
    CCI_REV = 4,
    ANNO_3CROWS = 5
    ANNO_CDLEVENINGSTAR = 6,
    ANNO_CDLABANDONEDBABY = 7,
    MACD_REV = 8,
    OBV_UP = 9,
    SAR_BREAK = 10,
    BB_BREAK = 11,
    SAR_REV_BEAR = 12,
    GAP = 13,
    ALL_NEGATIVE = 14


class INDICATORS(Enum):
    CANDLESTICK = 1,
    VOLUME = 2,
    MACD = 3,
    BBANDS = 4,
    SAR = 5,
    EMA = 6,
    DEMA = 7,
    RENKO = 8,
    DEPTH = 9,
    CCI = 10,
    ANNO_3CROWS = 11,
    ANNO_CDLEVENINGSTAR = 12,
    ANNO_CDLABANDONEDBABY = 13,
    OBV = 14,
    SPRS = 15,
    MA = 16


class CHART_TYPE(Enum):
    OHLC = 0,
    HEIKIN_ASHI = 1


