#!/usr/bin/env python3
"""
Fetch real-time stock data and filter by alert rules.
Alert Rules:
- Generic: drop > 3% or rise > 5%
- 中国石油 (601857.SH): rise > 2% or drop > 1%
"""

import os
import sys
from datetime import datetime
import time

# Tushare Token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '68442b378fd881f50cc6ae402e7277b6f46061bcc7b1df17b4ca6318')
WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")
ALERT_OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/alert-results.txt")

import tushare as ts

def get_realtime_data(ts_code, name):
    """Get real-time data using Tushare rt_k interface"""
    try:
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # Try rt_k real-time interface first
        try:
            df = pro.rt_k(ts_code=ts_code, fields='ts_code,name,close,pct_chg,pre_close,vol,amount,trade_time')
            if not df.empty:
                row = df.iloc[0]
                price = float(row.get('close', 0))
                pct_chg = float(row.get('pct_chg', 0))
                pre_close = float(row.get('pre_close', 0)) if row.get('pre_close') else 0
                price_change = price - pre_close if pre_close else 0
                return {
                    'code': ts_code.split('.')[0],
                    'name': row.get('name', name),
                    'price': price,
                    'pct_chg': pct_chg,
                    'price_change': price_change,
                    'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
        except Exception as e:
            print(f"rt_k failed for {ts_code}: {e}", file=sys.stderr)
        
        # Fallback to daily interface
        trade_date = datetime.now().strftime('%Y%m%d')
        df = pro.daily(ts_code=ts_code, trade_date=trade_date)
        if not df.empty:
            row = df.iloc[0]
            price = float(row.get('close', 0))
            pct_chg = float(row.get('pct_chg', 0))
            pre_close = float(row.get('pre_close', 0)) if row.get('pre_close') else price / (1 + pct_chg/100) if pct_chg else price
            price_change = price - pre_close
            return {
                'code': ts_code.split('.')[0],
                'name': row.get('name', name),
                'price': price,
                'pct_chg': pct_chg,
                'price_change': price_change,
                'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return None
    except Exception as e:
        print(f"Tushare error for {ts_code}: {e}", file=sys.stderr)
        return None

def check_alert_rules(code, name, pct_chg):
    """Check if stock triggers alert rules"""
    # Generic rules
    if pct_chg > 5.0 or pct_chg < -3.0:
        return True, "通用规则"
    
    # 中国石油 special rules
    if code == '601857' or '中国石油' in name:
        if pct_chg > 2.0:
            return True, "中国石油专属规则 (涨>2%)"
        if pct_chg < -1.0:
            return True, "中国石油专属规则 (跌>1%)"
    
    return False, None

def load_watchlist():
    """Load watchlist"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|')
                    code = parts[0]
                    name = parts[1] if len(parts) > 1 else parts[0]
                    
                    # Standardize code format
                    if not ('.' in code and (code.endswith('.SH') or code.endswith('.SZ') or code.endswith('.HK') or code.endswith('.US'))):
                        if code.startswith('6') or code.startswith('9'):
                            code = f"{code}.SH"
                        elif code.startswith('0') or code.startswith('3'):
                            code = f"{code}.SZ"
                        elif code.endswith('.HK'):
                            pass  # Already has .HK
                        elif len(code) <= 5 and code.isdigit():
                            code = f"{code}.SH" if code.startswith('6') or code.startswith('9') else f"{code}.SZ"
                    
                    stocks.append({'code': code, 'name': name, 'original_code': parts[0]})
    return stocks

def main():
    print(f"📊 开始获取实时行情 - {datetime.now()}")
    
    stocks = load_watchlist()
    all_results = []
    alert_results = []
    
    for i, stock in enumerate(stocks):
        ts_code = stock['code']
        name = stock['name']
        original_code = stock['original_code']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {original_code} {name}...", end=" ")
        
        data = get_realtime_data(ts_code, name)
        
        if data:
            all_results.append(data)
            
            # Check alert rules
            triggered, rule = check_alert_rules(original_code, name, data['pct_chg'])
            if triggered:
                alert_results.append({**data, 'rule': rule})
                change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
                print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol} ⚠️ 触发预警")
            else:
                change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
                print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # Rate limiting
        if i < len(stocks) - 1:
            time.sleep(1.2)
    
    # Write all data to realtime-data.txt
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in sorted(all_results, key=lambda x: x['pct_chg'], reverse=True):
            f.write(f"{r['code'].split('.')[0]}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['trade_time']}\n")
    
    print(f"\n✅ 完成！共获取 {len(all_results)} 只股票数据")
    print(f"📁 全部数据保存至：{OUTPUT_FILE}")
    
    # Write alert results
    if alert_results:
        with open(ALERT_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 触发规则 | 时间\n")
            for r in sorted(alert_results, key=lambda x: x['pct_chg'], reverse=True):
                f.write(f"{r['code'].split('.')[0]}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['rule']}|{r['trade_time']}\n")
        
        print(f"⚠️ {len(alert_results)} 只股票触发预警")
        print(f"📁 预警数据保存至：{ALERT_OUTPUT_FILE}")
        
        # Output JSON for alert sending
        print("\n=== 预警数据 ===")
        for r in alert_results:
            print(f"{r['code'].split('.')[0]} - {r['name']}: ¥{r['price']:.2f} ({r['pct_chg']:+.2f}%) - {r['rule']}")
    else:
        print("✅ 无股票触发预警规则")
        # Clear alert file
        open(ALERT_OUTPUT_FILE, 'w').close()

if __name__ == "__main__":
    main()
