#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 watchlist 股票的实时数据
使用东方财富行情 API - 修正版
"""
import requests
from datetime import datetime
import os
import time
import json
import re

# 读取 watchlist
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
with open(watchlist_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stocks = []
for line in lines:
    line = line.strip()
    if line and '|' in line:
        code, name = line.split('|', 1)
        stocks.append({'code': code, 'name': name})

print(f"共 {len(stocks)} 只股票需要获取数据")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

results = []
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://quote.eastmoney.com/',
}

for stock in stocks:
    code = stock['code']
    name = stock['name']
    
    try:
        # 东方财富实时行情接口
        if code.endswith('.HK'):
            # 港股
            hk_code = code.replace('.HK', '')
            symbol = f'116.{hk_code}'
        elif '.' in code:
            # A 股 - 需要转换格式
            if code.endswith('.SH'):
                symbol = f'1.{code.replace(".SH", "")}'
            elif code.endswith('.SZ'):
                symbol = f'0.{code.replace(".SZ", "")}'
            else:
                symbol = f'1.{code}'
        else:
            # 纯数字代码，默认上证
            if code.startswith('6') or code.startswith('9'):
                symbol = f'1.{code}'
            else:
                symbol = f'0.{code}'
        
        # 简化字段请求
        url = f'http://push2.eastmoney.com/api/qt/stock/get?secid={symbol}&fields=f43,f57,f58,f84,f166,f167,f168&ut=fa5fd1943c7b386f172d6893dbfba10b'
        
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        
        # 解析返回数据
        data_match = re.search(r'\{.*\}', html)
        if data_match:
            data = json.loads(data_match.group())
            if 'data' in data and data['data']:
                stock_data = data['data']
                # f43: 当前价 (分转元)
                # f166: 涨跌额 (分转元)
                # f167: 涨跌幅 (%)
                price = stock_data.get('f43')
                change = stock_data.get('f166')
                change_pct = stock_data.get('f167')
                
                if price is not None:
                    price = price / 100  # 分转元
                    change = change / 100 if change else 0  # 分转元
                    change_pct = change_pct / 100 if change_pct else 0  # 百分比转小数（141 -> 1.41%）
                    
                    results.append({
                        'code': code,
                        'name': name,
                        'price': f"¥{price:.2f}",
                        'change_pct': f"{change_pct:+.2f}%",
                        'change': f"¥{change:.2f}",
                        'timestamp': timestamp
                    })
                    print(f"{code} {name}: {price:.2f} {change_pct:+.2f}%")
                else:
                    print(f"{code} {name}: 无价格数据")
                    results.append({
                        'code': code,
                        'name': name,
                        'price': 'N/A',
                        'change_pct': 'N/A',
                        'change': 'N/A',
                        'timestamp': timestamp
                    })
            else:
                print(f"{code} {name}: 无数据")
                results.append({
                    'code': code,
                    'name': name,
                    'price': 'N/A',
                    'change_pct': 'N/A',
                    'change': 'N/A',
                    'timestamp': timestamp
                })
        else:
            print(f"{code} {name}: 解析失败")
            results.append({
                'code': code,
                'name': name,
                'price': 'N/A',
                'change_pct': 'N/A',
                'change': 'N/A',
                'timestamp': timestamp
            })
        
        time.sleep(0.1)
        
    except Exception as e:
        print(f"{code} {name}: 异常 - {e}")
        results.append({
            'code': code,
            'name': name,
            'price': 'N/A',
            'change_pct': 'N/A',
            'change': 'N/A',
            'timestamp': timestamp
        })

# 保存到文件
output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间\n")
    for r in results:
        f.write(f"{r['code']} | {r['name']} | {r['price']} | {r['change_pct']} | {r['change']} | {r['timestamp']}\n")

print(f"\n数据已保存到 {output_path}")
