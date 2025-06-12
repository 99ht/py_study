import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

url = ("https://push2.eastmoney.com/api/qt/stock/get?invt=2&fltt=1&cb=jQuery35102903516224067517_1729925852277&fields"
       "=f58%2Cf107%2Cf57%2Cf43%2Cf59%2Cf169%2Cf170%2Cf152%2Cf46%2Cf60%2Cf44%2Cf45%2Cf47%2Cf48%2Cf19%2Cf532%2Cf39"
       "%2Cf161%2Cf49%2Cf171%2Cf50%2Cf86%2Cf600%2Cf601%2Cf154%2Cf84%2Cf85%2Cf168%2Cf108%2Cf116%2Cf167%2Cf164%2Cf92"
       "%2Cf71%2Cf117%2Cf292%2Cf301&secid=0.159915&ut=fa5fd1943c7b386f172d6893dbfba10b&wbp2u=%7C0%7C0%7C0%7Cweb&dect"
       "=1&_=1729925852278")

response = requests.get(url, headers=headers)
print(response.text)