#!/usr/bin/env python3
import os
import tushare as ts
from datetime import datetime

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 获取今天日期
today = datetime.now().strftime('%Y%m%d')

# 查询交易日历
cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, is_open='1')

if cal.empty:
    print("NOT_TRADING_DAY")
else:
    print("TRADING_DAY")
