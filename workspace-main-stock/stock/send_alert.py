#!/usr/bin/env python3
"""发送预警通知到飞书"""
import os
import subprocess
from datetime import datetime

# 读取预警数据
alert_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-data.txt')
with open(alert_path, 'r') as f:
    lines = f.readlines()

# 读取接收者列表
receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
with open(receiver_path, 'r') as f:
    receivers = [line.strip() for line in f.readlines() if line.strip()]

# 构建预警消息 (表格格式)
# 根据 alert-template.md 格式
current_time = datetime.now().strftime('%H:%M')
update_time = datetime.now().strftime('%Y-%m-%d %H:%M')

# 构建表格消息
message_lines = [
    "⚠️ **股票预警通知**",
    "",
    f"更新时间：{update_time}",
    "",
    "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |",
    "|------|------|--------|--------|--------|------|"
]

# 添加预警数据 (跳过表头和分隔线)
for line in lines[2:]:
    line = line.strip()
    if not line:
        continue
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 6:
        code = parts[0]
        name = parts[1]
        price = parts[2]
        change_pct = parts[3]
        change_amt = parts[4]
        time_str = parts[5].split()[-1] if ' ' in parts[5] else parts[5]  # 只取 HH:MM:SS
        
        message_lines.append(f"| {code} | {name} | {price} | {change_pct} | {change_amt} | {time_str} |")

message_lines.extend([
    "",
    "⚙️ **预警规则**",
    "- 📉 下跌 > 3% → 触发",
    "- 📈 上涨 > 5% → 触发",
    "- 🟢 中国石油：涨幅 > 2% → 触发",
    "- 🔴 中国石油：跌幅 > 1% → 触发",
    "",
    "**【数据来源】**",
    "- 数据来源：Tushare Pro",
    f"- 更新时间：{update_time}"
])

alert_message = '\n'.join(message_lines)

print("预警消息内容:")
print(alert_message)
print("\n" + "="*60)

# 构建广播命令
# openclaw message broadcast --channel feishu --account stock --targets <user_id1> --targets <user_id2>... --message <xxx>
targets_args = []
for receiver in receivers:
    targets_args.extend(['--targets', receiver])

# 由于消息可能包含特殊字符，使用文件传递
msg_file = '/tmp/alert_message.txt'
with open(msg_file, 'w') as f:
    f.write(alert_message)

# 构建命令
cmd = ['openclaw', 'message', 'broadcast', '--channel', 'feishu', '--account', 'stock']
cmd.extend(targets_args)
cmd.extend(['--message', alert_message])

print(f"\n执行命令：{' '.join(cmd)}")

# 执行命令
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"返回码：{result.returncode}")
    print(f"输出：{result.stdout}")
    if result.stderr:
        print(f"错误：{result.stderr}")
except subprocess.TimeoutExpired:
    print("命令执行超时")
except Exception as e:
    print(f"执行失败：{e}")

# 返回消息内容用于日志
print("\n---MESSAGE_CONTENT---")
print(alert_message)
