#!/usr/bin/env python3
import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 自选股列表 (带.SZ/.SH 后缀)
stocks = ['601857.SH', '603606.SH', '002600.SZ', '002961.SZ', '001872.SZ']
ts_code_str = ','.join(stocks)

# 获取实时日线数据
df = pro.rt_k(ts_code=ts_code_str)

# 计算涨跌幅和涨跌额
df['pct_chg'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
df['change'] = (df['close'] - df['pre_close']).round(2)

# 格式化输出
output_file = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'

# 写入 CSV 格式
with open(output_file, 'w') as f:
    # 写入表头
    f.write('ts_code,name,pre_close,high,open,low,close,vol,amount,num,trade_time,pct_chg,change\n')
    
    # 写入数据行
    for idx, row in df.iterrows():
        trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        line = f"{row['ts_code']},{row['name']},{row['pre_close']},{row['high']},{row['open']},{row['low']},{row['close']},{row['vol']},{row['amount']},{row['num']},{trade_time},{row['pct_chg']},{row['change']}\n"
        f.write(line)

print(f"Data fetched successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total records: {len(df)}")
print(df[['ts_code', 'name', 'close', 'pct_chg', 'change']])
