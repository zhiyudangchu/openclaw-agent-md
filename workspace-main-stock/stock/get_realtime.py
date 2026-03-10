#!/usr/bin/env python3
"""
Get real-time stock data from web and output structured results.
"""
import requests
from bs4 import BeautifulSoup
import re

watchlist_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt"

def get_stock_info(code, name):
    """Fetch single stock info."""
    url = f"https://stockpage.10jqka.com.cn/{code}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get current price
        price_elements = soup.find_all('span', class_='current')
        if price_elements:
            current_price = price_elements[0].get_text(strip=True).replace(',', '')
        else:
            current_price = "N/A"
            
        # Get change percentage
        change_percent = None
        percent_pattern = r'(-?\d+\.\d+)%'
        matches = re.findall(percent_pattern, response.text[:5000])
        if matches:
            change_percent = matches[0]
        
        return {
            'code': code,
            'name': name,
            'price': current_price,
            'change': change_percent
        }
        
    except Exception as e:
        return {'code': code, 'name': name, 'error': str(e)}

# Read watchlist
with open(watchlist_file, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

print("=" * 70)
print("老板自选股实时行情数据")
print("=" * 70)

results = []
for line in lines:
    parts = line.split('|')
    if len(parts) == 2:
        code, name = parts
        print(f"\n正在获取 {code} - {name}...")
        result = get_stock_info(code, name)
        results.append(result)
        
import time
time.sleep(0.5)

# Output summary
print("\n" + "=" * 70)
print("【实时行情汇总】")
print("=" * 70)

for r in results:
    status = ""
    if 'error' in r:
        status = f"[数据获取失败：{r['error']}]"
    elif r['price'] != 'N/A':
        status = f"[现价：{r['price']}元 | 涨跌幅：{r['change']}%]"
    else:
        status = "[行情数据暂不可用]"
    
    print(f"{r['code']} - {r['name']:15} {status}")

print("\n" + "=" * 70)
print("数据来源：同花顺财经 stockpage.10jqka.com.cn")
print("数据时间：" + __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)
