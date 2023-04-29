class Utils:
    @staticmethod
    def heikin_ashi(ohlc_df):
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