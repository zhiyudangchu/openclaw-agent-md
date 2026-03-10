#!/usr/bin/env python3
"""
获取自选股实时行情并应用预警规则
"""

import os
import sys
from datetime import datetime
import time

# Tushare Token
TUSHARE_TOKEN = "68442b378fd881f50cc6ae402e7277b6f46061bcc7b1df17b4ca6318"
WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")
ALERT_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/alert-data.txt")

# 预警规则
def check_alert(code, name, pct_chg):
    """检查是否触发预警规则"""
    # 通用规则
    if pct_chg < -3.0:  # 下跌 > 3%
        return True, "下跌>3%"
    if pct_chg > 5.0:   # 上涨 > 5%
        return True, "上涨>5%"
    
    # 个股专属规则 - 中国石油 (601857)
    if code == "601857" or name == "中国石油":
        if pct_chg > 2.0:
            return True, "中国石油涨幅>2%"
        if pct_chg < -1.0:
            return True, "中国石油跌幅>1%"
    
    return False, None

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
        elif code.startswith('6') or code.startswith('0') or code.startswith('3') or code.startswith('9'):
            if code.startswith('6') or code.startswith('9'):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
        elif code.endswith('.HK'):
            ts_code = code
        else:
            # 美股
            ts_code = f"{code}.US"
        
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
    alerts = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_tushare_data(code)
        
        if data:
            results.append(data)
            
            # 检查预警规则
            is_alert, reason = check_alert(data['code'], data['name'], data['pct_chg'])
            if is_alert:
                alerts.append({**data, 'reason': reason})
            
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率
        if i < len(stocks) - 1:
            time.sleep(1.5)
    
    # 写入全部数据
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in sorted(results, key=lambda x: x['pct_chg'], reverse=True):
            f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['trade_time']}\n")
    
    # 写入预警数据
    with open(ALERT_FILE, 'w', encoding='utf-8') as f:
        if alerts:
            f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间 | 触发规则\n")
            for a in sorted(alerts, key=lambda x: x['pct_chg'], reverse=True):
                f.write(f"{a['code']}|{a['name']}|¥{a['price']:.2f}|{a['pct_chg']:+.2f}%|¥{a['price_change']:.2f}|{a['trade_time']}|{a['reason']}\n")
    
    print(f"\n✅ 完成！共获取 {len(results)} 只股票数据")
    print(f"🚨 触发预警：{len(alerts)} 只")
    print(f"📁 全部数据：{OUTPUT_FILE}")
    print(f"🚨 预警数据：{ALERT_FILE}")
    
    # 返回预警数据用于推送
    if alerts:
        print("\n📢 预警详情:")
        for a in sorted(alerts, key=lambda x: x['pct_chg'], reverse=True):
            print(f"  {a['code']} {a['name']}: ¥{a['price']:.2f} ({a['pct_chg']:+.2f}%) - {a['reason']}")
    
    return alerts

if __name__ == "__main__":
    alerts = main()
    sys.exit(0 if not alerts else 1)
