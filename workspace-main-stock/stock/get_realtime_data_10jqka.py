#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从同花顺获取自选股实时数据
数据源：https://stockpage.10jqka.com.cn/
"""

import os
import sys
import re
import json
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# 设置请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

def read_watchlist():
    """读取自选股列表"""
    watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
    stocks = []
    with open(watchlist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                code, name = line.split('|')
                stocks.append({'code': code, 'name': name})
    return stocks

def get_stock_data(code):
    """
    从同花顺获取股票实时数据
    使用同花顺的行情接口
    """
    try:
        # 同花顺行情接口
        # 对于 A 股，使用 6 位代码
        # 对于港股，使用 HK 前缀
        # 对于美股，使用 US 前缀
        
        ts_code = code
        if code.isdigit():
            # A 股
            if code.startswith('6'):
                ts_code = f"SH{code}"
            elif code.startswith('0') or code.startswith('3'):
                ts_code = f"SZ{code}"
            elif code.startswith('8') or code.startswith('4'):
                ts_code = f"BJ{code}"
        elif '.HK' in code.upper():
            ts_code = code.replace('.HK', '').replace('.hk', '')
            ts_code = f"HK{ts_code}"
        elif code.upper() in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']:
            ts_code = f"US{code}"
        
        # 同花顺实时行情接口
        url = f"http://q.10jqka.com.cn/stockorder/json/stock/{ts_code.lower()}/all.json"
        
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8', errors='ignore'))
            
            if data and 'data' in data:
                stock_data = data['data']
                return {
                    'code': code,
                    'name': stock_data.get('name', ''),
                    'price': float(stock_data.get('price', 0)),
                    'change': float(stock_data.get('change', 0)),
                    'pct_chg': float(stock_data.get('changepercent', 0)),
                    'pre_close': float(stock_data.get('preclose', 0)),
                    'open': float(stock_data.get('open', 0)),
                    'high': float(stock_data.get('high', 0)),
                    'low': float(stock_data.get('low', 0)),
                    'vol': float(stock_data.get('vol', 0)),
                    'amount': float(stock_data.get('amount', 0)),
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
    except Exception as e:
        print(f"获取 {code} 数据失败：{e}")
    
    return None

def get_stock_data_alternative(code):
    """
    备用数据获取方法 - 使用网页解析
    """
    try:
        # 处理代码格式
        if code.isdigit():
            stock_code = code
        elif '.HK' in code.upper():
            stock_code = code.replace('.HK', '').replace('.hk', '')
        elif code.upper() in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']:
            stock_code = code
        else:
            stock_code = code
        
        url = f"https://stockpage.10jqka.com.cn/{stock_code}/"
        req = Request(url, headers=HEADERS)
        
        with urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # 尝试从 HTML 中提取数据
            # 查找股价
            price_match = re.search(r'"now":"([\d.]+)"', html)
            # 查找涨跌幅
            pct_match = re.search(r'"nowPercent":"([+-]?[\d.]+)%?"', html)
            # 查找涨跌额
            change_match = re.search(r'"nowChange":"([+-]?[\d.]+)"', html)
            # 查找名称
            name_match = re.search(r'<title>([^-]+)-', html)
            
            if price_match:
                return {
                    'code': code,
                    'name': name_match.group(1).strip() if name_match else '',
                    'price': float(price_match.group(1)),
                    'change': float(change_match.group(1)) if change_match else 0,
                    'pct_chg': float(pct_match.group(1)) if pct_match else 0,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
    except Exception as e:
        print(f"备用方法获取 {code} 数据失败：{e}")
    
    return None

def check_alert_rules(stock_data):
    """
    检查预警规则
    通用规则:
    1. 下跌 > 3% → 触发
    2. 上涨 > 5% → 触发
    
    个股专属规则:
    中国石油 (601857):
    - 涨幅 > 2% → 触发预警
    - 跌幅 > 1% → 触发预警
    """
    if not stock_data:
        return None
    
    code = stock_data['code']
    pct_chg = stock_data['pct_chg']
    
    triggered = False
    rule = ""
    
    # 检查中国石油专属规则
    if code == '601857':
        if pct_chg > 2:
            triggered = True
            rule = f"🟢 专属规则：涨幅 {pct_chg:.2f}% > 2%"
        elif pct_chg < -1:
            triggered = True
            rule = f"🔴 专属规则：跌幅 {pct_chg:.2f}% < -1%"
    else:
        # 通用规则
        if pct_chg < -3:
            triggered = True
            rule = f"📉 通用规则：下跌 {pct_chg:.2f}% < -3%"
        elif pct_chg > 5:
            triggered = True
            rule = f"📈 通用规则：上涨 {pct_chg:.2f}% > 5%"
    
    if triggered:
        stock_data['rule'] = rule
        return stock_data
    
    return None

def save_data(all_data, alerts):
    """保存数据到文件"""
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("代码，名称，当前价，涨跌额，涨跌幅，昨收，今开，最高，最低，成交量，成交额，时间\n")
        for data in all_data:
            if data:
                f.write(f"{data['code']},{data['name']},{data['price']},{data['change']:.2f},{data['pct_chg']:.2f},{data.get('pre_close', 0)},{data.get('open', 0)},{data.get('high', 0)},{data.get('low', 0)},{data.get('vol', 0)},{data.get('amount', 0)},{data['time']}\n")

def generate_alert_message(alerts):
    """生成预警消息"""
    if not alerts:
        return None
    
    lines = []
    lines.append("🚨 股价预警通知")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    for alert in alerts[:10]:
        code = alert['code']
        name = alert['name']
        price = alert['price']
        pct_chg = alert['pct_chg']
        change = alert['change']
        time = alert['time'].split(' ')[1][:5]
        
        pct_str = f"+{pct_chg:.2f}%" if pct_chg > 0 else f"{pct_chg:.2f}%"
        change_str = f"+¥{change:.2f}" if change > 0 else f"¥{change:.2f}"
        
        lines.append(f"| {code} | {name} | ¥{price:.2f} | {pct_str} | {change_str} | {time} |")
    
    lines.append("")
    lines.append("⚙️ 预警规则")
    lines.append("• 📉 下跌 > 3% → 触发")
    lines.append("• 📈 上涨 > 5% → 触发")
    lines.append("• 中国石油专属：涨幅 > 2% 或 跌幅 > 1%")
    lines.append("")
    lines.append("【数据来源】")
    lines.append("数据来源：同花顺 (10jqka.com.cn)")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def read_receiver_list():
    """读取接收者列表"""
    receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    receivers = []
    with open(receiver_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    return receivers

if __name__ == '__main__':
    print("从同花顺获取实时数据...")
    
    # 读取 watchlist
    stocks = read_watchlist()
    print(f"自选股数量：{len(stocks)}")
    
    all_data = []
    alerts = []
    
    # 获取每只股票的数据
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=' ')
        
        data = get_stock_data(code)
        if not data:
            data = get_stock_data_alternative(code)
        
        if data:
            print(f"✓ {data['price']} ({data['pct_chg']:+.2f}%)")
            all_data.append(data)
            
            # 检查预警规则
            alert = check_alert_rules(data)
            if alert:
                alerts.append(alert)
                print(f"  ⚠️ 触发预警：{alert['rule']}")
        else:
            print("✗ 失败")
    
    print(f"\n成功获取 {len(all_data)} 条数据")
    print(f"触发预警 {len(alerts)} 条")
    
    # 保存数据
    save_data(all_data, alerts)
    print("数据已保存到 realtime-data.txt")
    
    if alerts:
        # 生成预警消息
        message = generate_alert_message(alerts)
        print("\n预警消息:")
        print(message)
        
        # 读取接收者列表
        receivers = read_receiver_list()
        print(f"\n接收者数量：{len(receivers)}")
        
        # 构建广播命令
        targets = ' '.join([f'--targets {r}' for r in receivers])
        # 转义消息中的特殊字符
        message_escaped = message.replace('"', '\\"').replace('\n', '\\n')
        
        cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{message_escaped}"'
        print(f"\n执行广播命令...")
        
        # 执行广播命令
        os.system(cmd)
        print("预警已发送")
    else:
        print("无触发预警的股票")
    
    print("\n任务完成")
