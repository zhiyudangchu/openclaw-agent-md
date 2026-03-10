#!/usr/bin/env python3
"""
使用 Tushare 获取自选股实时日线数据
"""
import os
import tushare as ts
from datetime import datetime
import pandas as pd

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

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
                # 转换代码格式为 tushare 格式
                if code.endswith('.SH') or code.endswith('.SZ'):
                    ts_code = code
                elif code.endswith('.HK'):
                    ts_code = code.replace('.HK', '.HK')
                elif code.isdigit():
                    # A 股代码
                    if code.startswith('6'):
                        ts_code = f"{code}.SH"
                    elif code.startswith('0') or code.startswith('3'):
                        ts_code = f"{code}.SZ"
                    elif code.startswith('9') or code.startswith('8'):
                        ts_code = f"{code}.BJ"
                    else:
                        ts_code = f"{code}.SH"
                else:
                    # 美股等，跳过
                    ts_code = None
                
                if ts_code:
                    stocks.append({'ts_code': ts_code, 'name': name})

# 获取实时日线数据 - 使用实时日线接口
ts_codes = ','.join([s['ts_code'] for s in stocks])
print(f"请求代码：{ts_codes}")

try:
    # 使用实时日线接口 (doc_id=372) - 先尝试今日
    df = pro.daily(ts_code=ts_codes, start_date=datetime.now().strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
    
    if df.empty:
        print("今日数据未更新，获取最近一个交易日数据 (2026-03-09)")
        # 获取最近的数据
        df = pro.daily(ts_code=ts_codes, start_date='20260309', end_date='20260309')
    
    results = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for _, row in df.iterrows():
        ts_code = row['ts_code']
        # 查找对应的股票名称
        name = next((s['name'] for s in stocks if s['ts_code'] == ts_code), ts_code)
        
        close = row.get('close', 0)
        pre_close = row.get('pre_close', 0)
        change = row.get('change', 0)
        pct_chg = row.get('pct_chg', 0)
        trade_date = row.get('trade_date', '')
        
        # 格式化日期
        if trade_date:
            trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        
        results.append({
            'ts_code': ts_code,
            'name': name,
            'close': close,
            'pre_close': pre_close,
            'change': change,
            'pct_chg': pct_chg,
            'trade_date': trade_date,
            'timestamp': timestamp
        })
        print(f"{ts_code} {name}: ¥{close:.2f} {pct_chg:+.2f}%")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"数据时间：{timestamp}\n")
        f.write(f"数据来源：Tushare Pro\n")
        f.write("-" * 80 + "\n")
        for r in results:
            f.write(f"{r['ts_code']}|{r['name']}|{r['close']:.2f}|{r['pct_chg']:.2f}|{r['change']:.2f}|{r['timestamp']}\n")
    
    print(f"\n共获取 {len(results)} 只股票数据，已保存到 {output_path}")
    
except Exception as e:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Error: {e}")
    # 如果 tushare 失败，使用备用数据
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"数据时间：{timestamp}\n")
        f.write(f"数据来源：Tushare Pro (获取失败)\n")
