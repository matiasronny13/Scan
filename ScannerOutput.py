import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
from pandas.plotting import register_matplotlib_converters
import numpy as np
from AppConstants import INDICATORS
from datetime import date
from datetime import timedelta
from matplotlib import transforms

class Output:

    def __init__(self, param):
        self.param = param
        register_matplotlib_converters()

    def get_default_config(self, subplots_config):
        for config in subplots_config:
            if config['Axes'] == 'default':
                subplots_config.remove(config)  # remove default from config
                return config

    def draw_renko(self, asset, ax):
        # still need more research
        df = asset.indicators[INDICATORS.RENKO.name]
        ohlc = df[['index', 'open', 'high', 'low', 'close']].copy()
        today = date.today() - timedelta(days=len(ohlc))
        ohlc["date"] = [today - timedelta(days=x) for x in range(0, len(ohlc))]
        ohlc.date = ohlc.date.apply(mdates.date2num)
        candlestick_ohlc(ax, ohlc.values, width=1, colorup='r', colordown='g')

    def draw_candlestick(self, asset, ax):
        ohlc = asset.klines[['index', 'open', 'high', 'low', 'close']].copy()
        candlestick_ohlc(ax, ohlc.values, width=self.bar_width, colorup='g', colordown='r')

    def draw_bbands(self, asset, ax):
        data = asset.indicators[INDICATORS.BBANDS.name]
        ax.plot(asset.klines.index, data.lower, color='b', alpha=.2)
        ax.plot(asset.klines.index, data.middle, color='b', alpha=.2)
        ax.plot(asset.klines.index, data.upper, color='b', alpha=.2)
        ax.fill_between(asset.klines.index, data.lower, data.upper, facecolor='blue', alpha=.05)

    def draw_cci(self, asset, ax):
        data = asset.indicators[INDICATORS.CCI.name]
        ax.plot(asset.klines.index, data.real)

    def draw_obv(self, asset, ax):
        data = asset.indicators[INDICATORS.OBV.name]
        ax.plot(asset.klines.index, data.real)

    def draw_macd(self, asset, ax):
        data = asset.indicators[INDICATORS.MACD.name]
        ax.plot(asset.klines.index, data.macd)
        ax.plot(asset.klines.index, data.macdsignal)

        colormat = np.where(data.macdhist > 0, 'g', 'r')
        ax.bar(asset.klines.index, data.macdhist, width=self.bar_width, alpha=.7, color=colormat)

    def draw_sar(self, asset, ax):
        data = asset.indicators[INDICATORS.SAR.name]
        ax.plot(asset.klines.index, data.real, 'b.', alpha=1, markersize=1)

    def draw_ma(self, asset, ax, indicator_name):
        data = asset.indicators[indicator_name]
        ax.plot(asset.klines.index, data.fast)
        ax.plot(asset.klines.index, data.medium)
        ax.plot(asset.klines.index, data.long)

    def draw_depth(self, asset, ax):
        from matplotlib.ticker import FormatStrFormatter

        ax2 = ax.twiny()
        ax2.invert_xaxis()

        # limit maximum line length to half of the screen
        ax2.set_xlim(asset.depth.qty.max() + asset.depth.qty.max() * 0.5)

        # vertical space
        zoom_distance = (asset.klines.high.max() - asset.klines.low.min()) * self.depth_zoom
        ax2.set_ylim(asset.klines.low.min() - zoom_distance, asset.klines.high.max() + zoom_distance)

        ax2.hlines(y=asset.depth.price, xmin=0, xmax=asset.depth.qty, alpha=.8, color='b')

        # right axes for depth price
        ax3 = ax.twinx()
        ax3.set_yticklabels(asset.depth.price, color='r')
        ax3.set_yticks(asset.depth.price)
        ax3.set_ylim(asset.klines.low.min() - zoom_distance, asset.klines.high.max() + zoom_distance)

        ax3.yaxis.set_major_formatter(FormatStrFormatter('%.8f'))

    def draw_support_resistance(self, asset, ax):
        yaxes = asset.indicators[INDICATORS.SPRS.name]
        ax2 = ax.twiny()
        ax2.invert_xaxis()
        ax2.set_xlim(1)
        ax2.hlines(y=yaxes.y, xmin=0, xmax=1, alpha=0.01, color='b')

    def draw_volume(self, asset, ax):
        data = asset.klines.vol
        ax2 = ax.twinx()

        ax2.set_position(transforms.Bbox([[0.125, 0.1], [0.9, .3]]))
        colormat = np.where(asset.klines.is_up, 'g', 'r')
        ax2.bar(asset.klines.index, data, width=self.bar_width, color=colormat, align='center', alpha=.5)

    def draw_annotation(self, asset, ax, indicator_name):
        series = asset.indicators[indicator_name]
        df = series.loc[series['integer'] != 0]
        for index, data in df.iterrows():
            quote = asset.klines.iloc[index]
            x = index
            y = asset.klines.iloc[index].high
            ax.annotate(str(quote.date),
                    xy=(x, y), xycoords='data',
                    xytext=(x, y + (y * .1)),
                    size=10,
                    bbox=dict(boxstyle="round4,pad=.5", facecolor="yellow"),
                    arrowprops=dict(facecolor='orange', shrink=0.05))

    def draw_ma(self, asset, ax):
        data = asset.indicators[INDICATORS.MA.name]
        if not data.columns.empty:
            for column in data.columns:
                ax.plot(asset.klines.index, data[column])

    def draw_indicators(self, asset, ax, config):
        for indicator_name in config:
            if indicator_name == INDICATORS.CANDLESTICK.name:
                self.draw_candlestick(asset, ax)
            elif indicator_name == INDICATORS.RENKO.name:
                self.draw_renko(asset, ax)
            elif indicator_name == INDICATORS.VOLUME.name:
                self.draw_volume(asset, ax)
            elif indicator_name == INDICATORS.BBANDS.name:
                self.draw_bbands(asset, ax)
            elif indicator_name == INDICATORS.MACD.name:
                self.draw_macd(asset, ax)
            elif indicator_name == INDICATORS.SAR.name:
                self.draw_sar(asset, ax)
            elif indicator_name == INDICATORS.EMA.name or indicator_name == INDICATORS.DEMA.name:
                self.draw_ma(asset, ax, indicator_name)
            elif indicator_name == INDICATORS.DEPTH.name:
                self.draw_depth(asset, ax)
            elif indicator_name == INDICATORS.VOLUME.name:
                self.draw_volume(asset, ax)
            elif indicator_name == INDICATORS.CCI.name:
                self.draw_cci(asset, ax)
            elif indicator_name == INDICATORS.ANNO_3CROWS.name:
                self.draw_annotation(asset, ax, INDICATORS.ANNO_3CROWS.name)
            elif indicator_name == INDICATORS.ANNO_CDLEVENINGSTAR.name:
                self.draw_annotation(asset, ax, INDICATORS.ANNO_CDLEVENINGSTAR.name)
            elif indicator_name == INDICATORS.ANNO_CDLABANDONEDBABY.name:
                self.draw_annotation(asset, ax, INDICATORS.ANNO_CDLABANDONEDBABY.name)
            elif indicator_name == INDICATORS.OBV.name:
                self.draw_obv(asset, ax)
            elif indicator_name == INDICATORS.SPRS.name:
                self.draw_support_resistance(asset, ax)
            elif indicator_name == INDICATORS.MA.name:
                self.draw_ma(asset, ax)


    def draw_axes(self, axes, asset, config):
        try:
            #axes.xaxis_date()
            axes.grid(True)
            axes.margins(.005)

            #axes.set_xticks(asset.klines.index)
            #axes.set_xticklabels(asset.klines.date)
            #axes.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y %H:%M:%S'))

            self.draw_indicators(asset, axes, config['Indicators'])
        except BaseException as ex:
            print("EXCEPTION: Failed to draw indicators for {0}".format(asset.symbol))
            print("Message: {0}".format(ex))

    def generate_output(self, all_asset_data):
        print("Start generating output ....")
        self.depth_zoom = int(self.param['Depth']['Zoom'])
        subplots_config = self.param['Subplots']
        subplots_count = len(subplots_config)

        if subplots_count == 1:
            plot_ratio = [4]
        elif subplots_count == 2:
            plot_ratio = [3, 1]
        elif subplots_count == 3:
            plot_ratio = [2, 1, 1]
        elif subplots_count == 4:
            plot_ratio = [1, 1, 1, 1]

        for asset in all_asset_data:
            if asset.is_displayed:
                #asset.klines["date"] = asset.klines["date"].apply(mdates.date2num)

                self.bar_width = .5
                #self.bar_width = .0003 * ((asset.klines.date[1] - asset.klines.date[0]) / 0.00069444440305233)

                fig, axes = plt.subplots(subplots_count, 1, sharex=True, figsize=(20, 15), gridspec_kw={'height_ratios': plot_ratio })
                fig.suptitle('{0} - {1}'.format(asset.symbol, asset.interval), fontsize=13, y=0.90, c='b')

                plt.autoscale(tight=True)
                #plt.gcf().autofmt_xdate()  # Beautify the x-labels

                if subplots_count > 1:
                    ax_index = 0
                    while True:
                        self.draw_axes(axes[ax_index], asset, subplots_config[ax_index])
                        ax_index += 1
                        if ax_index >= subplots_count:
                            break
                else:
                    self.draw_axes(axes, asset, subplots_config[0])

                fig.tight_layout()
                #plt.show()
                plt.savefig("./Output/{0}_{1}.png".format(asset.interval, asset.symbol))
                plt.close(fig)

