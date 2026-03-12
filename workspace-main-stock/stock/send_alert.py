#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成预警消息并推送
"""
import json
import subprocess
import sys
from datetime import datetime

# 读取过滤后的预警数据（alert-data.txt）
with open('alert-data.txt', 'r', encoding='utf-8') as f:
    data = json.load(f)

if data.get('status') != 'success':
    print("No valid data")
    sys.exit(0)

alert_data = data.get('data', [])
update_time = data.get('update_time', '')

if len(alert_data) == 0:
    print("No alerts to send")
    sys.exit(0)

# 读取接收者列表
with open('receiver-list.txt', 'r', encoding='utf-8') as f:
    receivers = [line.strip() for line in f if line.strip()]

# 构建消息内容（按 alert-template.md 格式）
message_lines = []
message_lines.append("🚨 **股票预警通知**")
message_lines.append("")
message_lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
message_lines.append("|------|------|--------|--------|-------|------|")

# 添加数据行（已按涨跌幅绝对值排序）
for stock in alert_data:
    ts_code = stock.get('ts_code', '')
    name = stock.get('name', '')
    close = stock.get('close', 0)
    pct_change = stock.get('pct_change', 0)
    change_amount = stock.get('change_amount', 0)
    trade_time = stock.get('trade_time', '')
    
    # 格式化时间（只显示时分）
    time_str = trade_time.split(' ')[-1][:5] if ' ' in trade_time else trade_time[:5]
    
    # 格式化涨跌幅（带符号）
    if pct_change > 0:
        pct_str = f"+{pct_change:.2f}%"
    else:
        pct_str = f"{pct_change:.2f}%"
    
    # 格式化涨跌额
    if change_amount > 0:
        amount_str = f"¥{change_amount:.2f}"
    else:
        amount_str = f"¥{change_amount:.2f}"
    
    # 添加涨跌符号
    if pct_change > 0:
        symbol = "📈"
    else:
        symbol = "📉"
    
    message_lines.append(f"| {ts_code.split('.')[0]} | {symbol} {name} | ¥{close:.2f} | {pct_str} | {amount_str} | {time_str} |")

message_lines.append("")
message_lines.append("⚙️ **预警规则**")
message_lines.append("- 📉 下跌 > 1% → 触发")
message_lines.append("- 📈 上涨 > 1% → 触发")
message_lines.append("- 🟢 中国石油：涨幅 > 2% 或 跌幅 > 1% → 触发")
message_lines.append("")
message_lines.append(f"**数据来源**：Tushare Pro")
message_lines.append(f"**更新时间**：{update_time}")

message = "\n".join(message_lines)

# 构建命令
targets_args = []
for receiver in receivers:
    targets_args.extend(["--targets", receiver])

cmd = [
    "openclaw", "message", "broadcast",
    "--channel", "feishu",
    "--account", "stock",
    "--message", message
] + targets_args

print(f"Executing: {' '.join(cmd)}")
print(f"Receivers: {len(receivers)}")
print(f"Alert count: {len(alert_data)}")

# 执行命令
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error: {e}")
