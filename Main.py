import json
import Exchanges.Bnb as bnb
import Exchanges.Idx as Idx
import Exchanges.Tda as Tda
import Exchanges.Yho as Yho
import Exchanges.Iex as Iex
import Exchanges.Ond as Ond
import Exchanges.Ivs as Ivs
import Exchanges.Mkw as Mkw
from Scanner import Scanner
from ScannerOutput import Output
from IndicatorLoader import IndicatorLoader


class ChartScanner:

    def main(self):
        print('Start main...')
        with open('Configs/input_yho.json', 'r') as f:
            input_config = json.load(f)

        # set exchange
        if input_config['Exchange'] == 'bnb':
            exchange = bnb.Bnb()
        elif input_config['Exchange'] == 'tda':
            exchange = Tda.Tda()
        elif input_config['Exchange'] == 'yho':
            exchange = Yho.Yho(input_config)
        elif input_config['Exchange'] == 'iex':
            exchange = Iex.Iex()
        elif input_config['Exchange'] == 'ond':
            exchange = Ond.Ond()
        elif input_config['Exchange'] == 'ivs':
            exchange = Ivs.Ivs()
        elif input_config['Exchange'] == 'mkw':
            exchange = Mkw.Mkw()
        else:
            exchange = Idx.Idx()

        allAssetData = exchange.get_all_dataframe()

        IndicatorLoader(input_config).load_indicators(allAssetData)

        Scanner(input_config).scan(allAssetData)

        #if input_config['Depth']['Visible'] == 'true':
        #    exchange.get_all_depths(input_config)

        Output(input_config).generate_output(allAssetData)


if __name__ == '__main__':
    app = ChartScanner()
    app.main()

