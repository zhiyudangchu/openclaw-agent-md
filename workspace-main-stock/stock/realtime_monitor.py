#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
- 获取自选股实时日线数据
- 根据预警规则过滤
- 输出预警数据
"""

import os
import tushare as ts
from datetime import datetime

# 读取 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表
stocks = [
    {"ts_code": "601857.SH", "name": "中国石油", "rule_up": 2.0, "rule_down": 1.0},
    {"ts_code": "603606.SH", "name": "东方电缆", "rule_up": 1.0, "rule_down": 1.0},
    {"ts_code": "002600.SZ", "name": "领益智造", "rule_up": 1.0, "rule_down": 1.0},
    {"ts_code": "002961.SZ", "name": "瑞达期货", "rule_up": 1.0, "rule_down": 1.0},
    {"ts_code": "001872.SZ", "name": "招商港口", "rule_up": 1.0, "rule_down": 1.0},
]

# 构建 ts_code 字符串
ts_codes = ",".join([s["ts_code"] for s in stocks])

print(f"获取实时数据：{ts_codes}")
print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 获取实时日线数据
try:
    df = pro.rt_k(ts_code=ts_codes)
    print(f"获取到 {len(df)} 条数据")
    print(df)
except Exception as e:
    print(f"获取数据失败：{e}")
    exit(1)

# 检查是否有数据
if df is None or len(df) == 0:
    print("未获取到数据，可能已休市")
    exit(0)

# 计算涨跌幅
df['pct_chg'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
df['change'] = (df['close'] - df['pre_close']).round(2)

# 预警规则过滤
alert_data = []
for _, row in df.iterrows():
    ts_code = row['ts_code']
    pct_chg = row['pct_chg']
    
    # 查找对应股票的专属规则
    stock_rule = None
    for s in stocks:
        if s["ts_code"] == ts_code:
            stock_rule = s
            break
    
    if not stock_rule:
        continue
    
    # 判断是否触发预警
    triggered = False
    if pct_chg > stock_rule["rule_up"]:
        triggered = True
    elif pct_chg < -stock_rule["rule_down"]:
        triggered = True
    
    if triggered:
        alert_data.append({
            "ts_code": row['ts_code'],
            "name": row['name'],
            "close": row['close'],
            "pct_chg": pct_chg,
            "change": row['change'],
            "trade_time": row.get('trade_time', datetime.now().strftime('%H:%M'))
        })

# 按涨跌幅排序
alert_data.sort(key=lambda x: abs(x['pct_chg']), reverse=True)

print(f"\n触发预警的股票数量：{len(alert_data)}")

# 输出到文件
output_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    if alert_data:
        f.write("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |\n")
        f.write("|------|------|--------|--------|--------|------|\n")
        for item in alert_data:
            time_str = item['trade_time'] if item['trade_time'] else datetime.now().strftime('%H:%M')
            # 处理时间字符串，只保留 HH:MM
            if len(time_str) > 5:
                time_str = time_str[:5]
            f.write(f"| {item['ts_code'].split('.')[0]} | {item['name']} | ¥{item['close']:.2f} | {item['pct_chg']:+.2f}% | ¥{item['change']:+.2f} | {time_str} |\n")
        f.write(f"\n**数据来源：** tushare rt_k 接口\n")
        f.write(f"**更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    else:
        f.write("无预警数据\n")

print(f"数据已写入：{output_file}")

# 输出 JSON 格式供后续使用
import json
print("\n=== JSON 输出 ===")
print(json.dumps(alert_data, ensure_ascii=False, indent=2))
