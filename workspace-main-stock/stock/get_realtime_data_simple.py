#!/usr/bin/env python3
"""
获取自选股实时数据 - 使用腾讯接口
数据格式：v_sh601857="1~中国石油~601857~11.94~12.92~12.18~...~-0.98~-7.59~..."
字段说明：
- f3: 当前价
- f4: 昨收
- f5: 今开
- f32: 涨跌额
- f33: 涨跌幅%
"""
import urllib.request
import re
from datetime import datetime

watchlist_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt'
output_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'

stocks = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) == 2:
                code, name = parts
                stocks.append({'code': code, 'name': name})

def get_stock_data(code):
    """获取单个股票的实时数据 - 使用腾讯接口"""
    # 转换代码格式
    if code.endswith('.SH'):
        qt_code = f"sh{code.replace('.SH', '')}"
    elif code.endswith('.SZ'):
        qt_code = f"sz{code.replace('.SZ', '')}"
    elif code.endswith('.HK'):
        qt_code = f"hk{code.replace('.HK', '')}"
    elif code.isdigit():
        if code.startswith('6') or code.startswith('9') or code.startswith('5'):
            qt_code = f"sh{code}"
        elif code.startswith('0') or code.startswith('3'):
            qt_code = f"sz{code}"
        elif code.startswith('8') or code.startswith('4'):
            qt_code = f"bj{code}"
        else:
            return None
    else:
        # 美股等不支持
        return None
    
    url = f"http://qt.gtimg.cn/q={qt_code}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('gbk')
            # 解析数据：v_sh601857="1~中国石油~601857~11.94~12.92~12.18~...~-0.98~-7.59~..."
            match = re.search(r'="([^"]+)"', content)
            if match:
                parts = match.group(1).split('~')
                if len(parts) >= 33:
                    # parts[3] = 当前价，parts[4] = 昨收，parts[31] = 涨跌额，parts[32] = 涨跌幅
                    price = float(parts[3]) if parts[3] else 0
                    prev_close = float(parts[4]) if parts[4] else 0
                    change_amt = float(parts[31]) if len(parts) > 31 and parts[31] else 0
                    change_pct = float(parts[32]) if len(parts) > 32 and parts[32] else 0
                    
                    return {
                        'price': price,
                        'change_pct': change_pct,
                        'change_amt': change_amt,
                        'prev_close': prev_close
                    }
    except Exception as e:
        print(f"Error fetching {code}: {e}")
    return None

results = []
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for stock in stocks:
    code = stock['code']
    name = stock['name']
    
    data = get_stock_data(code)
    if data:
        results.append({
            'code': code,
            'name': name,
            'current_price': data['price'],
            'change_pct': data['change_pct'],
            'change_amt': data['change_amt'],
            'timestamp': timestamp
        })
        print(f"{code} {name}: ¥{data['price']:.2f} {data['change_pct']:+.2f}%")
    else:
        print(f"{code} {name}: 数据获取失败")

# 写入文件
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间\n")
    for r in results:
        f.write(f"{r['code']} | {r['name']} | ¥{r['current_price']:.2f} | {r['change_pct']:+.2f}% | ¥{r['change_amt']:.2f} | {r['timestamp']}\n")

print(f"\n共获取 {len(results)} 只股票数据，已保存到 {output_path}")
