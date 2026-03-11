#!/usr/bin/env python3
"""获取自选股实时日线数据 (rt_k 接口)"""
import os
import tushare as ts
from datetime import datetime

# 初始化 pro 接口
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 读取自选股列表
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
with open(watchlist_path, 'r') as f:
    lines = f.readlines()

# 构建 ts_code 列表 (需要带.SZ/.SH/.BJ 后缀)
ts_codes = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    parts = line.split('|')
    code = parts[0]
    name = parts[1] if len(parts) > 1 else ''
    
    # 如果已经有后缀，直接使用；否则根据代码判断
    if '.SH' in code or '.SZ' in code or '.BJ' in code or '.HK' in code:
        ts_codes.append(code)
    else:
        # A 股代码判断
        if code.startswith('6'):
            ts_codes.append(f"{code}.SH")
        elif code.startswith('0') or code.startswith('3'):
            ts_codes.append(f"{code}.SZ")
        elif code.startswith('9'):
            ts_codes.append(f"{code}.BJ")
        else:
            # 美股等其他市场
            ts_codes.append(code)

# 批量获取实时日线数据 (rt_k 接口)
# 注意：rt_k 接口支持多个代码，用逗号分隔
ts_code_str = ','.join(ts_codes)
print(f"获取实时日线数据：{ts_code_str}")

try:
    df = pro.rt_k(ts_code=ts_code_str)
    print(f"获取到 {len(df)} 条数据")
    print(df)
    
    # 保存到 realtime-data.txt
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    
    # 写入表头
    with open(output_path, 'w') as f:
        f.write("代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 昨收 | 时间\n")
        f.write("-" * 60 + "\n")
        
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
            trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 写入数据
            f.write(f"{ts_code} | {name} | ¥{close:.2f} | {change_pct:+.2f}% | ¥{change:+.2f} | ¥{pre_close:.2f} | {trade_time}\n")
    
    print(f"数据已保存到 {output_path}")
    
except Exception as e:
    print(f"获取数据失败：{e}")
    # 尝试单个股票获取
    print("尝试单个股票获取...")
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    with open(output_path, 'w') as f:
        f.write("代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 昨收 | 时间\n")
        f.write("-" * 60 + "\n")
        
        for ts_code in ts_codes:
            try:
                df_single = pro.rt_k(ts_code=ts_code)
                if not df_single.empty:
                    row = df_single.iloc[0]
                    close = row['close']
                    pre_close = row['pre_close']
                    change = close - pre_close
                    change_pct = (change / pre_close) * 100 if pre_close != 0 else 0
                    trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    f.write(f"{ts_code} | {row['name']} | ¥{close:.2f} | {change_pct:+.2f}% | ¥{change:+.2f} | ¥{pre_close:.2f} | {trade_time}\n")
                    print(f"获取 {ts_code} 成功")
            except Exception as e2:
                print(f"获取 {ts_code} 失败：{e2}")
    
    print(f"数据已保存到 {output_path}")
