#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据
"""
import os
import sys
import tushare as ts
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表（从 stock-list.txt 读取）
stock_list_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/stock-list.txt'
stocks = []
with open(stock_list_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 3:
                code = parts[0]
                name = parts[1]
                board = parts[2]
                # 转换为 ts_code 格式
                if board == 'SH':
                    ts_code = f"{code}.SH"
                elif board == 'SZ':
                    ts_code = f"{code}.SZ"
                else:
                    ts_code = f"{code}.{board}"
                stocks.append(ts_code)

if not stocks:
    print("错误：自选股列表为空")
    sys.exit(1)

# 构建 ts_code 参数（支持批量）
ts_codes = ','.join(stocks)
print(f"获取股票：{ts_codes}")

try:
    # 调用 rt_k 接口获取实时日线数据
    df = pro.rt_k(ts_code=ts_codes)
    
    if df is None or df.empty:
        print("错误：未获取到数据")
        sys.exit(1)
    
    # 输出数据（用于后续处理）
    print("\n=== 实时日线数据 ===")
    print(df.to_string(index=False))
    
    # 保存到文件
    output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n数据已保存到：{output_path}")
    print(f"共获取 {len(df)} 条记录")
    
except Exception as e:
    print(f"错误：{str(e)}")
    sys.exit(1)
