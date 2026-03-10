#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据预警规则过滤实时数据，生成预警通知
"""
import os
import sys
from datetime import datetime

# 预警规则
# 通用规则：
# - 下跌 > 3% → 触发
# - 上涨 > 5% → 触发
# 中国石油 (601857) 专属规则：
# - 涨幅 > 2% → 触发
# - 跌幅 > 1% → 触发

def check_alert(code, name, change_pct):
    """检查是否触发预警"""
    # 中国石油专属规则
    if code == '601857' or name == '中国石油':
        if change_pct > 2:
            return True, '🟢 涨幅 > 2%'
        elif change_pct < -1:
            return True, '🔴 跌幅 > 1%'
    else:
        # 通用规则
        if change_pct < -3:
            return True, '📉 下跌 > 3%'
        elif change_pct > 5:
            return True, '📈 上涨 > 5%'
    
    return False, None

# 读取实时数据
data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
alerts = []

try:
    with open(data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        print("数据文件为空或格式错误")
        sys.exit(0)
    
    # 解析数据（跳过表头）
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        
        # 使用 | 分隔符解析
        parts = line.split('|')
        if len(parts) < 6:
            print(f"跳过格式错误的行：{line}")
            continue
        
        code = parts[0].strip()
        name = parts[1].strip()
        price_str = parts[2].strip().replace('¥', '')
        change_pct_str = parts[3].strip().replace('%', '')
        change_amt_str = parts[4].strip().replace('¥', '')
        time_str = parts[5].strip()
        
        try:
            price = float(price_str)
            change_pct = float(change_pct_str)
            change_amt = float(change_amt_str)
        except ValueError as e:
            print(f"解析数值出错：{e}, 行：{line}")
            continue
        
        # 检查是否触发预警
        triggered, rule = check_alert(code, name, change_pct)
        if triggered:
            alerts.append({
                'code': code,
                'name': name,
                'price': price,
                'change_amt': change_amt,
                'change_pct': change_pct,
                'time': time_str,
                'rule': rule
            })
            print(f"⚠️ {code} {name}: ¥{price:.2f} ({change_pct:+.2f}%) - {rule}")
    
    print(f"\n共触发 {len(alerts)} 条预警")
    
    if not alerts:
        print("无预警信息，结束任务")
        sys.exit(0)
    
    # 按涨跌幅排序（绝对值大的在前）
    alerts.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    
    # 生成预警消息（表格格式）
    message_lines = [
        "⚠️ 股价预警通知",
        "",
        "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 |",
        "|------|------|--------|--------|-------|"
    ]
    
    for alert in alerts:
        sign = '+' if alert['change_pct'] > 0 else ''
        amt_sign = '+' if alert['change_amt'] > 0 else ''
        message_lines.append(
            f"| {alert['code']} | {alert['name']} | ¥{alert['price']:.2f} | {sign}{alert['change_pct']:.2f}% | {amt_sign}{alert['change_amt']:.2f} |"
        )
    
    message_lines.extend([
        "",
        "⚙️ 预警规则",
        "• 📉 下跌 > 3% → 触发",
        "• 📈 上涨 > 5% → 触发",
        "• 中国石油专属：🟢 涨幅 > 2% | 🔴 跌幅 > 1%",
        "",
        f"📊 数据时间：{alerts[0]['time']}"
    ])
    
    message = '\n'.join(message_lines)
    
    # 保存预警消息
    alert_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-message.txt')
    with open(alert_path, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"\n预警消息已保存到：{alert_path}")
    print("\n" + message)
    
    # 读取接收者列表并推送
    receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    receivers = []
    with open(receiver_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    
    if receivers:
        print(f"\n接收者数量：{len(receivers)}")
        # 构建命令
        targets = ' '.join([f'--targets {r}' for r in receivers])
        cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{message}"'
        print(f"\n推送命令：{cmd}")
        # 执行推送
        os.system(cmd)
    
except Exception as e:
    print(f"处理数据出错：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
