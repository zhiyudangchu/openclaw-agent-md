#!/usr/bin/env python3
"""
Fetch real-time stock data and filter by alert rules.
"""
import requests
import json
from datetime import datetime

watchlist_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt"
output_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"

# Alert rules: drop > 3% or rise > 5%
ALERT_DROP_THRESHOLD = -3.0
ALERT_RISE_THRESHOLD = 5.0

def get_stock_data(code):
    """Fetch stock data from East Money API."""
    # Convert code to secid format
    if code.endswith('.HK'):
        secid = f"120.{code.replace('.HK', '')}"
    elif code.startswith('6') or code.startswith('9') or code.startswith('sh'):
        secid = f"1.{code.replace('sh', '')}"
    elif code.startswith('0') or code.startswith('3') or code.startswith('sz'):
        secid = f"0.{code.replace('sz', '')}"
    else:
        # Try Shanghai first, then Shenzhen
        secid = f"1.{code}"
    
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f57,f58,f170,f47,f48&_=1234567890"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('rc') == 0 and data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100 if d.get('f43') else 0
            change_pct = d.get('f170', 0) / 100 if d.get('f170') else 0
            volume = d.get('f47', 0)
            amount = d.get('f48', 0)
            
            # Format volume and amount
            if volume >= 100000000:
                vol_str = f"{volume/100000000:.2f}亿"
            elif volume >= 10000:
                vol_str = f"{volume/10000:.2f}万"
            else:
                vol_str = f"{volume}"
                
            if amount >= 100000000:
                amt_str = f"{amount/100000000:.1f}亿"
            elif amount >= 10000:
                amt_str = f"{amount/10000:.1f}万"
            else:
                amt_str = f"{amount}"
            
            return {
                'code': d.get('f57', code),
                'name': d.get('f58', 'Unknown'),
                'price': price,
                'change_pct': change_pct,
                'volume': vol_str,
                'amount': amt_str
            }
    except Exception as e:
        print(f"Error fetching {code}: {e}")
    
    return None

# Read watchlist
with open(watchlist_file, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

print("Fetching stock data...")
results = []
for line in lines:
    parts = line.split('|')
    if len(parts) >= 1:
        code = parts[0]
        name = parts[1] if len(parts) > 1 else ''
        print(f"Fetching {code} - {name}...")
        data = get_stock_data(code)
        if data:
            results.append(data)

# Filter by alert rules
alert_results = []
for r in results:
    change = r['change_pct']
    if change > ALERT_RISE_THRESHOLD or change < ALERT_DROP_THRESHOLD:
        alert_results.append(r)

# Sort by change percentage (descending)
alert_results.sort(key=lambda x: x['change_pct'], reverse=True)

# Write to output file
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("代码 | 名称 | 现价 | 涨跌幅 | 成交量 | 成交额 | 时间\n")
    for r in alert_results:
        price_str = f"{r['price']:.2f}"
        change_str = f"+{r['change_pct']:.2f}%" if r['change_pct'] >= 0 else f"{r['change_pct']:.2f}%"
        f.write(f"{r['code']}|{r['name']}|{price_str}|{change_str}|{r['volume']}|{r['amount']}|{timestamp}\n")

print(f"\nTotal stocks fetched: {len(results)}")
print(f"Stocks triggering alerts: {len(alert_results)}")

if alert_results:
    print("\n=== Alert Results ===")
    for r in alert_results:
        change_str = f"+{r['change_pct']:.2f}%" if r['change_pct'] >= 0 else f"{r['change_pct']:.2f}%"
        print(f"{r['code']} - {r['name']}: {r['price']:.2f}元 ({change_str})")
else:
    print("\nNo stocks triggered alert rules.")
