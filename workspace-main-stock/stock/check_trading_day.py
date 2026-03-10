#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查今日是否为交易日且未收盘
"""

import tushare as ts
import os
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
print(f"TUSHARE_TOKEN: {token[:10]}...")

# 初始化 pro 接口
pro = ts.pro_api(token)

# 获取当前日期
today = datetime.now().strftime('%Y%m%d')
current_time = datetime.now().strftime('%H%M%S')

print(f"当前日期：{today}")
print(f"当前时间：{current_time}")

# 获取交易日历
try:
    cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
    if cal.empty:
        print("今日不是交易日")
        exit(1)
    
    is_open = cal['is_open'].iloc[0]
    if is_open == 0:
        print("今日休市")
        exit(1)
    
    print("今日是交易日")
    
    # A 股交易时间：9:30-11:30, 13:00-15:00
    # 当前时间如果在 15:00 之后，则认为已收盘
    if int(current_time) >= 150000:
        print("已收盘（>= 15:00）")
        exit(1)
    elif int(current_time) < 93000:
        print("未开盘（< 9:30）")
        exit(1)
    else:
        print("未收盘，可以获取实时数据")
        exit(0)
        
except Exception as e:
    print(f"获取交易日历失败：{e}")
    # 如果获取失败，默认按时间判断
    if int(current_time) >= 150000:
        print("已收盘（>= 15:00）")
        exit(1)
    else:
        print("默认未收盘")
        exit(0)
