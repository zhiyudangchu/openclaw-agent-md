#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据 (使用 rt_k 接口)
"""

import tushare as ts
import os
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表 (从 watchlist.txt 读取)
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
watchlist = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|')
            # 转换代码格式
            if '.' in code:
                watchlist.append(code)
            elif code.endswith('HK'):
                watchlist.append(code)  # 港股保持原样
            else:
                # A 股，添加后缀
                if code.startswith('6') or code.startswith('9'):
                    watchlist.append(f"{code}.SH")
                else:
                    watchlist.append(f"{code}.SZ")

def get_realtime_data():
    """
    获取实时日线数据
    使用 rt_k 接口获取实时数据
    """
    results = []
    for ts_code in watchlist:
        try:
            # 实时日线接口
            df = pro.query('rt_k', ts_code=ts_code)
            if len(df) > 0:
                row = df.iloc[0]
                results.append({
                    'ts_code': ts_code,
                    'name': row.get('name', ts_code),
                    'close': float(row.get('close', 0)),
                    'pre_close': float(row.get('pre_close', 0)),
                    'pct_chg': float(row.get('pct_chg', 0)) if 'pct_chg' in row else ((float(row.get('close', 0)) - float(row.get('pre_close', 0))) / float(row.get('pre_close', 1)) * 100 if float(row.get('pre_close', 0)) > 0 else 0),
                    'change': float(row.get('close', 0)) - float(row.get('pre_close', 0)),
                    'trade_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            print(f"获取 {ts_code} 失败：{e}")
            continue
    
    return results

def main():
    print("===== 获取自选股实时日线数据 (rt_k 接口) =====")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"自选股数量：{len(watchlist)}")
    
    # 获取数据
    results = get_realtime_data()
    
    if results:
        print(f"成功获取 {len(results)} 只股票数据")
        
        # 输出到文件
        output_lines = []
        output_lines.append(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("数据来源：Tushare Pro")
        output_lines.append("-" * 80)
        
        for r in results:
            line = f"{r['ts_code']}|{r['name']}|{r['close']:.2f}|{r['pct_chg']:.2f}|{r['change']:.2f}|{r['trade_date']}"
            output_lines.append(line)
            print(line)
        
        # 写入文件
        output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"\n数据已保存到：{output_path}")
    else:
        print("获取数据失败")

if __name__ == "__main__":
    main()
