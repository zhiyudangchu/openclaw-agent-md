#!/usr/bin/env python3
"""
获取自选股实时行情数据 - 使用东方财富 API
"""

import os
import sys
import json
import requests
from datetime import datetime

WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")

def get_em_data(code, name):
    """通过东方财富接口获取实时行情"""
    try:
        # 转换代码格式为东方财富格式
        if code.endswith('.HK'):
            # 港股
            secid = code.replace('.HK', '')
            if secid.startswith('0'):
                secid = '1.' + secid  # 港股
            else:
                secid = '1.' + secid
        elif code.endswith('.US'):
            # 美股
            secid = '100.' + code.replace('.US', '').lower()
        elif code.startswith('6') or code.startswith('9'):
            # 沪市
            secid = '1.' + code.replace('.SH', '')
        elif code.startswith('0') or code.startswith('3'):
            # 深市
            secid = '0.' + code.replace('.SZ', '')
        else:
            # 默认沪市
            secid = '1.' + code
        
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f55,f56,f57,f58,f84,f85,f116,f117,f124,f125,f126,f127,f128"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get('rc') == 0 and data.get('data'):
            d = data['data']
            current_price = d.get('f43', 0) / 100  # 当前价 (分转元)
            prev_close = d.get('f44', 0) / 100 if d.get('f44') else current_price  # 昨收
            open_price = d.get('f46', 0) / 100 if d.get('f46') else 0  # 今开
            high = d.get('f45', 0) / 100 if d.get('f45') else 0  # 最高
            low = d.get('f47', 0) / 100 if d.get('f47') else 0  # 最低
            vol = d.get('f48', 0)  # 成交量 (手)
            amount = d.get('f49', 0)  # 成交额 (元)
            
            price_change = current_price - prev_close
            pct_chg = (price_change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                'code': code,
                'name': d.get('f58', name),
                'price': current_price,
                'pct_chg': pct_chg,
                'price_change': price_change,
                'vol': vol,
                'amount': amount,
                'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return None
    except Exception as e:
        print(f"错误 {code}: {e}", file=sys.stderr)
        return None

def load_watchlist():
    """加载自选股列表"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|')
                    stocks.append({'code': parts[0], 'name': parts[1] if len(parts) > 1 else parts[0]})
    return stocks

def main():
    print(f"📊 开始获取实时行情 (东方财富) - {datetime.now()}")
    
    stocks = load_watchlist()
    results = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_em_data(code, name)
        
        if data:
            results.append(data)
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率
        if i < len(stocks) - 1:
            import time
            time.sleep(0.2)
    
    # 写入结果 - 按涨跌幅排序
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in sorted(results, key=lambda x: x['pct_chg'], reverse=True):
            f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['trade_time']}\n")
    
    print(f"\n✅ 完成！共获取 {len(results)} 只股票数据")
    print(f"📁 保存至：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
