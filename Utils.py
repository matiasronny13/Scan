class Utils:
    @staticmethod
    def heikin_ashi(ohlc_df):
        df = ohlc_df.copy()
        df.close = round(((ohlc_df.open + ohlc_df.high + ohlc_df.low + ohlc_df.close) / 4), 2)
        for i in range(len(ohlc_df)):
            if i == 0:
                df.open.iloc[0] = round(((ohlc_df.open.iloc[0] + ohlc_df.close.iloc[0]) / 2), 2)
            else:
                df.open.iat[i] = round(((df.open.iat[i - 1] + df.close.iat[i - 1]) / 2), 2)
        df.high = df.loc[:, ['open', 'close']].join(ohlc_df.high).max(axis=1)
        df.low = df.loc[:, ['open', 'close']].join(ohlc_df.low).min(axis=1)
        return df

    @staticmethod
    def convert_to_4hours(ohlc_df):
        if ohlc_df is not None and len(ohlc_df) > 0:
            df_resampled = ohlc_df.resample("4H", on="date").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "vol": "sum"
            })

            # Drop incomplete intervals at the end of the DataFrame
            df_resampled.dropna(inplace=True)

            return df_resampled