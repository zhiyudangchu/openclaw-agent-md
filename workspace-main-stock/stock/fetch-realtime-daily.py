#!/usr/bin/env python3
"""
获取自选股实时行情数据 (使用 Tushare daily 接口)
"""

import os
import sys
from datetime import datetime, timedelta
import time

# Tushare Token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', 'd5dffac476638f230dbe209bef04cd97b100c2dd3ddd10ddf85bc33d')
WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")

def get_tushare_daily(code):
    """通过 Tushare daily 接口获取最新行情"""
    try:
        import tushare as ts
        
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 标准化代码格式
        ts_code = code
        if code.endswith('.SH') or code.endswith('.SZ') or code.endswith('.HK') or code.endswith('.US'):
            pass
        elif code.startswith('6') or code.startswith('9'):
            ts_code = f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            ts_code = f"{code}.SZ"
        elif code.startswith('68'):
            ts_code = f"{code}.SH"  # STAR market
        elif '.HK' in code.upper():
            ts_code = code.replace('.HK', '.HK').upper() if not code.endswith('.HK') else code
        elif code.isupper() and len(code) <= 5:
            ts_code = f"{code}.US"
        else:
            ts_code = f"{code}.SH"
        
        # 获取今天和昨天的数据
        today = datetime.now()
        for days_back in range(5):  # 最多回溯 5 天
            trade_date = (today - timedelta(days=days_back)).strftime('%Y%m%d')
            
            try:
                df = pro.daily(ts_code=ts_code, trade_date=trade_date)
                if not df.empty:
                    row = df.iloc[0]
                    close = float(row.get('close', 0))
                    pre_close = float(row.get('pre_close', 0))
                    pct_chg = float(row.get('pct_chg', 0))
                    
                    if close > 0:
                        price_change = close - pre_close
                        return {
                            'code': code.split('.')[0] if '.' in code else code,
                            'name': row.get('name', code),
                            'price': close,
                            'pct_chg': pct_chg,
                            'price_change': price_change,
                            'vol': float(row.get('vol', 0)),
                            'amount': float(row.get('amount', 0)),
                            'trade_time': trade_date
                        }
            except Exception as e:
                continue
        
        return None
    except Exception as e:
        print(f"Tushare 错误 {code}: {e}", file=sys.stderr)
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
    print(f"📊 开始获取实时行情 - {datetime.now()}")
    
    stocks = load_watchlist()
    results = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_tushare_daily(code)
        
        if data:
            results.append(data)
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率
        if i < len(stocks) - 1:
            time.sleep(0.5)
    
    # 写入结果 (使用 watchlist 中的名称)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stock_names = {s['code']: s['name'] for s in stocks}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in results:
            price_str = f"¥{r['price']:.2f}"
            change_str = f"{r['pct_chg']:+.2f}%"
            change_amt = f"¥{r['price_change']:.2f}"
            name = stock_names.get(r['code'], r['name'])
            f.write(f"{r['code']}|{name}|{price_str}|{change_str}|{change_amt}|{timestamp}\n")
    
    print(f"\n✅ 完成！共获取 {len(results)} 只股票数据")
    print(f"📁 保存至：{OUTPUT_FILE}")
    
    return results

if __name__ == "__main__":
    main()
