#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据预警规则过滤实时数据
"""
import json
from datetime import datetime
import os

# 使用绝对路径
base_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock')

# 读取实时数据
with open(os.path.join(base_path, 'realtime-data.txt'), 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['data']['items']
update_time = data['data']['update_time']

# 预警规则
# 通用规则：下跌 > 1% 或 上涨 > 1%
# 中国石油专属：涨幅 > 2% 或 跌幅 > 1%

alerts = []

for item in items:
    ts_code = item['ts_code']
    name = item['name']
    pct_chg = item['pct_chg']
    close = item['close']
    change = item['change']
    
    triggered = False
    reason = ""
    
    # 检查是否是中国石油
    if ts_code == "601857.SH":
        # 中国石油专属规则
        if pct_chg > 2:
            triggered = True
            reason = "🟢 涨幅 > 2%"
        elif pct_chg < -1:
            triggered = True
            reason = "🔴 跌幅 > 1%"
    else:
        # 通用规则
        if pct_chg > 1:
            triggered = True
            reason = "📈 上涨 > 1%"
        elif pct_chg < -1:
            triggered = True
            reason = "📉 下跌 > 1%"
    
    if triggered:
        alerts.append({
            "ts_code": ts_code,
            "name": name,
            "close": close,
            "pct_chg": pct_chg,
            "change": change,
            "reason": reason
        })

# 按涨跌幅绝对值排序
alerts.sort(key=lambda x: abs(x['pct_chg']), reverse=True)

# 输出结果
print(f"共检测到 {len(alerts)} 条预警信息")
print(json.dumps(alerts, ensure_ascii=False, indent=2))

# 生成飞书消息
if alerts:
    # 构建表格消息
    current_time = datetime.now().strftime("%H:%M")
    
    message_lines = []
    message_lines.append("🔔 **股价预警通知**\n")
    message_lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 | 触发原因 |")
    message_lines.append("|------|------|--------|--------|--------|------|----------|")
    
    for alert in alerts:
        pct_str = f"+{alert['pct_chg']:.2f}%" if alert['pct_chg'] > 0 else f"{alert['pct_chg']:.2f}%"
        change_str = f"+¥{alert['change']:.2f}" if alert['change'] > 0 else f"¥{alert['change']:.2f}"
        message_lines.append(f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | ¥{alert['close']:.2f} | {pct_str} | {change_str} | {current_time} | {alert['reason']} |")
    
    message_lines.append("\n⚙️ **预警规则**")
    message_lines.append("- 📉 下跌 > 1% → 触发")
    message_lines.append("- 📈 上涨 > 1% → 触发")
    message_lines.append("- 🟢 中国石油涨幅 > 2% → 触发")
    message_lines.append("- 🔴 中国石油跌幅 > 1% → 触发")
    message_lines.append(f"\n**数据来源**: Tushare Pro")
    message_lines.append(f"**更新时间**: {update_time}")
    
    message = "\n".join(message_lines)
    print("\n=== 飞书消息 ===")
    print(message)
    
    # 保存消息到文件
    with open(os.path.join(base_path, 'alert-message.txt'), 'w', encoding='utf-8') as f:
        f.write(message)
