#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取股票实时日线数据
调用 rt_k 接口，获取指定股票的实时日线数据
"""

import os
import json
import tushare as ts

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    exit(1)

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 要查询的股票代码
ts_code = '603606.SH,002600.SZ,002961.SZ,001872.SZ'

try:
    # 调用 rt_k 接口获取实时日线数据
    df = pro.rt_k(ts_code=ts_code)
    
    # 将 DataFrame 转换为字典格式以便完整展示
    result = {
        'status': 'success',
        'msg': '数据获取成功',
        'data': {
            'columns': df.columns.tolist(),
            'records': df.to_dict('records'),
            'shape': list(df.shape)
        }
    }
    
    # 输出完整的 JSON 结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    error_result = {
        'status': 'error',
        'msg': str(e),
        'data': None
    }
    print(json.dumps(error_result, ensure_ascii=False, indent=2))
