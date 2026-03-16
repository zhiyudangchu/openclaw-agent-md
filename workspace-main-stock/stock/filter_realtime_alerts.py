#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤实时数据，检查是否触发预警规则
"""

import os
import pandas as pd
from datetime import datetime

# 读取实时数据
input_file = os.path.join(os.path.dirname(__file__), 'realtime-data.txt')
output_file = os.path.join(os.path.dirname(__file__), 'alert-data.txt')

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found")
    exit(1)

df = pd.read_csv(input_file)

if df.empty:
    print("实时数据为空")
    exit(0)

print(f"读取到 {len(df)} 条实时数据")
print("\n原始数据:")
print(df.to_string())

# 计算涨跌幅
df['pct_change'] = ((df['close'] - df['pre_close']) / df['pre_close']) * 100

# 预警规则（根据 alert-rules.md 中的注释规则）
# 状态：已关闭，但保留逻辑供参考
# 通用规则：
# - 下跌 > 1% → 触发
# - 上涨 > 1% → 触发
# 个股专属规则：
# 1. 中国石油 (601857.SH):
#    - 涨幅 > 2% → 触发预警
#    - 跌幅 > 1% → 触发预警

alert_rules = {
    'general': {
        'down': -1.0,   # 下跌 > 1%
        'up': 1.0       # 上涨 > 1%
    },
    'stocks': {
        '601857.SH': {
            'down': -1.0,  # 跌幅 > 1%
            'up': 2.0      # 涨幅 > 2%
        }
    }
}

# 规则状态
RULES_ENABLED = False  # 预警规则状态：已关闭

alert_data = []

for idx, row in df.iterrows():
    ts_code = row['ts_code']
    pct = row['pct_change']
    name = row['name']
    
    triggered = False
    reason = ""
    
    if RULES_ENABLED:
        # 检查个股专属规则
        if ts_code in alert_rules['stocks']:
            rule = alert_rules['stocks'][ts_code]
            if pct > rule['up']:
                triggered = True
                reason = f"涨幅 {pct:.2f}% > {rule['up']}%"
            elif pct < rule['down']:
                triggered = True
                reason = f"跌幅 {pct:.2f}% < {rule['down']}%"
        else:
            # 检查通用规则
            if pct > alert_rules['general']['up']:
                triggered = True
                reason = f"涨幅 {pct:.2f}% > {alert_rules['general']['up']}%"
            elif pct < alert_rules['general']['down']:
                triggered = True
                reason = f"跌幅 {pct:.2f}% < {alert_rules['general']['down']}%"
    
    if triggered:
        alert_data.append({
            'ts_code': ts_code,
            'name': name,
            'close': row['close'],
            'pct_change': pct,
            'change_amount': row['close'] - row['pre_close'],
            'reason': reason
        })
        print(f"\n⚠️ 预警触发：{ts_code} {name} - {reason}")

# 保存预警数据
if alert_data:
    alert_df = pd.DataFrame(alert_data)
    alert_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n预警数据已保存到：{output_file}")
    print(f"共 {len(alert_data)} 条预警数据")
else:
    print("\n✅ 无触发预警的数据")
    # 创建空文件标记已执行
    with open(output_file, 'w') as f:
        f.write("")

print("\n" + "="*50)
print("数据详情:")
for idx, row in df.iterrows():
    pct = ((row['close'] - row['pre_close']) / row['pre_close']) * 100
    print(f"{row['ts_code']} {row['name']}: {row['close']:.2f} ({pct:+.2f}%)")
