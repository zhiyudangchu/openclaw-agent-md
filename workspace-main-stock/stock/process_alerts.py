#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理实时数据并检查预警规则，发送飞书通知
"""

import os
import sys
from datetime import datetime

def read_realtime_data():
    """读取实时数据文件"""
    data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    stocks = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 跳过表头
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    stock = {
                        'code': parts[0],
                        'name': parts[1],
                        'price': float(parts[2]),
                        'change': float(parts[3]),
                        'pct_chg': float(parts[4]),
                        'pre_close': float(parts[5]),
                        'time': parts[11] if len(parts) > 11 else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    stocks.append(stock)
                except (ValueError, IndexError) as e:
                    print(f"解析数据失败：{e}")
                    continue
    
    return stocks

def check_alert_rules(stock):
    """
    检查预警规则
    通用规则:
    1. 下跌 > 3% → 触发
    2. 上涨 > 5% → 触发
    
    个股专属规则:
    中国石油 (601857):
    - 涨幅 > 2% → 触发预警
    - 跌幅 > 1% → 触发预警
    """
    code = stock['code']
    pct_chg = stock['pct_chg']
    
    triggered = False
    rule = ""
    
    # 检查中国石油专属规则
    if code == '601857':
        if pct_chg > 2:
            triggered = True
            rule = f"🟢 专属规则：涨幅 {pct_chg:.2f}% > 2%"
        elif pct_chg < -1:
            triggered = True
            rule = f"🔴 专属规则：跌幅 {pct_chg:.2f}% < -1%"
    else:
        # 通用规则
        if pct_chg < -3:
            triggered = True
            rule = f"📉 通用规则：下跌 {pct_chg:.2f}% < -3%"
        elif pct_chg > 5:
            triggered = True
            rule = f"📈 通用规则：上涨 {pct_chg:.2f}% > 5%"
    
    if triggered:
        stock['rule'] = rule
        return stock
    
    return None

def generate_alert_message(alerts):
    """生成预警消息"""
    if not alerts:
        return None
    
    lines = []
    lines.append("🚨 股价预警通知")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    for alert in alerts[:10]:
        code = alert['code']
        name = alert['name']
        price = alert['price']
        pct_chg = alert['pct_chg']
        change = alert['change']
        time = alert['time'].split(' ')[1][:5] if ' ' in alert['time'] else alert['time'][:5]
        
        pct_str = f"+{pct_chg:.2f}%" if pct_chg > 0 else f"{pct_chg:.2f}%"
        change_str = f"+¥{change:.2f}" if change > 0 else f"¥{change:.2f}"
        
        lines.append(f"| {code} | {name} | ¥{price:.2f} | {pct_str} | {change_str} | {time} |")
    
    lines.append("")
    lines.append("⚙️ 预警规则")
    lines.append("• 📉 下跌 > 3% → 触发")
    lines.append("• 📈 上涨 > 5% → 触发")
    lines.append("• 中国石油专属：涨幅 > 2% 或 跌幅 > 1%")
    lines.append("")
    lines.append("【数据来源】")
    lines.append("数据来源：Tushare Pro")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def read_receiver_list():
    """读取接收者列表"""
    receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    receivers = []
    try:
        with open(receiver_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
    except FileNotFoundError:
        print(f"警告：接收者列表文件不存在：{receiver_path}")
    return receivers

if __name__ == '__main__':
    print("处理实时数据并检查预警规则...")
    
    # 读取实时数据
    stocks = read_realtime_data()
    print(f"读取到 {len(stocks)} 条数据")
    
    # 检查预警规则
    alerts = []
    for stock in stocks:
        alert = check_alert_rules(stock)
        if alert:
            alerts.append(alert)
            print(f"⚠️ {stock['code']} {stock['name']}: {stock['pct_chg']:.2f}% - {alert['rule']}")
    
    print(f"\n触发预警 {len(alerts)} 条")
    
    if alerts:
        # 生成预警消息
        message = generate_alert_message(alerts)
        print("\n预警消息:")
        print(message)
        
        # 读取接收者列表
        receivers = read_receiver_list()
        print(f"\n接收者数量：{len(receivers)}")
        
        if receivers:
            # 构建广播命令
            targets = ' '.join([f'--targets {r}' for r in receivers])
            # 转义消息中的特殊字符
            message_escaped = message.replace('"', '\\"').replace('\n', '\\n')
            
            cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{message_escaped}"'
            print(f"\n执行广播命令...")
            print(f"命令：{cmd}")
            
            # 执行广播命令
            exit_code = os.system(cmd)
            if exit_code == 0:
                print("✓ 预警已发送")
            else:
                print(f"✗ 发送失败，退出码：{exit_code}")
        else:
            print("警告：没有配置接收者")
    else:
        print("无触发预警的股票")
    
    print("\n任务完成")
