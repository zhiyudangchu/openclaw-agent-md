#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查预警规则并生成预警数据
"""
import json

# 预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
# 中国石油专属：涨幅 > 2% 或 跌幅 > 1%

def check_alert(stock, alert_rules):
    """
    检查单只股票是否触发预警
    """
    code = stock['code']
    name = stock['name']
    change_percent = stock['change_percent']
    
    triggered = False
    reason = []
    
    # 检查是否有专属规则
    if code in alert_rules.get('special', {}):
        special_rule = alert_rules['special'][code]
        if 'up_threshold' in special_rule and change_percent > special_rule['up_threshold']:
            triggered = True
            reason.append(f"涨幅 {change_percent:+.2f}% > {special_rule['up_threshold']:+.2f}%")
        if 'down_threshold' in special_rule and change_percent < special_rule['down_threshold']:
            triggered = True
            reason.append(f"跌幅 {change_percent:+.2f}% < {special_rule['down_threshold']:+.2f}%")
    else:
        # 通用规则
        if change_percent > alert_rules['general']['up']:
            triggered = True
            reason.append(f"涨幅 {change_percent:+.2f}% > {alert_rules['general']['up']:+.2f}%")
        if change_percent < alert_rules['general']['down']:
            triggered = True
            reason.append(f"跌幅 {change_percent:+.2f}% < {alert_rules['general']['down']:+.2f}%")
    
    return triggered, reason


def main():
    # 预警规则配置
    alert_rules = {
        'general': {
            'up': 5,    # 上涨 > 5%
            'down': -3  # 下跌 > 3%
        },
        'special': {
            '601857': {  # 中国石油
                'up_threshold': 2,   # 涨幅 > 2%
                'down_threshold': -1  # 跌幅 > 1%
            }
        }
    }
    
    # 读取实时数据
    with open('stock/realtime-data.txt', 'r', encoding='utf-8') as f:
        stocks = json.load(f)
    
    # 检查预警
    alerts = []
    for stock in stocks:
        triggered, reason = check_alert(stock, alert_rules)
        if triggered:
            stock['alert_reason'] = reason
            alerts.append(stock)
            print(f"⚠️ {stock['code']} {stock['name']}: {stock['change_percent']:+.2f}% - {', '.join(reason)}")
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_percent'], reverse=True)
    
    # 保存预警数据
    with open('stock/alert-data.txt', 'w', encoding='utf-8') as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
    
    print(f"\n共 {len(alerts)} 只股票触发预警")
    return alerts


if __name__ == '__main__':
    main()
