import json
import Exchanges.Bnb as bnb
import Exchanges.Yho as Yho
from Scanner import Scanner
from ScannerOutput import Output
from IndicatorLoader import IndicatorLoader


class ChartScanner:

    def main(self):
        print('Start main...')
        with open('Configs/input_yho.json', 'r') as f:
            input_config = json.load(f)

        # set exchange
        if input_config['exchange']['name'] == 'bnb':
            exchange = bnb.Bnb()
        elif input_config['exchange']['name'] == 'yho':
            exchange = Yho.Yho(input_config)

        all_asset_data = exchange.get_all_dataframe()

        IndicatorLoader(input_config).load_indicators(all_asset_data)

        Scanner(input_config).scan(all_asset_data)

        Output(input_config).generate_output(all_asset_data)


if __name__ == '__main__':
    app = ChartScanner()
    app.main()

