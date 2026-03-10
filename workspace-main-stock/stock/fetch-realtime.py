#!/usr/bin/env python3
"""
获取自选股实时行情数据
"""

import os
import sys
from datetime import datetime
import time

# Tushare Token
TUSHARE_TOKEN = "68442b378fd881f50cc6ae402e7277b6f46061bcc7b1df17b4ca6318"
WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")

def get_tushare_data(code):
    """通过 Tushare rt_k 接口获取实时行情"""
    try:
        import tushare as ts
        
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 标准化代码格式
        ts_code = code
        if code.endswith('.SH') or code.endswith('.SZ') or code.endswith('.HK') or code.endswith('.US'):
            pass
        elif code.startswith('6') or code.startswith('0'):
            ts_code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
        elif code.endswith('.HK'):
            ts_code = code
        else:
            ts_code = f"{code}.US" if code.isupper() else f"{code}.SH"
        
        # 尝试 rt_k 实时接口
        try:
            df = pro.rt_k(ts_code=ts_code)
            if not df.empty:
                row = df.iloc[0]
                return {
                    'code': code.split('.')[0] if '.' in code else code,
                    'name': row.get('name', code),
                    'price': float(row.get('close', 0)),
                    'pct_chg': float(row.get('pct_chg', 0)),
                    'price_change': float(row.get('close', 0)) - float(row.get('pre_close', 0)),
                    'vol': float(row.get('vol', 0)),
                    'amount': float(row.get('amount', 0)),
                    'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
        except Exception as e:
            print(f"rt_k 失败 {ts_code}: {e}", file=sys.stderr)
        
        # 回退到 daily 接口
        trade_date = datetime.now().strftime('%Y%m%d')
        df = pro.daily(ts_code=ts_code, trade_date=trade_date)
        if not df.empty:
            row = df.iloc[0]
            return {
                'code': code.split('.')[0] if '.' in code else code,
                'name': row.get('name', code),
                'price': float(row.get('close', 0)),
                'pct_chg': float(row.get('pct_chg', 0)),
                'price_change': float(row.get('close', 0)) - float(row.get('pre_close', 0)),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0)),
                'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
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
    
    # 清空输出文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        pass
    
    stocks = load_watchlist()
    results = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_tushare_data(code)
        
        if data:
            results.append(data)
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率 (rt_k 限制每分钟 1 次)
        if i < len(stocks) - 1:
            time.sleep(1.5)
    
    # 写入结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 成交量 | 成交额 | 时间\n")
        for r in results:
            vol_str = f"{r['vol']/10000:.2f}万" if r['vol'] > 10000 else f"{r['vol']:.2f}"
            amount_str = f"{r['amount']/100000000:.1f}亿" if r['amount'] > 100000000 else f"{r['amount']/10000:.1f}万"
            f.write(f"{r['code']}|{r['name']}|{r['price']:.2f}|{r['pct_chg']:+.2f}%|{vol_str}|{amount_str}|{r['trade_time']}\n")
    
    print(f"\n✅ 完成！共获取 {len(results)} 只股票数据")
    print(f"📁 保存至：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
