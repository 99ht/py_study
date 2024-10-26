# -*- coding: utf-8 -*-
import openpyxl as op
import os
import pandas as pd


def op_toExcel(data, fileName):  # openpyxl库储存数据到excel
    wb = op.Workbook()  # 创建工作簿对象
    ws = wb['Sheet']  # 创建子表
    ws.append(['序号', '酒店', '价格'])  # 添加表头
    print(data[0]['id'])
    print(data[0])
    print(len(data[0]))
    for i in range(len(data)):
        d = data[i]["id"], data[i]["name"], data[i]["price"]
        ws.append(d)  # 每次写入一行
    wb.save(fileName)


# "-------------数据用例-------------"
testData = [
    {"id": 1, "name": "立智", "price": 100},
    {"id": 2, "name": "维纳", "price": 200},
    {"id": 3, "name": "如家", "price": 300},
    {"id": 4, "name": "汉庭", "price": 400},
    {"id": 5, "name": "汉庭", "price": 500},
]
fileName = '测试3.xlsx'
if os.path.exists(fileName):
    os.remove(fileName)
op_toExcel(testData, fileName)

sheet_1 = pd.read_html('https://quote.eastmoney.com/sz159632.html')
print(sheet_1[0])