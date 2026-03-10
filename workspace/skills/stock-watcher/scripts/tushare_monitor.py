#!/usr/bin/env python3
"""
Tushare Pro 股票监控系统
数据源：Tushare API (更精准的 A 股/港股/美股数据)
"""

import os
import sys
import json
from datetime import datetime
import time

# 从配置读取 Tushare Token
TUSHARE_TOKEN = "68442b378fd881f50cc6ae402e7277b6f46061bcc7b1df17b4ca6318"
WATCHLIST_FILE = os.path.expanduser("~/.clawdbot/stock_watcher/watchlist.txt")

def get_stock_data_tushare(code):
    """通过 Tushare 获取股票数据"""
    try:
        import tushare as ts
        
        # 初始化接口
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 获取今日行情
        df = pro.daily(ts_code=code, trade_date=datetime.now().strftime('%Y%m%d'))
        
        if df.empty:
            return None
            
        row = df.iloc[0]
        
        return {
            'code': code,
            'name': self.get_stock_name(code),
            'price': row['close'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'vol': row['vol'],
            'amount': row['amount'],
            'pct_chg': row['pct_chg']  # 涨跌幅
        }
    except Exception as e:
        print(f"Tushare 获取失败 {code}: {e}", file=sys.stderr)
        return None

def get_stock_name(code):
    """获取股票名称"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        df = pro.stock_basic(ts_code=code)
        if not df.empty:
            return df.iloc[0]['name']
    except:
        pass
    return code

def load_watchlist():
    """加载监控列表"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    # 标准化股票代码格式
                    code = parts[0]
                    # 转换为 Tushare 格式（如 600519.SH）
                    if code.startswith('6') or code.startswith('0'):
                        code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
                    elif code == '00700':
                        code = '00700.HK'
                    elif code.upper() == 'AAPL':
                        code = 'AAPL.US'
                    stocks.append({'code': code, 'name': parts[1] if len(parts) > 1 else parts[0]})
    return stocks

def main():
    """主函数"""
    print(f"🦞 Tushare 监控系统启动 - {datetime.now()}")
    
    stocks = load_watchlist()
    results = []
    
    for stock in stocks:
        original_code = stock['code']
        display_name = stock['name']
        
        # 尝试用 Tushare 获取数据
        data = get_stock_data_tushare(original_code)
        
        if data:
            change = f"+{data['pct_chg']:.2f}%" if data['pct_chg'] >= 0 else f"{data['pct_chg']:.2f}%"
            results.append(f"{original_code:<12} {display_name:<10} ¥{data['price']:.2f}  {change}")
            print(f"✅ {original_code}: ¥{data['price']:.2f} ({change})")
        else:
            results.append(f"{original_code:<12} {display_name:<10} 数据暂不可用")
            print(f"⚠️ {original_code}: 数据获取失败")
        
        time.sleep(2)  # 控制请求频率
    
    print("\n---")
    print("📊 汇总完成")

if __name__ == "__main__":
    main()
