#!/usr/bin/env python3
"""
Tushare Pro 股价推送脚本
从环境变量获取 Token，定时推送至飞书
"""

import os
import sys
from datetime import datetime, timedelta
import time

# 从环境变量读取 Token
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TUSHARE_TOKEN:
    print("错误：TUSHARE_TOKEN 环境变量未设置", file=sys.stderr)
    sys.exit(1)

WATCHLIST_FILE = os.path.expanduser("~/.clawdbot/stock_watcher/watchlist.txt")
LOG_FILE = os.path.expanduser("~/.clawdbot/stock_watcher/push_tushare.log")

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")

def get_tushare_data(code, name):
    """通过 Tushare 获取股票数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 查询昨日数据（交易日）
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        df = pro.query('daily', ts_code=code, trade_date=yesterday)
        
        if df.empty:
            return {'code': code, 'name': name, 'price': 'N/A', 'change': 'N/A'}
        
        row = df.iloc[0]
        pct = row['pct_chg']
        change_str = f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"
        
        return {
            'code': code,
            'name': name,
            'price': row['close'],
            'change': change_str,
            'pct': pct
        }
    except Exception as e:
        log_message(f"Tushare 获取失败 {code}: {e}")
        return {'code': code, 'name': name, 'price': 'N/A', 'change': '获取失败', 'pct': 0}

def load_watchlist():
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    code = parts[0]
                    name = parts[1] if len(parts) > 1 else code
                    
                    # 标准化为 Tushare 格式
                    if code.startswith('6'):
                        code = f"{code}.SH"
                    elif code.startswith('0') or code.startswith('3'):
                        code = f"{code}.SZ"
                    elif code == '00700':
                        code = '00700.HK'
                    elif code.upper() == 'AAPL':
                        code = 'AAPL.US'
                    
                    stocks.append({'code': code, 'name': name})
    return stocks

def main():
    log_message("=== 开始 Tushare 推送 ===")
    
    stocks = load_watchlist()
    results = []
    
    for stock in stocks:
        data = get_tushare_data(stock['code'], stock['name'])
        results.append(data)
        time.sleep(2)
    
    # 生成报表
    timestamp = datetime.now().strftime("%m-%d %H:%M")
    content = f"🦞 **【Tushare 行情快报】** {timestamp}\n\n```\n{'-'*40}\n{'代码':<12} {'名称':<10} {'收盘价':<12} {'涨跌幅':<8}\n{'-'*40}\n"
    
    for r in results:
        price = f"¥{r['price']:.2f}" if isinstance(r['price'], (int, float)) else str(r['price'])
        emoji = '🟢' if r.get('pct', 0) >= 0 else '🔴'
        content += f"{emoji} {r['code']:<10} {r['name']:<10} {price:<12} {r['change']:<8}\n"
    
    content += f"{'-'*40}\n```\n\n📊 **数据来源：** Tushare Pro API\n⏱️ **下次更新：** 5 分钟后\n\n---\n🦞 龙虾自动推送服务"
    
    print(content)
    log_message(f"推送完成，共 {len(results)} 只股票")
    
    return content

if __name__ == "__main__":
    main()
