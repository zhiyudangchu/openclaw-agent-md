#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查市场状态并获取实时数据
"""

import os
import tushare as ts
from datetime import datetime
import sys
import pandas as pd

# 获取 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print('Error: TUSHARE_TOKEN not set')
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 检查今日是否交易日
today = datetime.now().strftime('%Y%m%d')
try:
    cal_df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
    is_open = cal_df['is_open'].iloc[0] if len(cal_df) > 0 else 0
except Exception as e:
    print(f'Error checking calendar: {e}')
    sys.exit(1)

if is_open == 0:
    print('MARKET_CLOSED')
    sys.exit(0)

# 获取当前时间判断是否盘中
now = datetime.now()
current_time = now.strftime('%H%M')
# A 股交易时间：9:30-11:30, 13:00-15:00
if current_time < '0930' or (current_time >= '1130' and current_time < '1300') or current_time >= '1500':
    print('MARKET_CLOSED')
    sys.exit(0)

print('MARKET_OPEN')

# 读取自选股列表
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|', 1)
            stocks.append(code)

# 构建 ts_code 格式（添加后缀）
ts_codes = []
for code in stocks:
    code = code.strip()
    if '.' in code:
        # 已经有后缀（如港股 9866.HK 或美股 AAPL）
        if code.endswith('.HK'):
            ts_codes.append(code)
        elif code.endswith('.SH') or code.endswith('.SZ'):
            ts_codes.append(code)
        else:
            # 美股
            ts_codes.append(code)
    else:
        # A 股，添加后缀
        if code.startswith('6') or code.startswith('9'):
            ts_codes.append(code + '.SH')
        else:
            ts_codes.append(code + '.SZ')

# 分批获取数据（A 股、港股、美股分开）
a_stocks = [c for c in ts_codes if c.endswith('.SH') or c.endswith('.SZ')]
hk_stocks = [c for c in ts_codes if c.endswith('.HK')]
us_stocks = [c for c in ts_codes if not c.endswith('.SH') and not c.endswith('.SZ') and not c.endswith('.HK')]

all_data = []

# 获取 A 股实时日线
if a_stocks:
    try:
        # 分批获取，每批最多 10 个
        for i in range(0, len(a_stocks), 10):
            batch = a_stocks[i:i+10]
            ts_code_str = ','.join(batch)
            df = pro.rt_k(ts_code=ts_code_str)
            if len(df) > 0:
                all_data.append(df)
    except Exception as e:
        print(f'Error fetching A-share data: {e}', file=sys.stderr)

# 获取港股实时日线
if hk_stocks:
    try:
        for code in hk_stocks:
            df = pro.hk_rt_k(ts_code=code)
            if len(df) > 0:
                all_data.append(df)
    except Exception as e:
        print(f'Error fetching HK stock data: {e}', file=sys.stderr)

# 获取美股实时日线
if us_stocks:
    try:
        for code in us_stocks:
            df = pro.us_rt_k(ts_code=code)
            if len(df) > 0:
                all_data.append(df)
    except Exception as e:
        print(f'Error fetching US stock data: {e}', file=sys.stderr)

# 合并数据
if all_data:
    result = pd.concat(all_data, ignore_index=True)
    # 输出为 CSV 格式
    print(result.to_csv(index=False))
else:
    print('No data fetched')
    sys.exit(1)
