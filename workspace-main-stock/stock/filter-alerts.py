#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据预警规则过滤数据
"""

import os
import pandas as pd
from datetime import datetime

def parse_realtime_data(file_path):
    """
    解析实时数据文件
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line or line.startswith('代码'):
                continue
            
            parts = line.split('\t')
            if len(parts) >= 11:
                data.append({
                    'code': parts[0],
                    'name': parts[1],
                    'close': float(parts[2]),
                    'pre_close': float(parts[3]),
                    'change_pct': float(parts[4].replace('%', '')),
                    'change_amt': float(parts[5]),
                    'open': float(parts[6]),
                    'high': float(parts[7]),
                    'low': float(parts[8]),
                    'vol': int(parts[9]),
                    'amount': float(parts[10]),
                    'time': parts[11] if len(parts) > 11 else ''
                })
    return data

def check_alert_rules(data):
    """
    检查预警规则
    规则（已关闭，但保留逻辑）：
    - 通用规则（已关闭）：
      - 下跌 > 1% → 触发
      - 上涨 > 1% → 触发
    - 个股专属规则（已关闭）：
      - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1% → 触发
    
    由于规则已关闭，返回空列表
    """
    alerts = []
    
    # 规则状态：已关闭 ⛔
    # 所有规则都被划掉了，不触发任何预警
    rule_status = "已关闭"
    
    if rule_status == "已关闭":
        print("预警规则状态：已关闭 ⛔")
        print("不触发任何预警")
        return []
    
    # 以下为规则开启时的逻辑（保留参考）
    for stock in data:
        change_pct = stock['change_pct']
        code = stock['code']
        name = stock['name']
        
        triggered = False
        reason = []
        
        # 通用规则
        if change_pct < -1.0:
            triggered = True
            reason.append(f"下跌 {change_pct:.2f}% > 1%")
        elif change_pct > 1.0:
            triggered = True
            reason.append(f"上涨 {change_pct:.2f}% > 1%")
        
        # 个股专属规则 - 中国石油
        if code == '601857':
            if change_pct > 2.0:
                triggered = True
                reason.append(f"涨幅 {change_pct:.2f}% > 2% (个股规则)")
            elif change_pct < -1.0:
                triggered = True
                reason.append(f"跌幅 {change_pct:.2f}% > 1% (个股规则)")
        
        if triggered:
            stock['alert_reason'] = '; '.join(reason)
            alerts.append(stock)
    
    return alerts

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), 'realtime-data.txt')
    data = parse_realtime_data(file_path)
    
    print(f"共读取 {len(data)} 条数据")
    
    alerts = check_alert_rules(data)
    
    print(f"\n触发预警的股票数量：{len(alerts)}")
    
    if alerts:
        print("\n预警详情:")
        for stock in alerts:
            print(f"  {stock['code']} {stock['name']}: {stock['alert_reason']}")
    
    # 输出 JSON 格式供后续使用
    import json
    output = {
        'total': len(data),
        'alerts': len(alerts),
        'alert_list': alerts,
        'rule_status': '已关闭'
    }
    
    with open(os.path.join(os.path.dirname(__file__), 'alert-result.json'), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到 alert-result.json")
