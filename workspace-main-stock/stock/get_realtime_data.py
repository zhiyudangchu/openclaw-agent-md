#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取自选股实时数据并检查预警规则
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加 tushare
import tushare as ts

# 获取 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 读取自选股列表
watchlist_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
watchlist = []
with open(watchlist_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            code, name = line.split('|', 1)
            watchlist.append({'code': code, 'name': name})

print(f"自选股数量：{len(watchlist)}")
print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 检查交易日历 - 获取今天是否是交易日
today = datetime.now()
today_str = today.strftime('%Y%m%d')

# 获取昨天日期（用于 fallback）
yesterday = today - timedelta(days=1)
if yesterday.weekday() == 5:  # Saturday
    yesterday = today - timedelta(days=2)
elif yesterday.weekday() == 6:  # Sunday
    yesterday = today - timedelta(days=3)
yesterday_str = yesterday.strftime('%Y%m%d')

try:
    # 获取交易日历
    cal_df = pro.trade_cal(exchange='SSE', start_date=today_str, end_date=today_str, is_open='1')
    if cal_df.empty:
        print(f"今天 ({today_str}) 不是交易日，使用昨天数据")
        use_date = yesterday_str
    else:
        print(f"今天 ({today_str}) 是交易日")
        use_date = today_str
except Exception as e:
    print(f"获取交易日历失败：{e}")
    use_date = yesterday_str

# 检查当前时间是否在交易时间内
current_hour = datetime.now().hour
current_minute = datetime.now().minute
current_time = current_hour * 60 + current_minute

# A 股交易时间：9:30-11:30, 13:00-15:00
afternoon_end = 15 * 60  # 900

if current_time > afternoon_end:
    print(f"当前时间 {current_hour}:{current_minute:02d} 已收盘")
    # 收盘后数据可能还未更新，尝试获取今天数据，如果为空则用昨天
    try_get_today = True
else:
    try_get_today = True

# 构建 ts_code 列表
ts_codes = []
for stock in watchlist:
    code = stock['code']
    # 处理不同市场的代码格式
    if code.endswith('.SH') or code.endswith('.SZ') or code.endswith('.HK'):
        ts_codes.append(code)
    elif code.isdigit():
        # A 股代码，需要根据代码判断市场
        if code.startswith('6') or code.startswith('9'):
            ts_codes.append(f"{code}.SH")
        elif code.startswith('0') or code.startswith('3'):
            ts_codes.append(f"{code}.SZ")
        else:
            ts_codes.append(f"{code}.SH")
    else:
        # 美股或其他
        ts_codes.append(code)

print(f"请求代码：{ts_codes}")
print(f"使用日期：{use_date}")

# 获取日线数据
df = None
try:
    ts_code_str = ','.join(ts_codes)
    print(f"获取日线数据：{ts_code_str}")
    
    # 先尝试获取今天的数据
    df = pro.query('daily', ts_code=ts_code_str, start_date=today_str, end_date=today_str)
    
    if df.empty:
        print(f"今日数据为空，尝试获取 {yesterday_str} 数据")
        df = pro.query('daily', ts_code=ts_code_str, start_date=yesterday_str, end_date=yesterday_str)
        data_date = yesterday_str
    else:
        data_date = today_str
    
    if df.empty:
        print("未获取到任何数据")
        sys.exit(0)
    
    print(f"获取到 {len(df)} 条数据，数据日期：{data_date}")
    
except Exception as e:
    print(f"获取数据失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 读取预警规则
alert_rules_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-rules.md')
with open(alert_rules_path, 'r', encoding='utf-8') as f:
    alert_rules_content = f.read()

# 解析预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
# 个股专属规则：中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%

general_down_threshold = -3.0  # 下跌 > 3%
general_up_threshold = 5.0     # 上涨 > 5%

# 个股专属规则
special_rules = {
    '601857.SH': {'up': 2.0, 'down': -1.0},  # 中国石油
}

# 过滤满足预警规则的数据
alert_data = []
for idx, row in df.iterrows():
    ts_code = row['ts_code']
    pct_chg = row['pct_chg'] if 'pct_chg' in row else 0
    close = row['close'] if 'close' in row else 0
    pre_close = row['pre_close'] if 'pre_close' in row else close / (1 + pct_chg/100) if pct_chg != 0 else close
    change = row['change'] if 'change' in row else close - pre_close
    
    # 获取股票名称
    stock_name = ''
    for stock in watchlist:
        stock_code = stock['code']
        if stock_code.endswith('.SH') or stock_code.endswith('.SZ'):
            if stock_code == ts_code:
                stock_name = stock['name']
                break
        else:
            # 处理不带后缀的代码
            base_code = ts_code.split('.')[0]
            if base_code == stock_code:
                stock_name = stock['name']
                break
    
    # 检查预警规则
    triggered = False
    rule_desc = ''
    
    # 检查是否有专属规则
    if ts_code in special_rules:
        rule = special_rules[ts_code]
        if pct_chg >= rule['up']:
            triggered = True
            rule_desc = f"🟢 涨幅 {pct_chg:.2f}% > {rule['up']}%"
        elif pct_chg <= rule['down']:
            triggered = True
            rule_desc = f"🔴 跌幅 {pct_chg:.2f}% < {rule['down']}%"
    else:
        # 通用规则
        if pct_chg >= general_up_threshold:
            triggered = True
            rule_desc = f"📈 上涨 {pct_chg:.2f}% > {general_up_threshold}%"
        elif pct_chg <= general_down_threshold:
            triggered = True
            rule_desc = f"📉 下跌 {pct_chg:.2f}% < {general_down_threshold}%"
    
    if triggered:
        alert_data.append({
            'code': ts_code.split('.')[0],
            'name': stock_name,
            'close': close,
            'pct_chg': pct_chg,
            'change': change,
            'time': datetime.now().strftime('%H:%M'),
            'rule': rule_desc
        })

print(f"\n触发预警的股票数量：{len(alert_data)}")

# 保存原始数据
output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
df.to_csv(output_path, index=False, encoding='utf-8')
print(f"原始数据已保存到：{output_path}")

# 保存预警数据
if alert_data:
    alert_df = pd.DataFrame(alert_data)
    # 按涨跌幅排序
    alert_df = alert_df.sort_values('pct_chg', ascending=False)
    
    alert_output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-data.txt')
    alert_df.to_csv(alert_output_path, index=False, encoding='utf-8')
    print(f"预警数据已保存到：{alert_output_path}")
    
    # 输出预警数据
    print("\n=== 预警数据 ===")
    print(alert_df.to_string(index=False))
else:
    print("\n无触发预警的股票")
    # 创建空的预警数据文件
    alert_output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-data.txt')
    with open(alert_output_path, 'w', encoding='utf-8') as f:
        f.write('')

print("\n数据处理完成")
