#!/usr/bin/env python3
"""
获取自选股实时行情数据 - 使用新浪财经接口 (无频率限制)
"""

import os
import requests
from datetime import datetime

WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")

def get_sina_data(code):
    """通过新浪财经接口获取实时行情"""
    try:
        # 转换代码格式
        if code.endswith('.HK'):
            # 港股
            sina_code = code.replace('.HK', '')
            if sina_code.startswith('0'):
                sina_code = 'hk' + sina_code
            else:
                sina_code = 'hk' + sina_code
        elif code.endswith('.US'):
            # 美股
            sina_code = 'gb_' + code.replace('.US', '').lower()
        elif code.startswith('6') or code.startswith('9'):
            # 沪市
            sina_code = 'sh' + code.replace('.SH', '')
        elif code.startswith('0') or code.startswith('3'):
            # 深市
            sina_code = 'sz' + code.replace('.SZ', '')
        else:
            # 默认尝试沪市
            sina_code = 'sh' + code
        
        url = f"http://hq.sinajs.cn/list={sina_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'gbk'
        
        text = response.text.strip()
        if text and '=' in text:
            # 解析数据: var hq_str_sh601857="中国石油，12.92,12.30,12.92,13.00,12.85,12.91,12.90,..."
            data_part = text.split('="')[1].strip('"')
            parts = data_part.split(',')
            
            if len(parts) >= 4:
                name = parts[0]
                current_price = float(parts[3]) if parts[3] else 0
                prev_close = float(parts[2]) if parts[2] else current_price
                price_change = current_price - prev_close
                pct_chg = (price_change / prev_close * 100) if prev_close > 0 else 0
                
                return {
                    'code': code.split('.')[0] if '.' in code else code,
                    'name': name,
                    'price': current_price,
                    'pct_chg': pct_chg,
                    'price_change': price_change,
                    'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return None
    except Exception as e:
        print(f"错误 {code}: {e}", file=os.sys.stderr)
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
    print(f"📊 开始获取实时行情 (新浪财经) - {datetime.now()}")
    
    stocks = load_watchlist()
    results = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_sina_data(code)
        
        if data:
            results.append(data)
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率
        if i < len(stocks) - 1:
            import time
            time.sleep(0.3)
    
    # 写入结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in sorted(results, key=lambda x: x['pct_chg'], reverse=True):
            f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['trade_time']}\n")
    
    print(f"\n✅ 完成！共获取 {len(results)} 只股票数据")
    print(f"📁 保存至：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
