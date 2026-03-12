#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
获取自选股实时日线数据，应用预警规则，推送预警信息
"""

import tushare as ts
import pandas as pd
import os
import json
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
pro = ts.pro_api(token)

# 自选股列表
STOCKS = [
    "601857.SH",  # 中国石油
    "603606.SH",  # 东方电缆
    "002600.SZ",  # 领益智造
    "002961.SZ",  # 瑞达期货
    "001872.SZ",  # 招商港口
]

# 预警规则
# 通用规则：涨跌 > 1%
# 中国石油专属：涨幅 > 2% 或 跌幅 > 1%
def check_alert(stock_code, stock_name, pct_chg):
    """
    检查是否触发预警
    """
    # 通用规则：涨跌绝对值 > 1%
    if abs(pct_chg) > 1.0:
        return True
    
    # 中国石油专属规则：涨幅 > 2% 或 跌幅 > 1%
    if stock_code == "601857.SH":
        if pct_chg > 2.0 or pct_chg < -1.0:
            return True
    
    return False

def get_realtime_data():
    """
    获取实时日线数据
    rt_k 接口返回字段：ts_code, name, pre_close, high, open, low, close, vol, amount, num, trade_time
    """
    try:
        # 使用 rt_k 接口获取实时日线数据
        ts_codes = ",".join(STOCKS)
        df = pro.rt_k(ts_code=ts_codes)
        
        # 计算涨跌幅和涨跌额
        df['change'] = df['close'] - df['pre_close']
        df['pct_chg'] = (df['change'] / df['pre_close']) * 100
        
        print(f"获取到 {len(df)} 条实时数据")
        print(df[['ts_code', 'name', 'pre_close', 'close', 'change', 'pct_chg']])
        return df
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        import traceback
        traceback.print_exc()
        return None

def format_alert_data(df):
    """
    格式化预警数据为表格形式
    """
    result = []
    
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        close = row['close']
        pct_chg = row.get('pct_chg', 0)
        change = row.get('change', 0)
        
        # 格式化涨跌幅显示
        if pct_chg >= 0:
            pct_str = f"+{pct_chg:.2f}%"
        else:
            pct_str = f"{pct_chg:.2f}%"
        
        result.append({
            "ts_code": ts_code,
            "name": name,
            "close": close,
            "pct_chg": pct_chg,
            "pct_str": pct_str,
            "change": change
        })
    
    # 按涨跌幅绝对值排序
    result.sort(key=lambda x: abs(x['pct_chg']), reverse=True)
    
    return result

def main():
    """
    主函数
    """
    print("===== 实时股价监控 =====")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取实时数据
    df = get_realtime_data()
    
    if df is None or len(df) == 0:
        print("未获取到数据，可能是休市时间")
        return {"status": "no_data", "message": "未获取到数据"}
    
    # 检查是否满足预警条件
    alert_stocks = []
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        pct_chg = row.get('pct_chg', 0)
        
        if check_alert(ts_code, name, pct_chg):
            alert_stocks.append(row)
            print(f"预警：{name} ({ts_code}) 涨跌幅：{pct_chg:.2f}%")
    
    if len(alert_stocks) == 0:
        print("无预警股票")
        return {"status": "no_alert", "message": "无预警股票"}
    
    # 格式化预警数据
    alert_df = pd.DataFrame(alert_stocks)
    alert_data = format_alert_data(alert_df)
    
    # 输出 JSON 格式数据到文件
    output = {
        "items": [],
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    for stock in alert_data:
        output["items"].append({
            "ts_code": stock["ts_code"],
            "name": stock["name"],
            "close": round(stock["close"], 2),
            "pct_chg": round(stock["pct_chg"], 2),
            "change": round(stock["change"], 2)
        })
    
    # 写入文件
    output_path = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n预警数据已写入：{output_path}")
    print(f"预警股票数量：{len(alert_stocks)}")
    
    # 返回预警数据用于推送
    return {"status": "success", "data": output, "count": len(alert_stocks)}

if __name__ == "__main__":
    result = main()
    print(f"\n执行结果：{json.dumps(result, ensure_ascii=False)}")
