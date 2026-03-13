import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 自选股列表 (ts_code 格式)
stocks = ['601857.SH', '603606.SH', '002600.SZ', '002961.SZ', '001872.SZ']
ts_codes = ','.join(stocks)

# 获取实时日线数据
df = pro.rt_k(ts_code=ts_codes)

# 格式化输出
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# 添加时间戳
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 保存数据到文件
output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"数据获取时间：{current_time}\n")
    f.write(f"接口：rt_k\n")
    f.write(f"参数：ts_code={ts_codes}\n\n")
    f.write(df.to_csv(index=False, sep='|'))

print("数据获取成功！")
print(f"记录数：{len(df)}")
print("\n数据预览：")
print(df[['ts_code', 'name', 'close', 'pre_close']].to_string(index=False))
