#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据
"""

import tushare as ts
import os
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表
stocks = [
    "601857.SH",  # 中国石油
    "603606.SH",  # 东方电缆
    "002600.SZ",  # 领益智造
    "002961.SZ",  # 瑞达期货
    "001872.SZ",  # 招商港口
]

def get_realtime_data():
    """
    获取实时日线数据
    """
    try:
        # 批量获取数据
        ts_codes = ",".join(stocks)
        print(f"获取实时数据：{ts_codes}")
        
        data = pro.rt_k(ts_code=ts_codes)
        
        if data.empty:
            print("未获取到数据")
            return None
        
        print(f"获取到 {len(data)} 条数据")
        print(data)
        
        # 格式化输出
        now = datetime.now()
        output_lines = []
        output_lines.append(f"# 实时股价数据 - 更新时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"# 数据来源：Tushare Pro (rt_k 接口)")
        output_lines.append("")
        output_lines.append("代码\t名称\t最新价\t昨收价\t涨跌幅%\t涨跌额\t开盘价\t最高价\t最低价\t成交量\t成交额\t时间")
        
        for idx, row in data.iterrows():
            ts_code = row['ts_code']
            code = ts_code.split('.')[0]
            name = row['name']
            close = row['close']  # 最新价
            pre_close = row['pre_close']  # 昨收价
            
            # 计算涨跌幅和涨跌额
            change_pct = ((close - pre_close) / pre_close) * 100
            change_amt = close - pre_close
            
            open_price = row['open']
            high = row['high']
            low = row['low']
            vol = row['vol']
            amount = row['amount']
            
            trade_time = row.get('trade_time', now.strftime('%H:%M:%S'))
            
            output_lines.append(f"{code}\t{name}\t{close:.2f}\t{pre_close:.2f}\t{change_pct:+.2f}%\t{change_amt:+.2f}\t{open_price:.2f}\t{high:.2f}\t{low:.2f}\t{vol}\t{amount}\t{trade_time}")
        
        return "\n".join(output_lines)
        
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = get_realtime_data()
    if result:
        print("\n=== 输出结果 ===")
        print(result)
        # 保存到文件
        with open(os.path.join(os.path.dirname(__file__), 'realtime-data.txt'), 'w', encoding='utf-8') as f:
            f.write(result)
        print("\n数据已保存到 realtime-data.txt")
    else:
        print("获取数据失败")
