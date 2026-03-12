#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警规则检查脚本
"""

import os
from datetime import datetime

# 预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
# 个股专属规则：
#   - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%

def check_alert_rules(code, name, close, pct_chg, change):
    """
    检查是否触发预警规则
    返回：(是否触发，触发原因)
    """
    alerts = []
    
    # 通用规则
    if pct_chg < -3.0:
        alerts.append(f"📉 下跌 > 3% (当前：{pct_chg:.2f}%)")
    if pct_chg > 5.0:
        alerts.append(f"📈 上涨 > 5% (当前：{pct_chg:.2f}%)")
    
    # 个股专属规则 - 中国石油
    if code == "601857.SH":
        if pct_chg > 2.0:
            alerts.append(f"🟢 专属规则：涨幅 > 2% (当前：{pct_chg:.2f}%)")
        if pct_chg < -1.0:
            alerts.append(f"🔴 专属规则：跌幅 > 1% (当前：{pct_chg:.2f}%)")
    
    if alerts:
        return True, alerts
    return False, []

def load_realtime_data():
    """加载实时数据"""
    data_file = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    stocks = []
    
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) >= 6:
                ts_code = parts[0]
                name = parts[1]
                close = float(parts[2])
                # pct_chg 从原始数据重新计算
                pre_close = close - float(parts[4])  # change = close - pre_close
                pct_chg = ((close - pre_close) / pre_close * 100) if pre_close > 0 else 0
                change = float(parts[4])
                time_str = parts[5]
                
                stocks.append({
                    'code': ts_code,
                    'name': name,
                    'close': close,
                    'pct_chg': pct_chg,
                    'change': change,
                    'time': time_str
                })
    
    return stocks

def format_alert_message(alert_stocks):
    """格式化预警消息"""
    # 按涨跌幅排序
    alert_stocks.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    lines = []
    lines.append("🚨 **股价预警通知** 🚨")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for stock in alert_stocks:
        time_short = stock['time'].split(' ')[1][:5]  # HH:MM
        change_sign = "+" if stock['change'] >= 0 else ""
        pct_sign = "+" if stock['pct_chg'] >= 0 else ""
        
        # 高亮异常波动
        highlight = ""
        if abs(stock['pct_chg']) > 3:
            highlight = "⚠️"
        
        lines.append(f"| {stock['code'].split('.')[0]} | {stock['name']} | ¥{stock['close']:.2f} | {pct_sign}{stock['pct_chg']:.2f}% | {change_sign}¥{stock['change']:.2f} | {time_short} | {highlight}")
    
    lines.append("")
    lines.append("⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("")
    lines.append(f"**数据来源**: Tushare Pro")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def main():
    print("===== 预警规则检查 =====")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载数据
    print("\n[步骤1] 加载实时数据...")
    stocks = load_realtime_data()
    print(f"共加载 {len(stocks)} 条记录")
    
    # 检查预警
    print("\n[步骤2] 检查预警规则...")
    alert_stocks = []
    
    for stock in stocks:
        triggered, reasons = check_alert_rules(
            stock['code'],
            stock['name'],
            stock['close'],
            stock['pct_chg'],
            stock['change']
        )
        
        if triggered:
            print(f"  ⚠️ {stock['name']} ({stock['code']}): 触发预警")
            for reason in reasons:
                print(f"     - {reason}")
            stock['alerts'] = reasons
            alert_stocks.append(stock)
        else:
            print(f"  ✓ {stock['name']} ({stock['code']}): {stock['pct_chg']:.2f}% - 无预警")
    
    # 保存结果
    print(f"\n[步骤3] 预警结果...")
    if alert_stocks:
        print(f"共 {len(alert_stocks)} 只股票触发预警")
        
        # 格式化消息
        message = format_alert_message(alert_stocks)
        
        # 保存预警消息
        output_file = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-message.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"预警消息已保存到：{output_file}")
        
        # 输出消息内容
        print("\n" + "="*50)
        print(message)
        print("="*50)
        
        return True, message
    else:
        print("无股票触发预警，任务结束")
        return False, None

if __name__ == "__main__":
    main()
