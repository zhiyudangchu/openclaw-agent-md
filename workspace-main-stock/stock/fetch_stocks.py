#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从同花顺网页获取自选股实时数据
"""

import requests
import re
import json
from datetime import datetime

# 读取自选股列表
watchlist_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt'
with open(watchlist_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 解析自选股
stocks = []
for line in lines:
    line = line.strip()
    if line and '|' in line:
        parts = line.split('|')
        code = parts[0]
        name = parts[1] if len(parts) > 1 else ''
        stocks.append({'code': code, 'name': name})

print(f"共 {len(stocks)} 只股票")

# 存储结果
results = []

# 同花顺实时数据接口
# 使用 http://q.10jqka.com.cn/stockinterface.php 接口
for stock in stocks:
    code = stock['code']
    name = stock['name']
    
    try:
        # 同花顺实时行情接口
        if '.' in code:
            # 已经有后缀
            if 'SH' in code or 'SZ' in code:
                symbol = code.replace('.SH', '').replace('.SZ', '')
            else:
                symbol = code
        else:
            symbol = code
        
        # 构建同花顺接口 URL
        url = f"http://q.10jqka.com.cn/stockinterface.php?code={symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://q.10jqka.com.cn/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # 解析返回数据
            content = response.text
            
            # 尝试提取数据
            # 同花顺返回格式类似：var hq_str_601857="中国石油，11.99,..."
            match = re.search(r'hq_str_\w+="([^"]+)"', content)
            if match:
                data_str = match.group(1)
                parts = data_str.split(',')
                
                if len(parts) >= 4:
                    stock_name = parts[0]
                    current_price = float(parts[1]) if parts[1] else 0
                    pre_close = float(parts[2]) if parts[2] else 0
                    open_price = float(parts[3]) if parts[3] else 0
                    
                    # 计算涨跌幅
                    if pre_close > 0:
                        change_pct = ((current_price - pre_close) / pre_close) * 100
                        change_amt = current_price - pre_close
                    else:
                        change_pct = 0
                        change_amt = 0
                    
                    results.append({
                        'code': code,
                        'name': stock_name,
                        'current': current_price,
                        'pre_close': pre_close,
                        'change_pct': change_pct,
                        'change_amt': change_amt,
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    print(f"✓ {code} {stock_name}: ¥{current_price:.2f} ({change_pct:+.2f}%)")
                else:
                    print(f"✗ {code} 数据格式异常")
            else:
                print(f"✗ {code} 未找到数据")
        else:
            print(f"✗ {code} HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ {code} 错误：{e}")

# 保存到文件
output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"数据时间：{current_time}\n")
    f.write("=" * 80 + "\n")
    
    for r in results:
        # 格式：代码 | 名称 | 当前价 | 昨收 | 最高 | 时间
        f.write(f"{r['code']}|{r['name']}|{r['current']:.2f}|{r['pre_close']:.2f}|{r['current']:.2f}|{r['time']}\n")

print(f"\n数据已保存到：{output_path}")
print(f"成功获取 {len(results)} 只股票数据")
