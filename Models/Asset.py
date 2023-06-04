class Asset:

    def __init__(self, symbol, klines, interval):
        self.symbol = symbol
        self.klines = klines
        self.interval = interval
        self.indicators = {}
        self.is_displayed = False
        



