#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时数据 - 使用 tushare 实时日线接口
"""

import tushare as ts
import os
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
print(f"TUSHARE_TOKEN: {token[:10]}...")

# 初始化 pro 接口
pro = ts.pro_api(token)

# 读取自选股列表
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|')
            # 处理股票代码格式
            if '.' in code:
                ts_code = code  # 已经是 ts_code 格式
            else:
                # 根据代码前缀判断交易所
                if code.startswith('6'):
                    ts_code = code + '.SH'
                elif code.startswith('0') or code.startswith('3'):
                    ts_code = code + '.SZ'
                else:
                    ts_code = code  # 港股或美股保持原样
            stocks.append((ts_code, name))

print(f"自选股数量：{len(stocks)}")
print("股票代码列表:")
for ts_code, name in stocks:
    print(f"  {ts_code} - {name}")

# 获取实时日线数据
# 只处理 A 股（.SH 和 .SZ 结尾的）
a_stocks = [(code, name) for code, name in stocks if code.endswith('.SH') or code.endswith('.SZ')]
if a_stocks:
    ts_codes = ','.join([code for code, _ in a_stocks])
    print(f"\n获取 A 股实时数据：{ts_codes}")
    
    try:
        # 使用实时日线接口
        df = pro.daily(ts_code=ts_codes, start_date=datetime.now().strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
        print(f"\n获取成功，数据条数：{len(df)}")
        print(df)
    except Exception as e:
        print(f"获取实时日线数据失败：{e}")
        
        # 尝试使用通用行情接口
        try:
            print("\n尝试使用通用行情接口...")
            df = pro.quote_daily(ts_code=ts_codes)
            print(f"获取成功，数据条数：{len(df)}")
            print(df)
        except Exception as e2:
            print(f"通用行情接口也失败：{e2}")
else:
    print("没有 A 股股票")
