#!/usr/bin/env python3
"""获取自选股实时日线数据 (rt_k 接口)"""
import os
import tushare as ts
from datetime import datetime

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 读取自选股列表
stock_list_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/stock-list.txt')
with open(stock_list_path, 'r') as f:
    lines = f.readlines()

# 构建 ts_code 列表 (需要带.SZ/.SH/.BJ 后缀)
ts_codes = []
for line in lines:
    line = line.strip()
    # 跳过注释行和空行
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    if len(parts) < 3:
        continue
    code = parts[0]
    name = parts[1]
    market = parts[2]  # SH or SZ
    
    # 构建 ts_code
    if market == 'SH':
        ts_codes.append(f"{code}.SH")
    elif market == 'SZ':
        ts_codes.append(f"{code}.SZ")
    elif market == 'BJ':
        ts_codes.append(f"{code}.BJ")

# 批量获取实时日线数据 (rt_k 接口)
ts_code_str = ','.join(ts_codes)
print(f"获取实时日线数据：{ts_code_str}")

try:
    df = pro.rt_k(ts_code=ts_code_str)
    print(f"获取到 {len(df)} 条数据")
    print(df)
    
    # 保存到 realtime-data.txt
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 写入文件
    with open(output_path, 'w') as f:
        f.write(f"数据来源：Tushare Pro\n")
        f.write(f"数据时间：{current_time}\n")
        f.write("=" * 80 + "\n")
        f.write("代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 昨收 | 时间\n")
        f.write("-" * 80 + "\n")
        
        # 计算涨跌幅和涨跌额
        for idx, row in df.iterrows():
            ts_code = row['ts_code']
            name = row['name']
            close = row['close']  # 最新价
            pre_close = row['pre_close']  # 昨收价
            
            # 计算涨跌额和涨跌幅
            change = close - pre_close
            change_pct = (change / pre_close) * 100 if pre_close != 0 else 0
            
            # 格式化时间
            trade_time = row.get('trade_time', current_time)
            
            # 写入数据
            f.write(f"{ts_code} | {name} | ¥{close:.2f} | {change_pct:+.2f}% | ¥{change:+.2f} | ¥{pre_close:.2f} | {trade_time}\n")
    
    print(f"数据已保存到 {output_path}")
    
except Exception as e:
    print(f"获取数据失败：{e}")
    import traceback
    traceback.print_exc()
