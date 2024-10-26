import json
import threading
import time
import tkinter as tk

import requests


class StockApp:
    def __init__(self, master):
        self.master = master
        self.master.title("股票信息")
        self.master.geometry("300x200")
        self.stock_code = "000001"

        # 股票信息
        self.stock_name = "创业板ETF"
        self.timestamp = "2024-10-25 15:00"
        self.current_price = 2.196
        self.change_percentage = 3

        # 创建标签
        self.label_title = tk.Label(master, text="股票信息", font=("Arial", 16))
        self.label_title.pack(pady=10)

        self.label_stock_name = tk.Label(master, text=f"股票名称：{self.stock_name}", font=("Arial", 12))
        self.label_stock_name.pack(pady=5)

        self.label_timestamp = tk.Label(master, text=f"时间：{self.timestamp}", font=("Arial", 12))
        self.label_timestamp.pack(pady=5)

        self.label_current_price = tk.Label(master, text=f"当前价格：{self.current_price}", font=("Arial", 12))
        self.label_current_price.pack(pady=5)

        self.label_change_percentage = tk.Label(master, text=f"涨跌幅度：{self.change_percentage}%", font=("Arial", 12))
        self.label_change_percentage.pack(pady=5)

        # 启动线程以获取数据
        self.running = True
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        i = 0
        while self.running:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            url = ("https://push2.eastmoney.com/api/qt/stock/trends2/get?secid=0." + self.stock_code + "&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&ut=fa5fd1943c7b386f172d6893dbfba10b&iscr=0&cb=cb_1729920299632_6004225&isqhquote=&cb_1729920299632_6004225=cb_1729920299632_6004225")
            response = requests.get(url, headers=headers)

            # 模拟从API获取JSON数据（替换为实际API URL）
            if response.status_code == 200:
                json_string = response.text.split('(', 1)[1].rsplit(')', 1)[0]
                data = json.loads(json_string)
                k_line = data['data']['trends'][-1].split(",")
                curr_price = k_line[2]
                self.update_display(float(curr_price), data['data']['decimal'])

            # 每隔5秒更新一次
            time.sleep(1)

    def update_display(self, new_price, new_change):
        # 更新标签内容
        self.current_price = new_price
        self.change_percentage = new_change

        self.label_current_price.config(text=f"当前价格：{self.current_price:.3f}")
        self.label_change_percentage.config(text=f"涨跌幅度：{self.change_percentage:.2f}%")

    def on_closing(self):
        self.running = False
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = StockApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
