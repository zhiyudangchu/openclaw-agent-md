#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控 - 完整流程
1. 获取实时数据
2. 应用预警规则
3. 发送飞书通知
"""

import requests
import json
import subprocess
from datetime import datetime
import sys

# ============ 配置 ============
WATCHLIST_FILE = '/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt'
REALTIME_DATA_FILE = '/home/openclaw/workspace-main-stock/stock/realtime-data.txt'
RECEIVER_FILE = '/home/openclaw/.openclaw/workspace-main-stock/stock/receiver-list.txt'

# ============ 获取股票数据 ============
def parse_stock_data(data_str, code, name):
    """解析腾讯财经数据"""
    try:
        if '"' in data_str:
            content = data_str.split('"')[1]
        else:
            content = data_str
        
        parts = content.split('~')
        if len(parts) < 35:
            return None
        
        current_name = parts[1] if len(parts) > 1 else name
        close = float(parts[3]) if len(parts) > 3 and parts[3] else 0
        pre_close = float(parts[4]) if len(parts) > 4 and parts[4] else 0
        open_price = float(parts[5]) if len(parts) > 5 and parts[5] else close
        high = float(parts[33]) if len(parts) > 33 and parts[33] else close
        low = float(parts[34]) if len(parts) > 34 and parts[34] else close
        
        change = close - pre_close
        change_pct = (change / pre_close * 100) if pre_close else 0
        
        return {
            'code': code,
            'name': current_name,
            'close': round(close, 2),
            'pre_close': round(pre_close, 2),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
        }
    except Exception as e:
        print(f'Parse error for {code}: {e}', file=sys.stderr)
        return None

def fetch_a_stock(code, name):
    if code.startswith('6') or code.startswith('9'):
        symbol = f'sh{code}'
    else:
        symbol = f'sz{code}'
    
    url = f'http://qt.gtimg.cn/q={symbol}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching A-share {code}: {e}', file=sys.stderr)
    return None

def fetch_hk_stock(code, name):
    hk_code = code.replace('.HK', '')
    url = f'http://qt.gtimg.cn/q=hk{hk_code}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching HK stock {code}: {e}', file=sys.stderr)
    return None

def fetch_us_stock(code, name):
    url = f'http://qt.gtimg.cn/q=gb_{code.lower()}'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.content.decode('gbk').strip()
            return parse_stock_data(data, code, name)
    except Exception as e:
        print(f'Error fetching US stock {code}: {e}', file=sys.stderr)
    return None

# ============ 预警规则 ============
def check_alert(stock):
    code = stock['code']
    change_pct = stock['change_pct']
    
    # 中国石油专属规则
    if code == '601857':
        if change_pct > 2:
            return True, '🟢 涨幅 > 2%'
        if change_pct < -1:
            return True, '🔴 跌幅 > 1%'
        return False, None
    
    # 通用规则
    if change_pct < -3:
        return True, '📉 下跌 > 3%'
    if change_pct > 5:
        return True, '📈 上涨 > 5%'
    
    return False, None

# ============ 主流程 ============
def main():
    # 读取自选股列表
    stocks = []
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                code, name = line.split('|', 1)
                stocks.append({'code': code.strip(), 'name': name.strip()})
    
    # 获取所有股票数据
    results = []
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        
        data = None
        if '.HK' in code:
            data = fetch_hk_stock(code, name)
        elif '.' not in code:
            data = fetch_a_stock(code, name)
        else:
            data = fetch_us_stock(code, name)
        
        if data:
            results.append(data)
    
    if not results:
        print('No data fetched')
        sys.exit(1)
    
    # 保存实时数据
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    # 应用预警规则
    alerts = []
    for stock in results:
        triggered, rule = check_alert(stock)
        if triggered:
            alerts.append({**stock, 'alert_rule': rule})
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_pct'], reverse=True)
    
    if not alerts:
        print('No alerts triggered')
        sys.exit(0)
    
    # 读取接收者列表
    receivers = []
    with open(RECEIVER_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    
    # 生成消息
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    lines = []
    lines.append("⚠️ **股价预警通知**")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for a in alerts:
        sign = '+' if a['change_pct'] >= 0 else ''
        lines.append(f"| {a['code']} | {a['name']} | ¥{a['close']:.2f} | {sign}{a['change_pct']:.2f}% | {a['change']:+.2f} | {now} |")
    
    lines.append("")
    lines.append("⚙️ 预警规则")
    lines.append("• 📉 下跌 > 3% → 触发")
    lines.append("• 📈 上涨 > 5% → 触发")
    lines.append("• 中国石油专属：🟢 涨幅 > 2% / 🔴 跌幅 > 1%")
    lines.append("")
    lines.append("【数据来源】")
    lines.append("数据来源：腾讯财经")
    lines.append(f"更新时间：{now}")
    
    message = '\n'.join(lines)
    
    # 发送飞书消息
    targets = []
    for r in receivers:
        targets.append('--targets')
        targets.append(r)
    
    cmd = ['openclaw', 'message', 'broadcast', '--channel', 'feishu', '--account', 'stock'] + targets + ['--message', message]
    
    print(f"Sending alert to {len(receivers)} receivers...")
    print(f"Alerts: {len(alerts)} stocks triggered")
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
    
    return result.returncode == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
