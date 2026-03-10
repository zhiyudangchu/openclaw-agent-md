#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
获取自选股实时数据并应用预警规则
"""

import tushare as ts
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# 基础路径
BASE_DIR = Path(os.path.expanduser('~/.openclaw/workspace-main-stock/stock'))

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

def check_trading_day():
    """检查今日是否为交易日"""
    today = datetime.now().strftime('%Y%m%d')
    try:
        cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, fields='calendar_date,is_open')
        if cal.empty:
            return False
        is_open = cal['is_open'].iloc[0]
        return is_open == 1
    except Exception as e:
        print(f"检查交易日失败：{e}")
        return False

def get_watchlist():
    """读取自选股列表"""
    watchlist = []
    watchlist_file = BASE_DIR / 'watchlist.txt'
    with open(watchlist_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                parts = line.split('|')
                code = parts[0]
                name = parts[1] if len(parts) > 1 else ''
                # 标准化代码格式
                if '.' not in code:
                    if code.isdigit() and len(code) == 6:
                        if code.startswith('6') or code.startswith('9'):
                            code = code + '.SH'
                        else:
                            code = code + '.SZ'
                watchlist.append({'ts_code': code, 'name': name})
    return watchlist

def get_realtime_daily_data(watchlist):
    """获取自选股实时日线数据"""
    results = []
    today_dt = datetime.now()
    today = today_dt.strftime('%Y%m%d')
    yesterday = (today_dt - pd.Timedelta(days=1)).strftime('%Y%m%d')
    
    for stock in watchlist:
        ts_code = stock['ts_code']
        try:
            df = pro.daily(ts_code=ts_code, start_date=yesterday, end_date=today)
            if not df.empty:
                latest = df.iloc[0]
                close = latest['close']
                pre_close = latest['pre_close']
                pct_chg = latest['pct_chg']
                change = close - pre_close
                trade_date = str(latest['trade_date'])
                time_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 15:00:00"
                
                results.append({
                    'ts_code': ts_code,
                    'name': stock['name'],
                    'close': close,
                    'pct_chg': pct_chg,
                    'change': change,
                    'time': time_str,
                    'pre_close': pre_close
                })
        except Exception as e:
            print(f"获取 {ts_code} 数据失败：{e}")
            continue
    
    return results

def apply_alert_rules(data):
    """应用预警规则过滤数据"""
    alerts = []
    
    for item in data:
        ts_code = item['ts_code']
        name = item['name']
        pct_chg = item['pct_chg']
        
        triggered = False
        rule = ''
        
        # 通用规则
        if pct_chg < -3:
            triggered = True
            rule = '📉 下跌 > 3%'
        elif pct_chg > 5:
            triggered = True
            rule = '📈 上涨 > 5%'
        
        # 个股专属规则 - 中国石油 (601857.SH)
        if ts_code == '601857.SH':
            if pct_chg > 2:
                triggered = True
                rule = '🟢 中国石油 涨幅 > 2%'
            elif pct_chg < -1:
                triggered = True
                rule = '🔴 中国石油 跌幅 > 1%'
        
        if triggered:
            alerts.append({
                **item,
                'rule': rule
            })
    
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    return alerts

def save_data(data, alerts):
    """保存数据到文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_file = BASE_DIR / 'realtime-data.txt'
    
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write(f"数据时间：{timestamp}\n")
        f.write("数据来源：Tushare Pro\n")
        f.write("-" * 80 + "\n")
        
        for item in data:
            f.write(f"{item['ts_code']}|{item['name']}|{item['close']:.2f}|{item['pct_chg']:.2f}|{item['change']:.2f}|{item['time']}\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("预警数据:\n")
        f.write("=" * 80 + "\n")
        
        for alert in alerts:
            f.write(f"{alert['ts_code']}|{alert['name']}|{alert['close']:.2f}|{alert['pct_chg']:.2f}|{alert['change']:.2f}|{alert['time']}|{alert['rule']}\n")
    
    return alerts

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return None
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    lines = []
    lines.append("🚨 **股价预警通知** 🚨\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 | 规则 |")
    lines.append("|------|------|--------|--------|-------|------|------|")
    
    for alert in alerts[:10]:
        code = alert['ts_code'].split('.')[0]
        name = alert['name']
        price = f"¥{alert['close']:.2f}"
        pct = f"{alert['pct_chg']:+.2f}%"
        change = f"¥{alert['change']:.2f}"
        time = alert['time'].split(' ')[1][:5]
        rule = alert['rule']
        
        lines.append(f"| {code} | {name} | {price} | {pct} | {change} | {time} | {rule} |")
    
    lines.append("\n\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 中国石油 (601857): 🟢 涨幅 > 2% | 🔴 跌幅 > 1%")
    lines.append(f"\n**数据来源**: Tushare Pro")
    lines.append(f"**更新时间**: {timestamp}")
    
    return "\n".join(lines)

def main():
    print("===== 实时股价监控任务启动 =====")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤 1: 检查是否收盘
    print("\n[步骤 1] 检查交易状态...")
    is_after_hours = datetime.now().hour >= 15 or datetime.now().hour < 9
    if not is_after_hours:
        if not check_trading_day():
            print("今日休市，任务结束")
            return
        print("市场交易中...")
    else:
        print("市场已收盘，获取收盘数据")
    
    # 步骤 2: 清空 realtime-data.txt
    print("\n[步骤 2] 清空历史数据...")
    data_file = BASE_DIR / 'realtime-data.txt'
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write("")
    print("已清空")
    
    # 步骤 3: 获取自选股数据
    print("\n[步骤 3] 获取自选股实时数据...")
    watchlist = get_watchlist()
    print(f"自选股数量：{len(watchlist)}")
    
    data = get_realtime_daily_data(watchlist)
    print(f"成功获取数据：{len(data)} 只股票")
    
    # 步骤 4: 应用预警规则
    print("\n[步骤 4] 应用预警规则过滤...")
    alerts = apply_alert_rules(data)
    print(f"触发预警：{len(alerts)} 只股票")
    
    # 步骤 5: 保存数据
    print("\n[步骤 5] 保存数据...")
    save_data(data, alerts)
    print("数据已保存")
    
    # 步骤 6: 如果有预警，输出消息格式
    if alerts:
        print("\n[步骤 6] 生成预警消息...")
        message = format_alert_message(alerts)
        print("\n" + "=" * 80)
        print(message)
        print("=" * 80)
        print("\n[广播命令]")
        print("请将以下消息通过飞书推送给接收者")
    else:
        print("\n无触发预警的股票，任务结束")

if __name__ == "__main__":
    main()
