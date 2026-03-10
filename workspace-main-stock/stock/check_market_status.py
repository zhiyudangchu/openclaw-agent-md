#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tushare as ts
from datetime import datetime

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("TOKEN_NOT_FOUND")
    exit(1)
pro = ts.pro_api(token)

# 获取交易日历 - 检查今天是否交易日
today = datetime.now().strftime('%Y%m%d')
cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, fields='cal_date,is_open')

if cal.empty or cal['is_open'].iloc[0] == 0:
    print("MARKET_CLOSED")
else:
    # 检查当前时间是否在交易时间内 (9:30-11:30, 13:00-15:00)
    now = datetime.now()
    current_time = now.strftime('%H%M')
    
    # 交易时间判断
    if current_time < '0930' or (current_time >= '1130' and current_time < '1300') or current_time > '1500':
        print("MARKET_CLOSED")
    else:
        print("MARKET_OPEN")
