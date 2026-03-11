#!/usr/bin/env python3
"""检查市场状态 - 判断是否收盘或休市以及是否在交易时间内"""
import os
import tushare as ts
from datetime import datetime

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 获取今天日期
today = datetime.now().strftime('%Y%m%d')
current_time = datetime.now().strftime('%H%M%S')

print(f"检查日期：{today}")
print(f"当前时间：{current_time}")

# 获取交易日历
cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, fields='cal_date,is_open')
print(f"交易日历：{cal}")

if cal.empty or cal['is_open'].iloc[0] == 0:
    print("今日休市")
    exit(1)

# A 股交易时间：9:30-11:30, 13:00-15:00
# 判断是否在交易时间内
hour = int(current_time[:2])
minute = int(current_time[2:4])
time_val = hour * 100 + minute

# 开盘前
if time_val < 930:
    print("未开盘")
    exit(1)

# 午休
if 1130 <= time_val < 1300:
    print("午休时间")
    exit(1)

# 收盘后
if time_val >= 1500:
    print("已收盘")
    exit(1)

print("交易时间内，可以继续")
exit(0)
