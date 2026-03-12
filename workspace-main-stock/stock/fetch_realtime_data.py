#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
获取自选股实时日线数据，应用预警规则，输出预警信息
"""

import os
import sys
import json
from datetime import datetime

# 添加 tushare
import tushare as ts

# 工作路径
WORK_DIR = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORK_DIR, 'stock')

# 文件路径
STOCK_LIST_FILE = os.path.join(STOCK_DIR, 'stock-list.txt')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
ALERT_RULES_FILE = os.path.join(STOCK_DIR, 'alert-rules.md')

def read_stock_list():
    """读取自选股列表"""
    stocks = []
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                code = parts[0]
                name = parts[1]
                board = parts[2]
                # 转换为 ts_code 格式
                if board == 'SH':
                    ts_code = f"{code}.SH"
                elif board == 'SZ':
                    ts_code = f"{code}.SZ"
                else:
                    ts_code = f"{code}.{board}"
                stocks.append({'code': code, 'name': name, 'ts_code': ts_code, 'board': board})
    return stocks

def get_realtime_data(stocks):
    """获取实时日线数据"""
    # 获取环境变量中的 token
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("错误：未找到 TUSHARE_TOKEN 环境变量")
        sys.exit(1)
    
    # 初始化 pro 接口
    pro = ts.pro_api(token)
    
    # 构建 ts_code 列表
    ts_codes = [s['ts_code'] for s in stocks]
    ts_code_str = ','.join(ts_codes)
    
    print(f"获取实时数据：{ts_code_str}")
    
    try:
        # 调用 rt_k 接口获取实时日线
        df = pro.rt_k(ts_code=ts_code_str)
        print(f"获取到 {len(df)} 条数据")
        print(f"数据列：{df.columns.tolist()}")
        print(f"数据内容:\n{df.to_string()}")
        return df
    except Exception as e:
        print(f"获取数据失败：{e}")
        return None

def check_alert_rules(row, stock_info):
    """
    检查是否满足预警规则
    返回：(是否触发预警，预警类型)
    """
    # 计算涨跌幅
    pre_close = row['pre_close']
    close = row['close']
    pct_change = ((close - pre_close) / pre_close) * 100
    
    code = row['ts_code']
    name = stock_info.get('name', '')
    
    # 通用规则：下跌 > 1% 或 上涨 > 1%
    if pct_change < -1.0:
        return True, '下跌>1%'
    if pct_change > 1.0:
        return True, '上涨>1%'
    
    # 个股专属规则：中国石油 (601857.SH)
    if code == '601857.SH':
        if pct_change > 2.0:
            return True, '中国石油涨幅>2%'
        if pct_change < -1.0:
            return True, '中国石油跌幅>1%'
    
    return False, None

def format_alert_data(df, stocks):
    """格式化预警数据"""
    # 构建股票信息映射
    stock_map = {s['ts_code']: s for s in stocks}
    
    alerts = []
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        stock_info = stock_map.get(ts_code, {})
        
        # 检查预警规则
        triggered, rule_type = check_alert_rules(row, stock_info)
        if triggered:
            # 计算涨跌额
            change = row['close'] - row['pre_close']
            pct_change = (change / row['pre_close']) * 100
            
            alerts.append({
                'ts_code': ts_code,
                'code': ts_code.split('.')[0],
                'name': row.get('name', stock_info.get('name', '')),
                'close': row['close'],
                'pre_close': row['pre_close'],
                'change': change,
                'pct_change': pct_change,
                'rule': rule_type,
                'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            })
    
    # 按涨跌幅绝对值排序
    alerts.sort(key=lambda x: abs(x['pct_change']), reverse=True)
    
    return alerts

def save_realtime_data(df, alerts):
    """保存实时数据和预警数据到文件"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# 实时数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 预警数据条数：{len(alerts)}\n\n")
        
        if alerts:
            f.write("## 预警数据\n")
            f.write("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 | 触发规则 |\n")
            f.write("|------|------|--------|--------|--------|------|----------|\n")
            for alert in alerts:
                time_str = alert['trade_time']
                if len(time_str) > 8:
                    time_str = time_str[-8:]  # 只保留 HH:MM:SS
                f.write(f"| {alert['code']} | {alert['name']} | ¥{alert['close']:.2f} | {alert['pct_change']:+.2f}% | ¥{alert['change']:.2f} | {time_str} | {alert['rule']} |\n")
        else:
            f.write("## 无预警数据\n")
        
        f.write(f"\n## 全部实时数据\n")
        f.write(df.to_string())
    
    return alerts

def main():
    print("=" * 60)
    print("实时股价监控任务开始")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 读取自选股列表
    print("\n[步骤 1] 读取自选股列表...")
    stocks = read_stock_list()
    print(f"自选股数量：{len(stocks)}")
    for s in stocks:
        print(f"  - {s['ts_code']} {s['name']}")
    
    # 2. 获取实时日线数据
    print("\n[步骤 2] 获取实时日线数据...")
    df = get_realtime_data(stocks)
    if df is None or len(df) == 0:
        print("未获取到数据，任务结束")
        return
    
    # 3. 检查预警规则并过滤
    print("\n[步骤 3] 应用预警规则过滤...")
    alerts = format_alert_data(df, stocks)
    print(f"触发预警的股票数量：{len(alerts)}")
    
    # 4. 保存数据
    print("\n[步骤 4] 保存数据到文件...")
    alerts = save_realtime_data(df, alerts)
    print(f"数据已保存到：{REALTIME_DATA_FILE}")
    
    # 5. 输出预警信息（用于后续推送）
    print("\n[步骤 5] 预警信息输出...")
    if alerts:
        print("触发预警的股票:")
        for alert in alerts:
            print(f"  - {alert['code']} {alert['name']}: {alert['pct_change']:+.2f}% ({alert['rule']})")
    else:
        print("无预警股票")
    
    # 6. 输出 JSON 格式数据（用于消息推送）
    print("\n[步骤 6] 输出 JSON 格式预警数据...")
    output = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': len(stocks),
        'alert_count': len(alerts),
        'alerts': alerts
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 60)
    print("实时股价监控任务结束")
    print("=" * 60)

if __name__ == '__main__':
    main()
