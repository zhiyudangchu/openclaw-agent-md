#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成预警消息并发送
"""
import json
from datetime import datetime

def format_alert_message(alerts):
    """
    按照 alert-template.md 格式生成预警消息
    """
    # 表格头部
    lines = []
    lines.append("🚨 **股票预警通知**\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    # 每条预警数据
    for stock in alerts:
        change_symbol = "+" if stock['change_percent'] >= 0 else ""
        time_str = stock['timestamp'].split(' ')[1][:5]  # HH:mm
        
        lines.append(
            f"| {stock['code']} | {stock['name']} | "
            f"¥{stock['close']:.2f} | {change_symbol}{stock['change_percent']:.2f}% | "
            f"{change_symbol}{stock['change_amount']:.2f} | {time_str} |"
        )
    
    lines.append("")
    lines.append("⚙️ **预警规则**")
    lines.append("• 📉 下跌 > 3% → 触发")
    lines.append("• 📈 上涨 > 5% → 触发")
    lines.append("• 🟡 中国石油专属：涨幅 > 2% 或 跌幅 > 1% → 触发")
    lines.append("")
    lines.append(f"**数据来源**: 东方财富")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return "\n".join(lines)


def main():
    # 读取预警数据
    with open('stock/alert-data.txt', 'r', encoding='utf-8') as f:
        alerts = json.load(f)
    
    if not alerts:
        print("No alerts to send")
        return
    
    # 生成消息
    message = format_alert_message(alerts)
    print("Generated message:")
    print(message)
    print("\n" + "="*50)
    
    # 读取接收者列表
    with open('stock/receiver-list.txt', 'r', encoding='utf-8') as f:
        receivers = [line.strip() for line in f if line.strip()]
    
    print(f"\n接收者数量：{len(receivers)}")
    for r in receivers:
        print(f"  - {r}")
    
    # 构建命令
    targets = " ".join([f"--targets {r}" for r in receivers])
    # 转义消息中的特殊字符
    escaped_message = message.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    
    cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{escaped_message}"'
    print(f"\n执行命令:\n{cmd}")
    
    return cmd, message


if __name__ == '__main__':
    main()
