#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时日线数据
"""
import os
import sys
import json
from datetime import datetime
import tushare as ts

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

if not token:
    print("ERROR: TUSHARE_TOKEN 环境变量未设置")
    sys.exit(1)

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

# 获取实时日线数据
ts_code_param = ",".join(stocks)
print(f"请求参数：ts_code={ts_code_param}")

try:
    df = pro.rt_k(ts_code=ts_code_param)
    print(f"返回数据行数：{len(df)}")
    print(f"返回列名：{list(df.columns)}")
    print("\n数据内容：")
    print(df.to_string())
    
    # 转换为 JSON 输出
    result = []
    for idx, row in df.iterrows():
        record = {
            "ts_code": row.get("ts_code", ""),
            "name": row.get("name", ""),
            "pre_close": float(row.get("pre_close", 0)) if row.get("pre_close") is not None else 0,
            "close": float(row.get("close", 0)) if row.get("close") is not None else 0,
            "high": float(row.get("high", 0)) if row.get("high") is not None else 0,
            "open": float(row.get("open", 0)) if row.get("open") is not None else 0,
            "low": float(row.get("low", 0)) if row.get("low") is not None else 0,
            "vol": int(row.get("vol", 0)) if row.get("vol") is not None else 0,
            "amount": int(row.get("amount", 0)) if row.get("amount") is not None else 0,
            "trade_time": row.get("trade_time", ""),
        }
        # 计算涨跌幅和涨跌额
        if record["pre_close"] > 0:
            record["change"] = record["close"] - record["pre_close"]
            record["pct_chg"] = (record["change"] / record["pre_close"]) * 100
        else:
            record["change"] = 0
            record["pct_chg"] = 0
        result.append(record)
    
    # 输出 JSON 格式数据
    print("\n===JSON 输出===")
    output = {
        "code": 0,
        "message": "success",
        "data": {
            "items": result,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    output = {
        "code": -1,
        "message": str(e),
        "data": None
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(1)
