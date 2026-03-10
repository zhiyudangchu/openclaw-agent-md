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
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    header_info = []
    for line in lines:
        line = line.strip()
        if line.startswith('数据时间：') or line.startswith('数据来源：') or line.startswith('-'):
            header_info.append(line)
        elif '|' in line:
            parts = line.split('|')
            if len(parts) >= 6:
                data_lines.append({
                    'ts_code': parts[0],
                    'name': parts[1],
                    'close': float(parts[2]),
                    'pct_chg': float(parts[3]),
                    'change': float(parts[4]),
                    'trade_date': parts[5]
                })
    
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
            return True, f"🟢 中国石油 涨幅 > 2%"
        elif pct_chg < -1:
            return True, f"🔴 中国石油 跌幅 > 1%"
    
    # 通用规则
    if pct_chg < -3:
        return True, f"📉 下跌 > 3%"
    elif pct_chg > 5:
        return True, f"📈 上涨 > 5%"
    
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
    
    print(f"触发预警的股票数量：{len(alerts)}")
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    # 追加预警数据到文件
    with open(data_path, 'a', encoding='utf-8') as f:
        f.write("\n================================================================================\n")
        f.write("预警数据:\n")
        f.write("================================================================================\n")
        
        for alert in alerts:
            line = f"{alert['ts_code']}|{alert['name']}|{alert['close']:.2f}|{alert['pct_chg']:.2f}|{alert['change']:.2f}|{alert['trade_date']}|{alert['alert_rule']}\n"
            f.write(line)
            print(line.strip())
    
    print(f"\n预警数据已追加到：{data_path}")
    
    # 返回预警数据供推送使用
    return alerts

if __name__ == "__main__":
    alerts = main()
    if len(alerts) == 0:
        print("\n无触发预警的股票，结束任务")
