#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时数据并应用预警规则
"""

import requests
import json
from datetime import datetime
import os

# 读取自选股列表
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|')
            stocks.append((code, name))

print(f"自选股数量：{len(stocks)}")

# 预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
# 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%
def check_alert(code, change_pct):
    """检查是否触发预警"""
    # 中国石油专属规则
    if code in ['601857.SH', '601857']:
        if change_pct > 2 or change_pct < -1:
            return True
    else:
        # 通用规则
        if change_pct < -3 or change_pct > 5:
            return True
    return False

# 东方财富实时行情 API
def get_stock_quote(code):
    """获取单只股票实时行情"""
    # 判断市场
    if '.' in code:
        if code.endswith('.SH'):
            secid = '1'
            stock_code = code.replace('.SH', '')
        elif code.endswith('.SZ'):
            secid = '0'
            stock_code = code.replace('.SZ', '')
        elif code.endswith('.HK'):
            secid = '105'
            stock_code = code.replace('.HK', '')
        else:
            return None
    elif code.startswith('6'):
        secid = '1'
        stock_code = code
    elif code.startswith('0') or code.startswith('3'):
        secid = '0'
        stock_code = code
    else:
        return None
    
    # 获取实时行情
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}.{stock_code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f84,f85,f116,f117,f118,f119"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('data'):
            return data['data']
    except Exception as e:
        print(f"获取 {code} 失败：{e}")
    return None

# 获取所有股票数据
results = []
alert_results = []
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for code, name in stocks:
    data = get_stock_quote(code)
    if data:
        # f43: 最新价 (分), f44: 涨跌幅 (%), f45: 涨跌额 (分), f46: 昨收 (分)
        # 价格需要除以 100 转换为元
        price = data.get('f43', 0) / 100
        change_pct = data.get('f44', 0)  # 已经是百分比
        change_amt = data.get('f45', 0) / 100
        pre_close = data.get('f46', 0) / 100
        
        # 格式化代码
        if code.startswith('6'):
            ts_code = f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            ts_code = f"{code}.SZ"
        else:
            ts_code = code
        
        result = {
            'code': ts_code,
            'name': name,
            'price': price,
            'change_pct': change_pct,
            'change_amt': change_amt,
            'pre_close': pre_close,
            'time': current_time
        }
        results.append(result)
        
        # 检查预警
        if check_alert(ts_code, change_pct):
            alert_results.append(result)
            print(f"⚠️ {ts_code} | {name} | {price:.2f} | {change_pct:+.2f}% | {change_amt:+.2f} [触发预警]")
        else:
            print(f"  {ts_code} | {name} | {price:.2f} | {change_pct:+.2f}% | {change_amt:+.2f}")
    else:
        print(f"  {code} | {name} | 获取失败")

# 保存全部数据到文件
output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"数据时间：{current_time}\n")
    f.write("=" * 80 + "\n")
    for r in results:
        f.write(f"{r['code']}|{r['name']}|{r['price']:.2f}|{r['pre_close']:.2f}|{r['change_pct']:.2f}|{r['time']}\n")

print(f"\n全部数据已保存到：{output_path}")
print(f"成功获取 {len(results)} 只股票数据")
print(f"触发预警 {len(alert_results)} 只股票")

# 如果有预警数据，输出预警信息
if alert_results:
    print("\n===== 预警数据 =====")
    # 按涨跌幅排序
    alert_results.sort(key=lambda x: x['change_pct'], reverse=True)
    for r in alert_results:
        print(f"{r['code']} | {r['name']} | {r['price']:.2f} | {r['change_pct']:+.2f}% | {r['change_amt']:+.2f}")
