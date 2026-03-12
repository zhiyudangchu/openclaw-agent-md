#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按照预警规则过滤实时数据
"""

import os
from datetime import datetime

def load_data(file_path):
    """加载实时数据"""
    data_lines = []
    header_info = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('数据来源：') or line.startswith('数据时间：'):
            header_info.append(line)
        elif line.startswith('====') or line.startswith('----') or line.startswith('代码 |'):
            continue
        elif '|' in line and not line.startswith('-'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                try:
                    # 解析数据：代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 昨收 | 时间
                    ts_code = parts[0]
                    name = parts[1]
                    close = float(parts[2].replace('¥', ''))
                    pct_chg_str = parts[3].replace('%', '')
                    pct_chg = float(pct_chg_str)
                    change = float(parts[4].replace('¥', ''))
                    pre_close = float(parts[5].replace('¥', ''))
                    trade_time = parts[6] if len(parts) > 6 else ''
                    
                    data_lines.append({
                        'ts_code': ts_code,
                        'name': name,
                        'close': close,
                        'pct_chg': pct_chg,
                        'change': change,
                        'pre_close': pre_close,
                        'trade_time': trade_time
                    })
                except Exception as e:
                    print(f"解析行失败：{line}, 错误：{e}")
    
    return header_info, data_lines

def check_alert_rules(stock):
    """
    检查是否触发预警规则
    返回：(是否触发，触发规则描述)
    """
    ts_code = stock['ts_code']
    name = stock['name']
    pct_chg = stock['pct_chg']
    
    # 中国石油专属规则
    if ts_code == '601857.SH':
        if pct_chg > 2:
            return True, f"🟢 涨幅 > 2%"
        elif pct_chg < -1:
            return True, f"🔴 跌幅 > 1%"
    
    # 通用规则
    if pct_chg < -1:
        return True, f"📉 下跌 > 1%"
    elif pct_chg > 1:
        return True, f"📈 上涨 > 1%"
    
    return False, None

def main():
    print("===== 预警数据过滤 =====")
    
    # 加载数据
    data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    header_info, data = load_data(data_path)
    
    print(f"加载到 {len(data)} 只股票数据")
    
    # 过滤预警数据
    alerts = []
    for stock in data:
        triggered, rule = check_alert_rules(stock)
        if triggered:
            alerts.append({
                **stock,
                'alert_rule': rule
            })
            print(f"触发预警：{stock['ts_code']} {stock['name']} {stock['pct_chg']:+.2f}% - {rule}")
    
    print(f"\n触发预警的股票数量：{len(alerts)}")
    
    # 按涨跌幅排序（降序）
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    # 返回预警数据
    return header_info, alerts

if __name__ == "__main__":
    header_info, alerts = main()
    if len(alerts) == 0:
        print("\n无触发预警的股票，结束任务")
    else:
        print("\n预警数据列表：")
        for alert in alerts:
            print(f"  {alert['ts_code']} {alert['name']} {alert['pct_chg']:+.2f}%")
