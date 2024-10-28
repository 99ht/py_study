import json
import threading
import time
import tkinter as tk
from tkinter import ttk

import requests

from config_reader import CSVConfig as cfg

market_dict = {
    "0": "SZ",
    "1": "SH"
}


def get_socket_data(market_code, stock_code):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market_code}.{stock_code}&fields1=f1,f2,f3,"
        f"f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58")
    response = requests.get(url, headers=headers)
    # 模拟从API获取JSON数据（替换为实际API URL）
    if response.status_code == 200:
        json_string = response.text
        json_obj = json.loads(json_string)  # 将字符串转为python的字典类型

        data = json_obj["data"]
        k_line = data['trends'][-1].split(",")
        # 上日收盘
        pre_close = data["preClose"]
        curr_price = float(k_line[2])
        # 涨跌幅
        change_rate = (curr_price - pre_close) / pre_close
        # 涨跌额
        change_price = curr_price - pre_close
        return market_code, stock_code, data["name"], float(curr_price), f"{change_rate:.2%}", f"{change_price:.3}"
    return None, None


class StockApp:
    def __init__(self, master):
        self.master = master
        self.master.title("股票信息")
        self.master.geometry("500x300")

        # 创建 Treeview 小部件
        tree = ttk.Treeview(root)
        self.tree = tree

        columns = ["#0", "#1", "#2", "#3", "#4", "#5", "#6"]
        headers = ["序号", "股票代码", "股票名称", "市场代码", "涨跌幅", "当前股价", "当日涨跌"]

        # 设置列
        tree["columns"] = columns

        # 设置列标题
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
        # 设置列宽度
        tree.column("#0", width=50, minwidth=50, anchor=tk.CENTER)
        tree.column("#1", width=100, minwidth=100, anchor=tk.CENTER)
        tree.column("#2", width=100, minwidth=100, anchor=tk.CENTER)
        tree.column("#3", width=60, minwidth=60, anchor=tk.CENTER)
        tree.column("#4", width=60, minwidth=60, anchor=tk.CENTER)
        tree.column("#5", width=60, minwidth=60, anchor=tk.CENTER)
        tree.column("#6", width=60, minwidth=60, anchor=tk.CENTER)

        # 配置标签,设置颜色
        tree.tag_configure('green', foreground='green')
        tree.tag_configure('red', foreground='red')

        # 将 Treeview 放置在主窗口中
        tree.pack(expand=True, fill=tk.BOTH)

        # 启动线程以获取数据
        self.running = True
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        item_dict = {}

        while self.running:
            i = 0
            datas = []
            for stock in cfg.__get_config__():
                datas.append(get_socket_data(stock.market_code, stock.stock_code))

            for data in datas:
                i += 1
                self.update_table(i, data, item_dict)

            time.sleep(3)

    def update_table(self, i, data, item_dict):
        market_code, stock_code, name, price, change, change_price = data
        key = f"{market_code}_{stock_code}"
        if key not in item_dict:
            item = self.tree.insert("", tk.END, text=str(i),
                                    values=(
                                        stock_code, name, market_dict[market_code], change, price,
                                        change_price),
                                    tags=('green',) if float(change_price) < 0 else (('red',) if float(change_price) > 0 else ''))
            item_dict[key] = item
        else:
            self.tree.item(item_dict[key],
                           values=(
                               stock_code, name, market_dict[market_code], change, price,
                               change_price),
                           tags=('green',) if float(change_price) < 0 else (('red',) if float(change_price) > 0 else ''))

    def on_closing(self):
        self.running = False
        self.master.destroy()


if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = StockApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"发生了一个异常: {e}")
