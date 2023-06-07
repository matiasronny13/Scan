import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from pandas.plotting import register_matplotlib_converters
import numpy as np
from AppConstants import INDICATORS
from datetime import datetime
import os
from numpy import ndarray


class Output:
    def __init__(self, param):
        self.param = param
        self.functions = {
            INDICATORS.VOLUME.name: self.draw_volume,
            INDICATORS.BBANDS.name: self.draw_bbands,
            INDICATORS.MACD.name: self.draw_macd,
            INDICATORS.SAR.name: self.draw_sar,
            INDICATORS.CCI.name: self.draw_cci,
            INDICATORS.OBV.name: self.draw_obv,
            INDICATORS.FIBONACCI.name: self.draw_fibonacci,
            INDICATORS.EMA.name: self.draw_ma,
            INDICATORS.MA.name: self.draw_ma
        }
        register_matplotlib_converters()

    def generate_output(self, all_asset_data):
        if len(all_asset_data) == 0:
            return

        print("Start generating output ....")
        indicator_configs = self.param['chart']['indicators']
        subplots_count = len(set([a['axes'] for a in indicator_configs if a['axes'] > -1]))

        if subplots_count == 1:
            plot_ratio = [4]
        elif subplots_count == 2:
            plot_ratio = [3, 1]
        elif subplots_count == 3:
            plot_ratio = [2, 1, 1]
        elif subplots_count == 4:
            plot_ratio = [1, 1, 1, 1]

        subdir = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{all_asset_data[0].interval}'
        os.mkdir("./Output/" + subdir)

        for asset in all_asset_data:
            if asset.is_displayed:
                #asset.klines["date"] = asset.klines["date"].apply(mdates.date2num)

                self.bar_width = .5
                #self.bar_width = .0003 * ((asset.klines.date[1] - asset.klines.date[0]) / 0.00069444440305233)

                fig, axes = plt.subplots(subplots_count, 1, sharex=True, figsize=(20, 15), gridspec_kw={'height_ratios': plot_ratio })
                axes_list = axes if isinstance(axes, ndarray) else [axes]   #if just single object then wrap it in array
                fig.suptitle('{0} - {1}'.format(asset.symbol, asset.interval), fontsize=13, y=0.90, c='b')

                plt.autoscale(tight=True)
                #plt.gcf().autofmt_xdate()  # Beautify the x-labels

                #configure individual axes
                for ax in axes_list:
                    self.configure_axes(ax)

                self.draw_ohlc(axes_list[0], asset.klines)
                for indicator_config in indicator_configs:
                    try:
                        indicator_axes = indicator_config['axes']
                        if indicator_axes > -1:
                            indicator_id = indicator_config['id']
                            executor = self.functions.get(indicator_id)
                            if executor is not None:
                                executor(axes_list[indicator_axes], asset.klines, asset.indicators[indicator_id])
                    except BaseException as ex:
                        print(f"EXCEPTION: Failed to draw indicators for {asset.symbol}")
                        print(f"Message: {ex}")

                fig.tight_layout()
                #plt.show()
                plt.savefig("./Output/{0}/{1}_{2}.png".format(subdir, asset.interval, asset.symbol.replace("*", "^")))
                plt.close(fig)

    def configure_axes(self, axes):
        #axes.xaxis_date()
        axes.grid(True)
        axes.margins(.005)

        #axes.set_xticks(klines.index)
        #axes.set_xticklabels(asset.klines.date)
        #axes.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y %H:%M:%S'))

    def draw_ohlc(self, ax, klines):
        ohlc = klines[['index', 'open', 'high', 'low', 'close']].copy()
        candlestick_ohlc(ax, ohlc.values, width=self.bar_width, colorup='g', colordown='r')

    def draw_bbands(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.lower, color='b', alpha=.2)
        ax.plot(klines.index, indicator.middle, color='b', alpha=.2)
        ax.plot(klines.index, indicator.upper, color='b', alpha=.2)
        ax.fill_between(klines.index, indicator.lower, indicator.upper, facecolor='blue', alpha=.05)

    def draw_cci(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.real)

    def draw_obv(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.real)

    def draw_macd(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.macd)
        ax.plot(klines.index, indicator.macdsignal)

        colormat = np.where(indicator.macdhist > 0, 'g', 'r')
        ax.bar(klines.index, indicator.macdhist, width=self.bar_width, alpha=.7, color=colormat)

    def draw_sar(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.real, 'b.', alpha=1, markersize=3)

    def draw_ma(self, ax, klines, indicator):
        ax.plot(klines.index, indicator.fast)
        ax.plot(klines.index, indicator.medium)
        ax.plot(klines.index, indicator.long)

    def draw_fibonacci(self, ax, klines, indicator):
        if indicator is not None and len(indicator) > 0:
            is_first = True
            for axis in indicator:
                if is_first:
                    top = axis["price"]
                    is_first = False
                else:
                    bottom = axis["price"]
                    ax.axhspan(ymin=bottom, ymax=top, alpha=0.1, color=axis["color"], label=axis["percent"], zorder=0,
                               linestyle="-")
                    top = bottom

                ax.annotate(f"{str(axis['percent'])[0:4]}",
                            xy=(len(klines), axis['price']), xycoords='data',
                            xytext=(0, -3), textcoords="offset points",
                            size=10,
                            color="grey")
            ax.set_xmargin(0.02)
            ax.hlines(y=indicator[3]['price'], xmin=0, xmax=len(klines), alpha=1, color='red', linestyles="--")

    def draw_volume(self, ax, klines, indicator):
        data = klines.vol
        ax2 = ax.twinx()

        colormat = np.where(klines.is_up, 'g', 'r')
        ax2.bar(klines.index, data, width=self.bar_width, color=colormat, align='center', alpha=.5)
