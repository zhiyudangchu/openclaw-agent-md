import os
import tushare as ts
import pandas as pd

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 自选股列表 (从 stock-list.txt 读取)
stocks = [
    '601857.SH',  # 中国石油
    '603606.SH',  # 东方电缆
    '002600.SZ',  # 领益智造
    '002961.SZ',  # 瑞达期货
    '001872.SZ',  # 招商港口
]

# 拼接 ts_code 参数
ts_code = ','.join(stocks)

# 获取实时日线数据
df = pro.rt_k(ts_code=ts_code)

# 保存数据到文件
df.to_csv('/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt', index=False, sep='\t')

print("数据获取成功!")
print(df)
