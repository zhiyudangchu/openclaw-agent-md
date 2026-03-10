#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据 - 使用东方财富数据源
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

def read_watchlist():
    """读取自选股列表"""
    watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
    stocks = []
    with open(watchlist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                parts = line.split('|')
                code = parts[0]
                name = parts[1] if len(parts) > 1 else ''
                stocks.append({'code': code, 'name': name})
    return stocks

def convert_to_eastmoney_code(code, name=''):
    """转换为东方财富代码格式"""
    code = code.strip()
    # 如果已经是 ts_code 格式（包含.），转换一下
    if '.' in code:
        if 'SH' in code or 'HK' in code:
            return f"1.{code.split('.')[0]}"
        elif 'SZ' in code:
            return f"0.{code.split('.')[0]}"
    # 根据代码前缀判断交易所
    if code.startswith('6') or code.startswith('9'):
        return f"1.{code}"
    elif code.startswith('0') or code.startswith('3'):
        return f"0.{code}"
    elif code.startswith('8') or code.startswith('4') or code.startswith('920'):
        return f"0.{code}"  # 北交所
    else:
        # 港股或美股，暂时跳过
        return None

def get_realtime_data_eastmoney(stocks):
    """从东方财富获取实时数据"""
    results = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建东方财富实时行情请求
    codes = []
    stock_map = {}
    for stock in stocks:
        em_code = convert_to_eastmoney_code(stock['code'], stock['name'])
        if em_code:
            codes.append(em_code)
            stock_map[em_code] = stock
    
    if not codes:
        print("没有有效的 A 股代码")
        return results
    
    # 东方财富实时行情 API
    code_str = ','.join(codes)
    url = f"http://push2.eastmoney.com/api/qt/ulist/get?fltt=2&invt=2&fields=f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f1700,f13,f173,f104,f105,f14,f1701&secids={code_str}"
    
    print(f"请求 URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'http://quote.eastmoney.com/')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            json_data = json.loads(data)
            
            if json_data.get('data') and json_data['data'].get('diff'):
                for item in json_data['data']['diff']:
                    f57 = item.get('f57', '')  # 代码
                    f58 = item.get('f58', '')  # 市场代码
                    f14 = item.get('f14', '')  # 名称
                    f43 = item.get('f43', 0)   # 最新价
                    f46 = item.get('f46', 0)   # 涨跌额
                    f170 = item.get('f170', 0) # 涨跌幅
                    
                    # 找到原始股票信息
                    original_stock = None
                    for s in stocks:
                        if s['code'] == f57 or f"{'1' if f58 == 1 else '0'}.{f57}" in [convert_to_eastmoney_code(s['code'])]:
                            original_stock = s
                            break
                    
                    results.append({
                        'code': f57,
                        'name': original_stock['name'] if original_stock else f14,
                        'close': round(float(f43), 2) if f43 else 0,
                        'change_percent': round(float(f170), 2) if f170 else 0,
                        'change_amount': round(float(f46), 2) if f46 else 0,
                        'pre_close': round(float(f43) - float(f46), 2) if f43 and f46 else 0,
                        'open': round(float(item.get('f47', 0)), 2),
                        'high': round(float(item.get('f44', 0)), 2),
                        'low': round(float(item.get('f45', 0)), 2),
                        'volume': round(float(item.get('f48', 0)) / 10000, 2),  # 转换为万手
                        'amount': round(float(item.get('f50', 0)) / 100000000, 2),  # 转换为亿元
                        'timestamp': timestamp
                    })
    except Exception as e:
        print(f"获取东方财富数据失败：{e}")
    
    return results

def main():
    print("===== 获取自选股实时数据（东方财富）=====")
    
    # 读取自选股列表
    stocks = read_watchlist()
    print(f"自选股数量：{len(stocks)}")
    
    # 获取实时数据
    results = get_realtime_data_eastmoney(stocks)
    print(f"成功获取数据：{len(results)} 条")
    
    # 保存到文件
    output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到：{output_path}")
    
    # 打印结果
    for item in results:
        print(f"{item['code']} {item['name']}: ¥{item['close']} ({item['change_percent']:+.2f}%)")

if __name__ == "__main__":
    main()
