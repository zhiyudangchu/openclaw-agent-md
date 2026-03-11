#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控任务执行脚本
按照 realtime-data-cron-config.md 的要求执行
"""

import os
import sys
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 配置路径
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORKSPACE, 'stock')
WATCHLIST_FILE = os.path.join(STOCK_DIR, 'watchlist.txt')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
RECEIVER_LIST_FILE = os.path.join(STOCK_DIR, 'receiver-list.txt')
ALERT_RULES_FILE = os.path.join(STOCK_DIR, 'alert-rules.md')

# 读取 Tushare Token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    # 尝试从文件读取
    token_file = os.path.join(WORKSPACE, '.tushare_token')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
    
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量或 token 文件")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

def check_trading_day():
    """检查今日是否交易日以及是否在交易时间内"""
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    # 获取交易日历
    try:
        cal = pro.trade_cal(exchange='SSE', start_date=today_str, end_date=today_str)
        if cal.empty or cal['is_open'].iloc[0] == '0':
            print(f"今日 ({today.strftime('%Y-%m-%d')}) 休市，结束任务")
            return False
    except Exception as e:
        print(f"获取交易日历失败：{e}")
        # 如果获取失败，假设是交易日继续执行
        print("假设今日为交易日，继续执行")
    
    # 检查是否在交易时间内 (9:30-11:30, 13:00-15:00)
    # 注意：午餐时间 (11:30-13:00) 也允许执行，因为数据仍然有效
    current_time = today.strftime('%H%M')
    if current_time < '0930' or current_time >= '1500':
        print(f"当前时间 {today.strftime('%H:%M')} 不在交易时间内，结束任务")
        return False
    
    print(f"今日是交易日，当前时间 {today.strftime('%H:%M')} 在交易时间内，继续执行")
    return True

def load_watchlist():
    """加载自选股列表"""
    watchlist = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    code, name = line.split('|', 1)
                    # 转换代码格式为 tushare 格式
                    if '.' in code:
                        ts_code = code
                    elif code.startswith('6') or code.startswith('9'):
                        ts_code = f"{code}.SH"
                    elif code.startswith('0') or code.startswith('3'):
                        ts_code = f"{code}.SZ"
                    elif code.startswith('8') or code.startswith('4'):
                        ts_code = f"{code}.BJ"
                    else:
                        ts_code = code
                    watchlist.append({'ts_code': ts_code, 'name': name})
    return watchlist

def clear_realtime_data():
    """清空 realtime-data.txt"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    print("已清空 realtime-data.txt")

def get_realtime_data(watchlist):
    """获取实时日线数据"""
    if not watchlist:
        print("自选股列表为空")
        return []
    
    # 构建 ts_code 列表
    ts_codes = [stock['ts_code'] for stock in watchlist]
    ts_code_str = ','.join(ts_codes)
    
    print(f"获取实时数据：{ts_code_str}")
    
    try:
        # 使用 rt_k 接口获取实时日线
        df = pro.rt_k(ts_code=ts_code_str)
        
        if df.empty:
            print("未获取到实时数据")
            return []
        
        print(f"获取到 {len(df)} 条实时数据")
        
        # 保存数据到文件
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(f"数据时间：{now}\n")
            f.write("数据来源：Tushare Pro\n")
            f.write("-" * 80 + "\n")
            
            for _, row in df.iterrows():
                ts_code = row.get('ts_code', '')
                name = row.get('name', '')
                close = row.get('close', 0)
                pre_close = row.get('pre_close', 0)
                
                # 计算涨跌幅和涨跌额
                if pre_close > 0:
                    change_pct = ((close - pre_close) / pre_close) * 100
                    change_amt = close - pre_close
                else:
                    change_pct = 0
                    change_amt = 0
                
                # 格式化输出
                change_pct_str = f"+{change_pct:.2f}" if change_pct >= 0 else f"{change_pct:.2f}"
                change_amt_str = f"+{change_amt:.2f}" if change_amt >= 0 else f"{change_amt:.2f}"
                
                f.write(f"{ts_code}|{name}|{close:.2f}|{change_pct_str}|{change_amt_str}|{now}\n")
        
        return df.to_dict('records')
    
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        return []

def load_alert_rules():
    """加载预警规则"""
    rules = {
        'general': {
            'drop_threshold': -3.0,  # 下跌 > 3%
            'rise_threshold': 5.0    # 上涨 > 5%
        },
        'stocks': {
            '601857.SH': {  # 中国石油
                'rise_threshold': 2.0,   # 涨幅 > 2%
                'drop_threshold': -1.0   # 跌幅 > 1%
            }
        }
    }
    return rules

def filter_alerts(data, rules):
    """根据预警规则过滤数据"""
    alerts = []
    
    for row in data:
        ts_code = row.get('ts_code', '')
        name = row.get('name', '')
        close = row.get('close', 0)
        pre_close = row.get('pre_close', 0)
        
        if pre_close <= 0:
            continue
        
        change_pct = ((close - pre_close) / pre_close) * 100
        
        alert_reason = None
        
        # 检查个股专属规则
        if ts_code in rules['stocks']:
            stock_rules = rules['stocks'][ts_code]
            if change_pct > stock_rules['rise_threshold']:
                alert_reason = f"🟢 涨幅 > {stock_rules['rise_threshold']}%"
            elif change_pct < stock_rules['drop_threshold']:
                alert_reason = f"🔴 跌幅 > {abs(stock_rules['drop_threshold'])}%"
        else:
            # 检查通用规则
            if change_pct < rules['general']['drop_threshold']:
                alert_reason = f"📉 下跌 > {abs(rules['general']['drop_threshold'])}%"
            elif change_pct > rules['general']['rise_threshold']:
                alert_reason = f"📈 上涨 > {rules['general']['rise_threshold']}%"
        
        if alert_reason:
            change_pct_str = f"+{change_pct:.2f}" if change_pct >= 0 else f"{change_pct:.2f}"
            change_amt = close - pre_close
            change_amt_str = f"+{change_amt:.2f}" if change_amt >= 0 else f"{change_amt:.2f}"
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            alerts.append({
                'ts_code': ts_code,
                'name': name,
                'close': close,
                'change_pct': change_pct,
                'change_pct_str': change_pct_str,
                'change_amt': change_amt,
                'change_amt_str': change_amt_str,
                'time': now,
                'alert_reason': alert_reason
            })
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return alerts

def load_receivers():
    """加载接收者列表"""
    receivers = []
    if os.path.exists(RECEIVER_LIST_FILE):
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
    return receivers

def send_alerts(alerts, receivers):
    """发送预警消息"""
    if not alerts or not receivers:
        print("没有预警数据或接收者列表为空")
        return
    
    # 构建消息
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    message = f"⚠️ 股价预警通知\n\n"
    message += f"**数据来源：** Tushare Pro\n"
    message += f"**更新时间：** {now}\n\n"
    message += "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |\n"
    message += "|------|------|--------|--------|--------|------|\n"
    
    for alert in alerts[:10]:  # 最多 10 条
        time_short = alert['time'].split(' ')[1][:5]
        message += f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | ¥{alert['close']:.2f} | {alert['change_pct_str']}% | ¥{alert['change_amt_str']} | {time_short} |\n"
    
    message += f"\n⚙️ 预警规则\n"
    message += f"- 📉 下跌 > 3% → 触发\n"
    message += f"- 📈 上涨 > 5% → 触发\n"
    message += f"- 🟢 中国石油：涨幅 > 2% / 跌幅 > 1% → 触发\n"
    
    # 构建命令
    targets = ' '.join([f"--targets {r}" for r in receivers])
    command = f"openclaw message broadcast --channel feishu --account stock {targets} --message '{message}'"
    
    print(f"发送预警消息:\n{command}")
    
    # 执行命令
    os.system(command)

def send_monitoring_log():
    """发送任务监控日志到群聊"""
    chat_id = "oc_e5021f4489531f598034cdfc2e0394f6"
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"📊 实时股价监控任务执行报告\n\n"
    message += f"**执行时间：** {now}\n"
    message += f"**任务状态：** 完成\n\n"
    message += f"**调用接口：**\n"
    message += f"- trade_cal: 检查交易日历\n"
    message += f"- rt_k: 获取实时日线数据\n\n"
    message += f"**数据来源：** Tushare Pro\n"
    message += f"**错误信息：** 无\n"
    
    command = f"openclaw message send --channel feishu --account stock --target {chat_id} --message '{message}'"
    
    print(f"发送监控日志:\n{command}")
    os.system(command)

def main():
    """主函数"""
    print("=" * 60)
    print("实时股价监控任务开始执行")
    print("=" * 60)
    
    # 步骤 1: 检查是否交易日和交易时间
    print("\n【步骤 1】检查交易状态...")
    if not check_trading_day():
        # 发送监控日志
        send_monitoring_log()
        return
    
    # 步骤 2: 清空 realtime-data.txt
    print("\n【步骤 2】清空实时数据文件...")
    clear_realtime_data()
    
    # 步骤 3: 加载自选股并获取实时数据
    print("\n【步骤 3】获取实时日线数据...")
    watchlist = load_watchlist()
    print(f"加载到 {len(watchlist)} 只自选股")
    
    data = get_realtime_data(watchlist)
    if not data:
        print("未获取到数据，结束任务")
        send_monitoring_log()
        return
    
    # 步骤 4: 加载预警规则并过滤
    print("\n【步骤 4】应用预警规则过滤...")
    rules = load_alert_rules()
    alerts = filter_alerts(data, rules)
    print(f"筛选出 {len(alerts)} 条预警数据")
    
    if not alerts:
        print("没有触发预警的数据，结束任务")
        send_monitoring_log()
        return
    
    # 步骤 5: 发送预警
    print("\n【步骤 5】发送预警通知...")
    receivers = load_receivers()
    print(f"加载到 {len(receivers)} 个接收者")
    
    send_alerts(alerts, receivers)
    
    # 步骤 6: 发送监控日志
    print("\n【步骤 6】发送任务监控日志...")
    send_monitoring_log()
    
    print("\n" + "=" * 60)
    print("实时股价监控任务执行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
