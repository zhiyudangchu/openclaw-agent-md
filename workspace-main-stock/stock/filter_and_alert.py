#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据预警规则过滤股票数据并生成预警消息
"""

import os
from datetime import datetime

# 预警规则
# 通用规则：
# 1. 下跌 > 3% → 触发
# 2. 上涨 > 5% → 触发
# 
# 个股专属规则：
# 中国石油 (601857.SH):
# - 涨幅 > 2% → 触发预警
# - 跌幅 > 1% → 触发预警

def check_alert(ts_code, name, pct_chg):
    """检查是否触发预警"""
    # 提取纯代码（去掉市场后缀）
    code = ts_code.split('.')[0] if '.' in ts_code else ts_code
    
    # 中国石油专属规则
    if code == '601857':
        if pct_chg > 2.0:  # 涨幅 > 2%
            return True, f"🟢 专属规则：涨幅 {pct_chg:.2f}% > 2%"
        elif pct_chg < -1.0:  # 跌幅 > 1%
            return True, f"🔴 专属规则：跌幅 {abs(pct_chg):.2f}% > 1%"
    else:
        # 通用规则
        if pct_chg > 5.0:  # 上涨 > 5%
            return True, f"📈 通用规则：涨幅 {pct_chg:.2f}% > 5%"
        elif pct_chg < -3.0:  # 下跌 > 3%
            return True, f"📉 通用规则：跌幅 {abs(pct_chg):.2f}% > 3%"
    
    return False, None

# 读取实时数据
data_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
stocks_data = []

with open(data_path, 'r', encoding='utf-8') as f:
    header = f.readline().strip().split('|')
    for line in f:
        line = line.strip()
        if line:
            parts = line.split('|')
            if len(parts) >= 10:
                stock = {
                    'ts_code': parts[0],
                    'name': parts[1],
                    'trade_date': parts[2],
                    'open': float(parts[3]) / 100 if parts[3] else 0,
                    'high': float(parts[4]) / 100 if parts[4] else 0,
                    'low': float(parts[5]) / 100 if parts[5] else 0,
                    'close': float(parts[6]) / 100 if parts[6] else 0,
                    'pre_close': float(parts[7]) / 100 if parts[7] else 0,
                    'change': float(parts[8]) / 100 if parts[8] else 0,
                    'pct_chg': float(parts[9]) if parts[9] else 0,
                    'vol': float(parts[10]) if parts[10] else 0,
                    'amount': float(parts[11]) / 100000000 if len(parts) > 11 and parts[11] else 0  # 转换为亿
                }
                stocks_data.append(stock)

print(f"读取到 {len(stocks_data)} 条股票数据")

# 过滤预警数据
alert_stocks = []
for stock in stocks_data:
    is_alert, reason = check_alert(stock['ts_code'], stock['name'], stock['pct_chg'])
    if is_alert:
        stock['alert_reason'] = reason
        alert_stocks.append(stock)
        print(f"预警：{stock['name']} ({stock['ts_code']}) - {stock['pct_chg']:.2f}% - {reason}")

print(f"\n共 {len(alert_stocks)} 只股票触发预警")

# 按涨跌幅排序
alert_stocks.sort(key=lambda x: x['pct_chg'], reverse=True)

# 生成预警消息
if alert_stocks:
    # 读取接收者列表
    receiver_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/receiver-list.txt'
    receivers = []
    with open(receiver_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    
    print(f"接收者数量：{len(receivers)}")
    
    # 生成消息内容
    current_time = datetime.now().strftime('%H:%M')
    trade_date = alert_stocks[0]['trade_date'] if alert_stocks else ''
    
    # 构建表格消息（飞书支持 markdown）
    message_lines = []
    message_lines.append(f"⚠️ **股票预警通知** - {trade_date} {current_time}\n")
    message_lines.append(f"共 {len(alert_stocks)} 只股票触发预警条件\n")
    message_lines.append("")
    message_lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    message_lines.append("|------|------|--------|--------|-------|------|")
    
    for stock in alert_stocks[:10]:  # 最多显示 10 条
        price_str = f"¥{stock['close']:.2f}"
        change_str = f"+{stock['pct_chg']:.2f}%" if stock['pct_chg'] > 0 else f"{stock['pct_chg']:.2f}%"
        change_amt_str = f"+¥{stock['change']:.2f}" if stock['change'] > 0 else f"¥{stock['change']:.2f}"
        message_lines.append(f"| {stock['ts_code'].split('.')[0]} | {stock['name']} | {price_str} | {change_str} | {change_amt_str} | {current_time} |")
    
    message_lines.append("")
    message_lines.append("⚙️ **预警规则**")
    message_lines.append("• 📉 下跌 > 3% → 触发")
    message_lines.append("• 📈 上涨 > 5% → 触发")
    message_lines.append("• 🟢 中国石油：涨幅 > 2% 或 跌幅 > 1% → 触发")
    
    message = '\n'.join(message_lines)
    
    # 保存消息到文件
    msg_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/alert-message.txt'
    with open(msg_path, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"\n预警消息已保存到 {msg_path}")
    print("\n--- 预警消息内容 ---")
    print(message)
    
    # 构建命令
    targets_str = ' '.join([f"--targets {r}" for r in receivers])
    command = f"openclaw message broadcast --channel feishu --account stock {targets_str} --message \"{message.replace('"', "'").replace('\n', '\\n')}\""
    
    print("\n--- 执行命令 ---")
    print(command)
    
    # 保存命令到文件
    cmd_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/send-alert-cmd.sh'
    with open(cmd_path, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n")
        f.write(command)
    
else:
    print("\n没有股票触发预警，任务结束")
