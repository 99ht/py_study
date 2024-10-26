import os

import pandas as pd


class CSVConfig:
    stock_data = []

    def __init__(self, stock_code, market_code):
        self.stock_code = str(stock_code)
        self.market_code = str(market_code)
        print(self.stock_code, self.market_code)

    def __hash__(self):
        # 使用 symbol 的哈希值作为 Stock 对象的哈希值
        return hash(f'{self.stock_code}#{self.market_code}')

    def __eq__(self, other):
        # 两个 Stock 对象相等当且仅当它们的 symbol 相等
        if isinstance(other, CSVConfig):
            return self.stock_code == other.stock_code and self.market_code == other.market_code
        return False

    def __repr__(self):
        return f"CSVConfig(stock_code={self.stock_code}, market_code={self.market_code})"

    @staticmethod
    def __reload_config__():
        current_dir = os.getcwd()  # 这将是当前脚本的目录
        csv_file_path = os.path.join(current_dir, 'config.csv')
        df = pd.read_csv(csv_file_path, dtype={'stockCode': str})
        CSVConfig.stock_data = [CSVConfig(row['stockCode'], row['marketCode']) for index, row in df.iterrows()]
        return CSVConfig.stock_data

    @staticmethod
    def __get_config__():
        if len(CSVConfig.stock_data) == 0:
            CSVConfig.__reload_config__()
        return CSVConfig.stock_data
