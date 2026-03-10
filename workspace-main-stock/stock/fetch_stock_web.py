#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过腾讯财经获取实时行情（无需 Token）
数据格式解析 (基于实际响应):
v_sh601857="1~中国石油~601857~11.99~12.92~12.18~...
索引 (1-based):
  1=unknown, 2=名称，3=代码，4=当前价，5=昨收，6=今开
  33=最高价，34=最低价
"""

import requests
import json
from datetime import datetime
import sys

# 读取自选股列表
watchlist_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt'
stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|', 1)
            stocks.append({'code': code.strip(), 'name': name.strip()})

def parse_stock_data(data_str, code, name):
    """解析腾讯财经数据"""
    try:
        # 提取引号内的内容
        if '"' in data_str:
            content = data_str.split('"')[1]
        else:
            content = data_str
        
        parts = content.split('~')
        
        if len(parts) < 35:
            return None
        
        # 基本数据 (0-based 索引)
        current_name = parts[1] if len(parts) > 1 else name
        close = float(parts[3]) if len(parts) > 3 and parts[3] else 0
        pre_close = float(parts[4]) if len(parts) > 4 and parts[4] else 0
        open_price = float(parts[5]) if len(parts) > 5 and parts[5] else close
        
        # 最高价和最低价 (索引 33 和 34, 0-based)
        high = float(parts[33]) if len(parts) > 33 and parts[33] else close
        low = float(parts[34]) if len(parts) > 34 and parts[34] else close
        
        # 计算涨跌
        change = close - pre_close
        change_pct = (change / pre_close * 100) if pre_close else 0
        
        return {
            'code': code,
            'name': current_name,
            'close': round(close, 2),
            'pre_close': round(pre_close, 2),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
        }
    except Exception as e:
        print(f'Parse error for {code}: {e}', file=sys.stderr)
        return None

def fetch_a_stock(code, name):
    """获取 A 股数据"""
    if code.startswith('6') or code.startswith('9'):
        symbol = f'sh{code}'
    else:
        symbol = f'sz{code}'
    
    url = f'http://qt.gtimg.cn/q={symbol}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching A-share {code}: {e}', file=sys.stderr)
    return None

def fetch_hk_stock(code, name):
    """获取港股数据"""
    hk_code = code.replace('.HK', '')
    url = f'http://qt.gtimg.cn/q=hk{hk_code}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching HK stock {code}: {e}', file=sys.stderr)
    return None

def fetch_us_stock(code, name):
    """获取美股数据"""
    url = f'http://qt.gtimg.cn/q=gb_{code.lower()}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching US stock {code}: {e}', file=sys.stderr)
    return None

# 获取所有股票数据
results = []
for stock in stocks:
    code = stock['code']
    name = stock['name']
    
    data = None
    if '.HK' in code:
        data = fetch_hk_stock(code, name)
    elif '.' not in code:  # A 股
        data = fetch_a_stock(code, name)
    else:  # 美股等
        data = fetch_us_stock(code, name)
    
    if data:
        results.append(data)
        print(f"Fetched: {data['code']} - {data['name']} @ ¥{data['close']} ({data['change_pct']:+.2f}%)")
    else:
        print(f"Failed: {code} - {name}", file=sys.stderr)

if results:
    print(f'\n=== DATA START ===')
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    print('=== DATA END ===')
    print(f'\nTotal: {len(results)} stocks fetched successfully')
else:
    print('No data fetched', file=sys.stderr)
    sys.exit(1)
