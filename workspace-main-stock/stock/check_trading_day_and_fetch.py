#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查今日是否交易日，并获取自选股实时数据
"""

import os
import sys
import tushare as ts
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 获取今天日期
today = datetime.now().strftime('%Y%m%d')
today_str = datetime.now().strftime('%Y-%m-%d')

# 检查今天是否是交易日（通过交易日历）
# 获取上交所交易日历
cal_df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, is_open='1')

if cal_df.empty:
    print("今日非交易日，任务结束")
    sys.exit(0)
else:
    print(f"今日 ({today_str}) 是交易日，继续执行")

# 读取 watchlist.txt
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            parts = line.split('|')
            if len(parts) >= 2:
                code = parts[0].strip()
                name = parts[1].strip()
                stocks.append({'code': code, 'name': name})

print(f"共读取 {len(stocks)} 只股票")

# 构建 ts_code 列表
# 需要判断股票代码的交易所后缀
def format_ts_code(code):
    """将股票代码转换为 tushare 格式"""
    code = code.strip()
    # 如果已经有.SH 或.SZ 后缀，直接返回
    if '.SH' in code or '.SZ' in code:
        return code
    # 港股
    if '.HK' in code:
        return code
    # A 股：600/601/603/688 开头是上海，000/001/002/003 开头是深圳，300/301 开头是深圳
    if code.startswith('6') or code.startswith('688'):
        return f"{code}.SH"
    elif code.startswith('0') or code.startswith('3'):
        return f"{code}.SZ"
    # 美股
    if len(code) <= 5 and code.isalpha():
        return code
    return code

# 格式化所有股票代码
ts_codes = [format_ts_code(s['code']) for s in stocks]
# 过滤掉港股和美股（tushare 实时数据主要支持 A 股）
a_stock_codes = [c for c in ts_codes if '.SH' in c or '.SZ' in c]

if not a_stock_codes:
    print("没有 A 股股票代码，任务结束")
    sys.exit(0)

print(f"A 股数量：{len(a_stock_codes)}")

# 获取实时行情数据 - 使用实时日线接口
# 文档：https://tushare.pro/document/2?doc_id=109
try:
    # 批量获取实时数据
    df = pro.daily(ts_code=','.join(a_stock_codes), start_date=today, end_date=today)
    
    if df.empty:
        print("未获取到今日数据，尝试获取最近一个交易日数据")
        # 尝试获取最近的数据
        df = pro.daily(ts_code=','.join(a_stock_codes), start_date='20260309', end_date='20260310')
    
    print(f"获取到 {len(df)} 条记录")
    
    # 保存到 realtime-data.txt
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    
    if not df.empty:
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("ts_code|name|trade_date|open|high|low|close|pre_close|change|pct_chg|vol|amount\n")
            for idx, row in df.iterrows():
                line = f"{row.get('ts_code', '')}|{row.get('name', '')}|{row.get('trade_date', '')}|{row.get('open', 0)}|{row.get('high', 0)}|{row.get('low', 0)}|{row.get('close', 0)}|{row.get('pre_close', 0)}|{row.get('change', 0)}|{row.get('pct_chg', 0)}|{row.get('vol', 0)}|{row.get('amount', 0)}\n"
                f.write(line)
        print(f"数据已保存到 {output_path}")
    else:
        print("未获取到有效数据")
        sys.exit(1)
        
except Exception as e:
    print(f"获取数据失败：{e}")
    sys.exit(1)

print("数据获取完成")
