#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
获取自选股实时日线数据，检查是否满足预警条件
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

# 自选股列表
stocks = [
    "603606.SH",  # 东方电缆
    "002600.SZ",  # 领益智造
    "002961.SZ",  # 瑞达期货
    "001872.SZ",  # 招商港口
]

# 获取实时日线数据
print(f"获取实时日线数据... 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
ts_code_str = ",".join(stocks)
print(f"请求参数：ts_code={ts_code_str}")

try:
    df = pro.rt_k(ts_code=ts_code_str)
    print(f"接口返回数据行数：{len(df)}")
    print(f"数据列：{list(df.columns)}")
    print("\n原始数据:")
    print(df.to_string())
except Exception as e:
    print(f"获取数据失败：{e}")
    sys.exit(1)

# 检查是否有数据
if df is None or len(df) == 0:
    print("未获取到数据，可能市场休市")
    sys.exit(0)

# 计算涨跌幅
df['pct_chg'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
df['change'] = (df['close'] - df['pre_close']).round(2)

# 预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
# 个股专属规则：无（自选股中没有 601857.SH 中国石油）

alert_records = []

for idx, row in df.iterrows():
    ts_code = row['ts_code']
    name = row['name']
    close = row['close']
    pre_close = row['pre_close']
    pct_chg = row['pct_chg']
    change = row['change']
    trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 检查预警条件
    triggered = False
    reason = ""
    
    # 通用规则
    if pct_chg < -3:
        triggered = True
        reason = f"下跌 {pct_chg:.2f}% > 3%"
    elif pct_chg > 5:
        triggered = True
        reason = f"上涨 {pct_chg:.2f}% > 5%"
    
    if triggered:
        alert_records.append({
            'ts_code': ts_code,
            'name': name,
            'close': close,
            'pct_chg': pct_chg,
            'change': change,
            'trade_time': trade_time,
            'reason': reason
        })
        print(f"\n⚠️ 预警触发：{name} ({ts_code}) - {reason}")

# 输出结果
print(f"\n===== 预警结果 =====")
print(f"检查股票数：{len(df)}")
print(f"触发预警数：{len(alert_records)}")

if alert_records:
    print("\n预警详情:")
    for rec in alert_records:
        print(f"  {rec['ts_code']} {rec['name']}: 当前价={rec['close']:.2f}, 涨跌幅={rec['pct_chg']:.2f}%, 涨跌额={rec['change']:.2f}, 原因={rec['reason']}")
else:
    print("无满足预警条件的股票")

# 保存实时数据到文件
output_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"# 实时数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# 数据源：Tushare Pro\n\n")
    
    if len(df) > 0:
        # 写入表头
        f.write("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |\n")
        f.write("|------|------|--------|--------|--------|------|\n")
        
        # 写入数据
        for idx, row in df.iterrows():
            ts_code = row['ts_code']
            name = row['name']
            close = row['close']
            pct_chg = row['pct_chg']
            change = row['change']
            time_str = datetime.now().strftime('%H:%M')
            
            # 格式化涨跌幅显示
            if pct_chg > 0:
                pct_str = f"+{pct_chg:.2f}%"
            else:
                pct_str = f"{pct_chg:.2f}%"
            
            f.write(f"| {ts_code.split('.')[0]} | {name} | ¥{close:.2f} | {pct_str} | ¥{change:.2f} | {time_str} |\n")
    
    # 写入预警数据
    if alert_records:
        f.write(f"\n## ⚠️ 预警股票 ({len(alert_records)}只)\n\n")
        for rec in alert_records:
            ts_code_short = rec['ts_code'].split('.')[0]
            if rec['pct_chg'] > 0:
                pct_str = f"+{rec['pct_chg']:.2f}%"
            else:
                pct_str = f"{rec['pct_chg']:.2f}%"
            f.write(f"- **{ts_code_short} {rec['name']}**: ¥{rec['close']:.2f} ({pct_str}), {rec['reason']}\n")

print(f"\n数据已保存到：{output_file}")

# 输出预警数据 JSON 格式，用于后续推送
if alert_records:
    print("\n===== 预警数据(JSON) =====")
    import json
    print(json.dumps(alert_records, ensure_ascii=False, indent=2))
