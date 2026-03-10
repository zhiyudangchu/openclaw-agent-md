#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据
"""

import tushare as ts
import pandas as pd
import os
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表 (从 watchlist.txt 读取)
watchlist = [
    '601857.SH',  # 中国石油
    '601808.SH',  # 中海油服
    '600256.SH',  # 广汇能源
    '600583.SH',  # 海油工程
    '000852.SZ',  # 石化机械
    '600547.SH',  # 山东黄金
    '601069.SH',  # 西部黄金
    '600988.SH',  # 赤峰黄金
    '000975.SZ',  # 银泰黄金
    '002716.SZ',  # 金贵银业
    '601899.SH',  # 紫金矿业
    '688111.SH',  # 金山办公
]

def get_realtime_daily_data():
    """
    获取实时日线数据
    使用 pro.daily 接口获取最新交易日数据
    """
    try:
        # 获取最新交易日数据（不指定日期，获取最新）
        # ts_code 支持多个代码，用逗号分隔
        ts_codes = ','.join(watchlist)
        
        # 获取日线数据
        data = pro.daily(ts_code=ts_codes)
        
        # 按 ts_code 和 trade_date 排序，获取每只股票的最新数据
        data = data.sort_values('trade_date', ascending=False)
        latest_data = data.groupby('ts_code').first().reset_index()
        
        return latest_data
    except Exception as e:
        print(f"获取数据失败：{e}")
        return None

def format_output(data):
    """
    格式化输出数据
    格式：代码 | 名称 | 最新价 | 涨跌幅%|涨跌额 | 时间点
    """
    if data is None or len(data) == 0:
        return []
    
    results = []
    for _, row in data.iterrows():
        ts_code = row['ts_code']
        # 计算涨跌幅
        pct_chg = row['pct_chg'] if 'pct_chg' in row else 0
        # 计算涨跌额 = 当前价 - 昨收价
        close = row['close']
        pre_close = row['pre_close'] if 'pre_close' in row else close
        change = close - pre_close
        
        # 格式化时间点
        trade_date = str(row['trade_date'])
        if len(trade_date) == 8:
            trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 15:00:00"
        
        # 获取股票名称（从 ts_code 映射）
        name_map = {
            '601857.SH': '中国石油',
            '601808.SH': '中海油服',
            '600256.SH': '广汇能源',
            '600583.SH': '海油工程',
            '000852.SZ': '石化机械',
            '600547.SH': '山东黄金',
            '601069.SH': '西部黄金',
            '600988.SH': '赤峰黄金',
            '000975.SZ': '银泰黄金',
            '002716.SZ': '金贵银业',
            '601899.SH': '紫金矿业',
            '688111.SH': '金山办公',
        }
        name = name_map.get(ts_code, ts_code)
        
        results.append({
            'ts_code': ts_code,
            'name': name,
            'close': close,
            'pct_chg': pct_chg,
            'change': change,
            'trade_date': trade_date
        })
    
    return results

def main():
    print("===== 获取自选股实时日线数据 =====")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取数据
    data = get_realtime_daily_data()
    
    if data is not None:
        print(f"获取到 {len(data)} 只股票数据")
        
        # 格式化输出
        results = format_output(data)
        
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
