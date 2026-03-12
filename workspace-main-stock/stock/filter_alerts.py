#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按照预警规则过滤实时数据
"""
import pandas as pd
from datetime import datetime

# 读取实时数据
data_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
df = pd.read_csv(data_path)

# 计算涨跌幅
df['pct_chg'] = ((df['close'] - df['pre_close']) / df['pre_close']) * 100

# 预警规则过滤
alert_records = []

for idx, row in df.iterrows():
    ts_code = row['ts_code']
    name = row['name']
    pct_chg = row['pct_chg']
    trigger_reason = []
    
    # 中国石油专属规则
    if ts_code == '601857.SH':
        if pct_chg > 2:
            trigger_reason.append('🟢 涨幅 > 2%')
        elif pct_chg < -1:
            trigger_reason.append('🔴 跌幅 > 1%')
    else:
        # 通用规则
        if pct_chg > 1:
            trigger_reason.append('📈 上涨 > 1%')
        elif pct_chg < -1:
            trigger_reason.append('📉 下跌 > 1%')
    
    if trigger_reason:
        alert_records.append({
            'ts_code': ts_code,
            'name': name,
            'close': row['close'],
            'pct_chg': pct_chg,
            'change_amt': row['close'] - row['pre_close'],
            'pre_close': row['pre_close'],
            'trigger_reason': ','.join(trigger_reason)
        })

# 转换为 DataFrame 并按涨跌幅排序
if alert_records:
    alert_df = pd.DataFrame(alert_records)
    alert_df = alert_df.sort_values('pct_chg', ascending=False)
    
    print(f"=== 触发预警的股票：{len(alert_df)} 只 ===\n")
    print(alert_df.to_string(index=False))
    
    # 保存过滤后的数据
    output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/alert-data.txt'
    alert_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n预警数据已保存到：{output_path}")
else:
    print("没有触发预警的股票")
    
# 输出 JSON 格式供后续使用
import json
print("\n=== JSON 格式 ===")
print(json.dumps(alert_records, ensure_ascii=False, indent=2))
