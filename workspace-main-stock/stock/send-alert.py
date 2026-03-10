#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成预警消息并推送
"""
from datetime import datetime
import subprocess

# 读取预警数据
alert_path = '/home/openclaw/workspace-main-stock/stock/alert-data.txt'
with open(alert_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 解析预警数据
alerts = []
for line in lines:
    line = line.strip()
    if line.startswith('#') or not line or line.startswith('code|'):
        continue
    
    parts = line.split('|')
    if len(parts) >= 6:
        alerts.append({
            'code': parts[0],
            'name': parts[1],
            'price': parts[2],
            'change_percent': parts[3],
            'change_amount': parts[4],
            'reason': parts[5]
        })

# 读取接收者列表
receiver_path = '/home/openclaw/workspace-main-stock/stock/receiver-list.txt'
with open(receiver_path, 'r', encoding='utf-8') as f:
    receivers = [line.strip() for line in f.readlines() if line.strip()]

print(f"接收者数量：{len(receivers)}")
print(f"预警股票数量：{len(alerts)}")

# 构建消息内容（按照 alert-template.md 格式）
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 构建表格头部
message = f"⚠️ **股价预警通知**\n\n"
message += f"📊 更新时间：{timestamp}\n\n"
message += f"**预警股票明细**（共 {len(alerts)} 只）\n\n"

# 构建表格（Markdown 格式，但 WhatsApp/Telegram 不支持，使用文本格式）
# 按照 alert-template.md 的表格形式
message += "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 预警原因 |\n"
message += "|------|------|--------|--------|--------|----------|\n"

for alert in alerts:
    message += f"| {alert['code']} | {alert['name']} | ¥{alert['price']} | {alert['change_percent']} | ¥{alert['change_amount']} | {alert['reason']} |\n"

message += f"\n⚙️ **预警规则**\n"
message += "• 📉 下跌 > 3% → 触发\n"
message += "• 📈 上涨 > 5% → 触发\n"
message += "• 中国石油：涨幅>2% 或 跌幅>1% → 触发\n"

print("\n=== 消息内容 ===")
print(message)

# 构建命令
# openclaw message broadcast --channel feishu --account stock --targets <user_id1> --targets <user_id2>... --message <xxx>
targets_args = []
for receiver in receivers:
    targets_args.extend(['--targets', receiver])

# 由于消息包含特殊字符，使用临时文件方式
import tempfile
import os

# 将消息写入临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write(message)
    temp_file = f.name

try:
    # 读取消息内容
    with open(temp_file, 'r', encoding='utf-8') as f:
        msg_content = f.read()
    
    # 构建命令参数
    cmd = ['openclaw', 'message', 'broadcast', '--channel', 'feishu', '--account', 'stock']
    cmd.extend(targets_args)
    cmd.extend(['--message', msg_content])
    
    print("\n=== 执行命令 ===")
    print(' '.join(cmd))
    
    # 执行命令
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    print("\n=== 执行结果 ===")
    print(f"返回码：{result.returncode}")
    print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
        
finally:
    # 清理临时文件
    os.unlink(temp_file)
