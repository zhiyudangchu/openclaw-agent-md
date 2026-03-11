#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据 (使用 rt_k 接口)
"""

import tushare as ts
import os
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
pro = ts.pro_api(token)

def get_watchlist():
    """读取自选股列表"""
    watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
    stocks = []
    with open(watchlist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                code, name = line.split('|', 1)
                # 处理股票代码格式
                if '.' not in code and code.isdigit():
                    # 6 位数字代码，需要添加后缀
                    if code.startswith('6') or code.startswith('9'):
                        code = code + '.SH'
                    else:
                        code = code + '.SZ'
                stocks.append({'ts_code': code, 'name': name})
    return stocks

def get_realtime_k_data(ts_codes):
    """
    获取实时日线数据 (rt_k 接口)
    """
    # 将代码列表转换为逗号分隔的字符串
    codes_str = ','.join(ts_codes)
    
    try:
        # 使用 rt_k 接口获取实时日线数据
        data = pro.rt_k(ts_code=codes_str, fields='ts_code,name,close,pct_chg,change,pre_close,open,high,low,vol,amount,trade_time')
        return data
    except Exception as e:
        print(f"获取 rt_k 数据失败：{e}")
        # 尝试使用通用行情接口作为备选
        try:
            data = pro.daily(ts_code=codes_str, start_date=datetime.now().strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
            print("使用 daily 接口作为备选")
            return data
        except Exception as e2:
            print(f"备选接口也失败：{e2}")
            return None

def format_output(data):
    """格式化输出数据"""
    if data is None or data.empty:
        return ""
    
    output_lines = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    output_lines.append(f"数据时间：{current_time}")
    output_lines.append("数据来源：Tushare Pro (rt_k 接口)")
    output_lines.append("-" * 80)
    
    for idx, row in data.iterrows():
        ts_code = row.get('ts_code', '')
        name = row.get('name', '')
        close = row.get('close', 0)
        pct_chg = row.get('pct_chg', 0)
        change = row.get('change', 0)
        trade_time = row.get('trade_time', current_time)
        
        # 格式化输出：代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 时间
        line = f"{ts_code}|{name}|{close:.2f}|{pct_chg:.2f}|{change:.2f}|{trade_time}"
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def main():
    # 读取自选股
    stocks = get_watchlist()
    print(f"读取到 {len(stocks)} 只自选股")
    
    # 获取代码列表
    ts_codes = [s['ts_code'] for s in stocks]
    
    # 分批获取数据（避免单次请求过多）
    batch_size = 10
    all_data = []
    
    for i in range(0, len(ts_codes), batch_size):
        batch = ts_codes[i:i+batch_size]
        print(f"获取批次 {i//batch_size + 1}: {batch}")
        batch_data = get_realtime_k_data(batch)
        if batch_data is not None and not batch_data.empty:
            all_data.append(batch_data)
    
    # 合并数据
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        output = format_output(result)
        
        # 写入文件
        output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"数据已写入：{output_path}")
        print(output)
    else:
        print("未获取到任何数据")

if __name__ == "__main__":
    import pandas as pd
    main()
