#!/usr/bin/env python3
"""
获取自选股实时数据
从东方财富网获取实时行情数据
"""
import urllib.request
import json
import re
from datetime import datetime

# 读取 watchlist.txt
watchlist_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt'
output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'

stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            parts = line.split('|')
            if len(parts) == 2:
                code, name = parts
                stocks.append({'code': code, 'name': name})

# 构建东方财富实时数据请求 URL
# 东方财富实时数据接口：http://push2.eastmoney.com/api/qt/stock/get
def get_stock_data(code):
    """获取单个股票的实时数据"""
    # 转换代码格式
    if code.endswith('.SH'):
        secid = f"1.{code.replace('.SH', '')}"
    elif code.endswith('.SZ'):
        secid = f"0.{code.replace('.SZ', '')}"
    elif code.endswith('.HK'):
        secid = f"116.{code.replace('.HK', '')}"
    elif code.isdigit():
        # A 股代码
        if code.startswith('6'):
            secid = f"1.{code}"
        elif code.startswith('0') or code.startswith('3'):
            secid = f"0.{code}"
        elif code.startswith('9') or code.startswith('8'):
            secid = f"0.{code}"  # 北交所
        else:
            secid = f"1.{code}"
    else:
        # 美股等
        return None
    
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f100,f101,f102,f103,f104,f105,f106,f107,f108,f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('data'):
                return data['data']
    except Exception as e:
        print(f"Error fetching {code}: {e}")
    return None

results = []
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for stock in stocks:
    code = stock['code']
    name = stock['name']
    
    data = get_stock_data(code)
    if data:
        # f43: 最新价，f44: 涨跌幅，f45: 涨跌额，f46: 昨收，f47: 今开，f48: 最高，f49: 最低
        # 东方财富 API 返回的价格需要除以 100
        current_price = data.get('f43', 0) / 100 if data.get('f43', 0) > 100 else data.get('f43', 0)
        change_pct = data.get('f44', 0) / 100 if abs(data.get('f44', 0)) > 100 else data.get('f44', 0)
        change_amt = data.get('f45', 0) / 100 if abs(data.get('f45', 0)) > 100 else data.get('f45', 0)
        prev_close = data.get('f46', 0) / 100 if data.get('f46', 0) > 100 else data.get('f46', 0)
        open_price = data.get('f47', 0) / 100 if data.get('f47', 0) > 100 else data.get('f47', 0)
        high = data.get('f48', 0) / 100 if data.get('f48', 0) > 100 else data.get('f48', 0)
        low = data.get('f49', 0) / 100 if data.get('f49', 0) > 100 else data.get('f49', 0)
        
        results.append({
            'code': code,
            'name': name,
            'current_price': current_price,
            'change_pct': change_pct,
            'change_amt': change_amt,
            'prev_close': prev_close,
            'open': open_price,
            'high': high,
            'low': low,
            'timestamp': timestamp
        })
        print(f"{code} {name}: ¥{current_price:.2f} {change_pct:+.2f}%")
    else:
        print(f"{code} {name}: 数据获取失败")

# 写入文件
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"数据时间：{timestamp}\n")
    f.write("-" * 80 + "\n")
    for r in results:
        f.write(f"{r['code']}|{r['name']}|{r['current_price']:.2f}|{r['change_pct']:.2f}|{r['change_amt']:.2f}|{r['timestamp']}\n")

print(f"\n共获取 {len(results)} 只股票数据，已保存到 {output_path}")
