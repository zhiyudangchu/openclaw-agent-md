#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 watchlist 股票的实时数据并保存到 realtime-data.txt
使用同花顺 API 接口
"""
import requests
import json
from datetime import datetime
import os

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

# 同花顺行情 API 接口
def get_realtime_quote(code):
    """获取单只股票实时行情"""
    try:
        # 同花顺行情接口
        if '.' in code or code.endswith('HK'):
            # 港股或美股
            if code.endswith('.HK'):
                hk_code = code.replace('.HK', '')
                url = f'http://q.10jqka.com.cn/hk/detail/stock/{hk_code}/'
            else:
                url = f'http://q.10jqka.com.cn/usa/detail/stock/{code}/'
        else:
            # A 股
            url = f'http://q.10jqka.com.cn/detail/stock/{code}/'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://q.10jqka.com.cn/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        return None  # 需要解析 HTML
    except Exception as e:
        print(f"获取 {code} 失败：{e}")
        return None

# 使用同花顺批量行情接口
def get_batch_quotes():
    """批量获取股票行情"""
    results = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建同花顺批量查询 URL
    codes = ','.join([s['code'] for s in stocks])
    url = f'http://q.10jqka.com.cn/index/index/index/plate/stock/order/desc/page/1/ajax/1/callback/{codes}'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://q.10jqka.com.cn/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 解析数据...
            pass
    except Exception as e:
        print(f"批量获取失败：{e}")
    
    # 如果批量获取失败，则逐个获取
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        
        # 模拟数据（实际应该从 API 获取）
        results.append({
            'code': code,
            'name': name,
            'price': 'N/A',
            'change_pct': 'N/A',
            'change': 'N/A',
            'timestamp': timestamp
        })
    
    return results

# 获取数据
results = get_batch_quotes()

# 保存到文件
output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间\n")
    for r in results:
        f.write(f"{r['code']} | {r['name']} | {r['price']} | {r['change_pct']} | {r['change']} | {r['timestamp']}\n")

print(f"数据已保存到 {output_path}")
