import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 神火股份股票代码
ts_code = '000933.SZ'

# 1. 先获取股票基本信息，确定上市日期
print("正在获取股票基本信息...")
stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,list_date')
print(stock_info)

list_date = stock_info.iloc[0]['list_date']
print(f"\n上市日期：{list_date}")

# 2. 获取上市以来的所有日线数据
print("\n正在获取历史 K 线数据...")
df = pro.daily(ts_code=ts_code, start_date=list_date, end_date=datetime.now().strftime('%Y%m%d'))

# 按交易日期排序（从早到晚）
df = df.sort_values('trade_date').reset_index(drop=True)

print(f"\n获取到 {len(df)} 条记录")
print(f"数据范围：{df['trade_date'].min()} 至 {df['trade_date'].max()}")

# 3. 计算一些关键统计数据
print("\n=== 关键统计数据 ===")
print(f"上市首日收盘价：{df.iloc[0]['close']}")
print(f"最新收盘价：{df.iloc[-1]['close']}")
print(f"历史最高价：{df['high'].max()}")
print(f"历史最低价：{df['low'].min()}")
print(f"累计成交量：{df['vol'].sum():,.0f} 手")
print(f"累计成交额：{df['amount'].sum():,.2f} 千元")

# 4. 保存数据到 CSV
output_path = '/home/openclaw/.openclaw/workspace-main-stock/tmp/shenhuo_kline.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n数据已保存到：{output_path}")

# 5. 输出关键数据摘要（用于飞书文档）
print("\n=== 数据摘要（用于飞书文档）===")
print(f"股票名称：神火股份")
print(f"股票代码：{ts_code}")
print(f"上市日期：{list_date}")
print(f"数据条数：{len(df)}")
print(f"上市首日：{df.iloc[0]['trade_date']}, 开盘:{df.iloc[0]['open']}, 收盘:{df.iloc[0]['close']}, 最高:{df.iloc[0]['high']}, 最低:{df.iloc[0]['low']}")
print(f"最新交易日：{df.iloc[-1]['trade_date']}, 开盘:{df.iloc[-1]['open']}, 收盘:{df.iloc[-1]['close']}, 最高:{df.iloc[-1]['high']}, 最低:{df.iloc[-1]['low']}")
