#!/usr/bin/env python3
import os
import sys
import tushare as ts
from datetime import datetime
import json

# 获取 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("ERROR: TUSHARE_TOKEN not set", file=sys.stderr)
    sys.exit(1)

# 初始化
pro = ts.pro_api(token)

# 读取 watchlist
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
stocks = []
with open(watchlist_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|')
            stocks.append((code.strip(), name.strip()))

# 构建 ts_code 列表
ts_codes = []
for code, name in stocks:
    # 已经是 ts_code 格式 (如 601857.SH, 9866.HK)
    if '.' in code:
        ts_codes.append(code)
    else:
        # A 股代码转换
        if code.startswith('6'):
            ts_codes.append(f"{code}.SH")
        elif code.startswith('0') or code.startswith('3'):
            ts_codes.append(f"{code}.SZ")
        elif code.startswith('9') or code.startswith('8'):
            ts_codes.append(f"{code}.BJ")

# 批量获取实时日线数据 - 使用 rt_k 接口
ts_code_str = ','.join(ts_codes)
print(f"Fetching realtime data for: {ts_code_str}", file=sys.stderr)

try:
    # 使用 rt_k 接口获取实时日线数据
    df = pro.rt_k(ts_code=ts_code_str)
    
    if df is not None and len(df) > 0:
        # 转换为 JSON 格式输出
        result = []
        for idx, row in df.iterrows():
            record = {
                'ts_code': row.get('ts_code', ''),
                'name': row.get('name', ''),
                'pre_close': float(row.get('pre_close', 0)) if row.get('pre_close') else 0,
                'close': float(row.get('close', 0)) if row.get('close') else 0,
                'open': float(row.get('open', 0)) if row.get('open') else 0,
                'high': float(row.get('high', 0)) if row.get('high') else 0,
                'low': float(row.get('low', 0)) if row.get('low') else 0,
                'vol': int(row.get('vol', 0)) if row.get('vol') else 0,
                'amount': int(row.get('amount', 0)) if row.get('amount') else 0,
                'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }
            # 计算涨跌幅和涨跌额
            if record['pre_close'] > 0:
                record['change'] = record['close'] - record['pre_close']
                record['pct_change'] = (record['change'] / record['pre_close']) * 100
            else:
                record['change'] = 0
                record['pct_change'] = 0
            result.append(record)
        
        # 输出 JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("[]", file=sys.stdout)
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("[]", file=sys.stdout)
