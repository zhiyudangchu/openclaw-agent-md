#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter realtime data by alert rules and output alert results
"""

import os
from datetime import datetime

REALTIME_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")
ALERT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/alert-results.txt")

def check_alert_rules(code, name, pct_chg):
    """Check if stock triggers alert rules"""
    # Generic rules: drop > 3% or rise > 5%
    if pct_chg > 5.0:
        return True, "通用规则 (涨>5%)"
    if pct_chg < -3.0:
        return True, "通用规则 (跌>3%)"
    
    # 中国石油 special rules: rise > 2% or drop > 1%
    if code == '601857' or '中国石油' in name:
        if pct_chg > 2.0:
            return True, "中国石油专属规则 (涨>2%)"
        if pct_chg < -1.0:
            return True, "中国石油专属规则 (跌>1%)"
    
    return False, None

def main():
    print(f"🔍 开始过滤预警数据 - {datetime.now()}")
    
    alert_results = []
    
    if os.path.exists(REALTIME_FILE):
        with open(REALTIME_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Skip header
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 5:
                code = parts[0]
                name = parts[1]
                price_str = parts[2].replace('¥', '')
                pct_str = parts[3].replace('%', '')
                
                try:
                    price = float(price_str)
                    pct_chg = float(pct_str)
                except:
                    continue
                
                triggered, rule = check_alert_rules(code, name, pct_chg)
                if triggered:
                    alert_results.append({
                        'code': code,
                        'name': name,
                        'price': price,
                        'pct_chg': pct_chg,
                        'rule': rule,
                        'time': parts[5] if len(parts) > 5 else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    # Write alert results
    with open(ALERT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 触发规则 | 时间\n")
        for r in sorted(alert_results, key=lambda x: x['pct_chg'], reverse=True):
            price_change = r['price'] * r['pct_chg'] / 100
            f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{price_change:.2f}|{r['rule']}|{r['time']}\n")
    
    if alert_results:
        print(f"⚠️ {len(alert_results)} 只股票触发预警:")
        for r in alert_results:
            change_symbol = "🔴" if r['pct_chg'] >= 0 else "🟢"
            print(f"  {r['code']} {r['name']}: ¥{r['price']:.2f} ({r['pct_chg']:+.2f}%) {change_symbol} - {r['rule']}")
        print(f"📁 预警数据保存至：{ALERT_FILE}")
    else:
        print("✅ 无股票触发预警规则")
    
    # Output for message sending
    if alert_results:
        print("\n=== 预警消息内容 ===")
        msg_lines = ["⚠️ 股价预警通知", f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
        msg_lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 触发规则 |")
        msg_lines.append("|------|------|--------|--------|----------|")
        for r in sorted(alert_results, key=lambda x: x['pct_chg'], reverse=True):
            change_symbol = "🔴" if r['pct_chg'] >= 0 else "🟢"
            msg_lines.append(f"| {r['code']} | {r['name']} | ¥{r['price']:.2f} | {r['pct_chg']:+.2f}% {change_symbol} | {r['rule']} |")
        msg_lines.append("")
        msg_lines.append("⚙️ 预警规则")
        msg_lines.append("• 📉 下跌 > 3% → 触发")
        msg_lines.append("• 📈 上涨 > 5% → 触发")
        msg_lines.append("• 中国石油：涨>2% 或 跌>1% → 触发")
        
        print('\n'.join(msg_lines))

if __name__ == "__main__":
    main()
