#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据预警规则过滤实时数据
"""

import os
from datetime import datetime

def read_realtime_data():
    """读取实时数据文件"""
    data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    stocks = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 跳过头部信息
    for line in lines:
        line = line.strip()
        if not line or line.startswith('数据时间') or line.startswith('数据来源') or line.startswith('-'):
            continue
        
        parts = line.split('|')
        if len(parts) >= 5:
            stocks.append({
                'ts_code': parts[0],
                'name': parts[1],
                'close': float(parts[2]),
                'pct_chg': float(parts[3]),
                'change': float(parts[4]),
                'time': parts[5] if len(parts) > 5 else ''
            })
    
    return stocks

def check_alert_rules(stock):
    """
    检查是否满足预警规则
    
    通用规则:
    - 下跌 > 3% → 触发
    - 上涨 > 5% → 触发
    
    个股专属规则:
    - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1% → 触发
    """
    ts_code = stock['ts_code']
    pct_chg = stock['pct_chg']
    
    # 检查中国石油专属规则
    if ts_code == '601857.SH':
        if pct_chg > 2:
            return True, '🟢 涨幅 > 2% (专属规则)'
        elif pct_chg < -1:
            return True, '🔴 跌幅 > 1% (专属规则)'
    
    # 通用规则
    if pct_chg < -3:
        return True, f'📉 下跌 > 3% ({pct_chg:.2f}%)'
    elif pct_chg > 5:
        return True, f'📈 上涨 > 5% ({pct_chg:.2f}%)'
    
    return False, None

def filter_alerts(stocks):
    """过滤出满足预警条件的股票"""
    alerts = []
    
    for stock in stocks:
        is_alert, reason = check_alert_rules(stock)
        if is_alert:
            stock['alert_reason'] = reason
            alerts.append(stock)
    
    # 按涨跌幅排序（绝对值大的在前）
    alerts.sort(key=lambda x: abs(x['pct_chg']), reverse=True)
    
    return alerts

def format_alert_table(alerts):
    """格式化预警数据为表格"""
    if not alerts:
        return ""
    
    lines = []
    lines.append("🚨 **股票预警通知** 🚨")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for stock in alerts[:10]:  # 最多输出 10 条
        time_short = stock['time'].split(' ')[1][:5] if ' ' in stock['time'] else stock['time'][:5]
        pct_sign = '+' if stock['pct_chg'] >= 0 else ''
        change_sign = '+' if stock['change'] >= 0 else ''
        
        line = f"| {stock['ts_code'].split('.')[0]} | {stock['name']} | ¥{stock['close']:.2f} | {pct_sign}{stock['pct_chg']:.2f}% | {change_sign}¥{stock['change']:.2f} | {time_short} |"
        lines.append(line)
    
    lines.append("")
    lines.append("⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 中国石油专属：🟢 涨幅 > 2% | 🔴 跌幅 > 1%")
    lines.append("")
    lines.append(f"**【数据来源】**")
    lines.append("- 数据来源：Tushare Pro (rt_k 接口)")
    lines.append(f"- 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def main():
    # 读取实时数据
    stocks = read_realtime_data()
    print(f"读取到 {len(stocks)} 只股票数据")
    
    # 过滤预警
    alerts = filter_alerts(stocks)
    print(f"筛选出 {len(alerts)} 只预警股票")
    
    if alerts:
        # 输出预警表格
        alert_table = format_alert_table(alerts)
        print(alert_table)
        
        # 保存预警数据
        alert_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-data.txt')
        with open(alert_path, 'w', encoding='utf-8') as f:
            f.write(alert_table)
        print(f"预警数据已保存：{alert_path}")
        
        # 输出纯文本格式用于消息推送
        print("\n--- 推送消息格式 ---")
        print(alert_table)
    else:
        print("无满足预警条件的股票")

if __name__ == "__main__":
    main()
