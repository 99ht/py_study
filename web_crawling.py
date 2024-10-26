import json
import threading
import time
import tkinter as tk
from enum import Enum
from tkinter import ttk

import requests


class Stock(Enum):
    # 纳指ETF
    NSDK = ("513100", "1")
    # 平安银行
    ZGPA = ("000001", "0")

    def __init__(self, stock_code, market_code):
        self.stock_code = stock_code
        self.market_code = market_code


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
    cb = "cb_1729920299632_6004225"
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market_code}.{stock_code}&fields1=f1,f2,f3,"
        f"f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,"
        f"f58&ut=fa5fd1943c7b386f172d6893dbfba10b&iscr=0&cb={cb}&isqhquote=&{cb}={cb}")
    response = requests.get(url, headers=headers)
    # 模拟从API获取JSON数据（替换为实际API URL）
    if response.status_code == 200:
        json_string = response.text.split('(', 1)[1].rsplit(')', 1)[0]
        json_obj = json.loads(json_string)

        data = json_obj["data"]
        k_line = data['trends'][-1].split(",")
        # 上日收盘
        pre_close = data["preClose"]
        curr_price = float(k_line[2])
        # 涨跌幅
        change_rate = (curr_price - pre_close) / pre_close
        return data["name"], float(curr_price), f"{change_rate:.2%}"
    return None, None


class StockApp:
    def __init__(self, master):
        self.master = master
        self.master.title("股票信息")
        self.master.geometry("500x300")

        # 创建 Treeview 小部件
        tree = ttk.Treeview(root)
        self.tree = tree

        # 定义列
        tree["columns"] = ("#1", "#2", "#3", "#4", "#5")

        # 设置列标题
        tree.heading("#0", text="序号")
        tree.heading("#1", text="股票代码")
        tree.heading("#2", text="股票名称")
        tree.heading("#3", text="市场代码")
        tree.heading("#4", text="涨跌幅")
        tree.heading("#5", text="当前股价")

        # 设置列宽度
        tree.column("#0", width=50, minwidth=50, anchor=tk.CENTER)
        tree.column("#1", width=100, minwidth=100, anchor=tk.CENTER)
        tree.column("#2", width=100, minwidth=100, anchor=tk.CENTER)
        tree.column("#3", width=60, minwidth=60, anchor=tk.CENTER)
        tree.column("#4", width=60, minwidth=60, anchor=tk.CENTER)
        tree.column("#5", width=60, minwidth=60, anchor=tk.CENTER)

        # 将 Treeview 放置在主窗口中
        tree.pack(expand=True, fill=tk.BOTH)

        # 启动线程以获取数据
        self.running = True
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        item_dict = {}
        j = 0
        while self.running:
            i = 0
            j += 1
            for stock in Stock:
                name, price, change = get_socket_data(stock.market_code, stock.stock_code)
                if stock not in item_dict:
                    i += 1
                    item = self.tree.insert("", tk.END, text=str(i),
                                            values=(
                                                stock.stock_code, name, market_dict[stock.market_code], change, price))
                    item_dict[stock] = item
                else:
                    self.tree.item(item_dict[stock],
                                   values=(stock.stock_code, name, market_dict[stock.market_code], change, price))

            time.sleep(1)

    def on_closing(self):
        self.running = False
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = StockApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
