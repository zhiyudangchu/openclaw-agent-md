#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
功能：获取自选股实时数据，应用预警规则，推送 alerts
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加技能路径
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace-main-stock/skills/tushare-data'))

import tushare as ts

# 配置
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORKSPACE, 'stock')
WATCHLIST_FILE = os.path.join(STOCK_DIR, 'watchlist.txt')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
ALERT_RULES_FILE = os.path.join(STOCK_DIR, 'alert-rules.md')
RECEIVER_LIST_FILE = os.path.join(STOCK_DIR, 'receiver-list.txt')
ALERT_TEMPLATE_FILE = os.path.join(STOCK_DIR, 'alert-template.md')

# 日志记录
execution_log = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "api_calls": [],
    "errors": []
}

def log_api_call(api_name, params, result_status):
    """记录 API 调用"""
    execution_log["api_calls"].append({
        "api": api_name,
        "params": params,
        "status": result_status,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def log_error(error_msg):
    """记录错误"""
    execution_log["errors"].append({
        "error": error_msg,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def get_token():
    """获取 Tushare token"""
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        token_file = os.path.expanduser('~/.tushare_token')
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token = f.read().strip()
    return token

def check_market_status(pro):
    """
    检查市场状态：是否收盘、休市或交易时间内
    返回：(is_trading, status_msg)
    """
    today = datetime.now().strftime('%Y%m%d')
    
    try:
        # 获取交易日历
        cal_df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        log_api_call('trade_cal', {'exchange': 'SSE', 'start_date': today, 'end_date': today}, 'success')
        
        if cal_df.empty or cal_df.iloc[0]['is_open'] == 0:
            return False, "今日休市"
        
        # 检查当前时间
        now = datetime.now()
        current_time = now.strftime('%H%M')
        
        # 交易时间：上午 9:30-11:30, 下午 13:00-15:00
        if current_time < '0930':
            return False, "未开盘（早盘前）"
        elif current_time >= '1130' and current_time < '1300':
            return False, "午休时间"
        elif current_time >= '1500':
            return False, "已收盘"
        else:
            return True, "交易时间内"
            
    except Exception as e:
        log_error(f"检查市场状态失败：{str(e)}")
        return True, "默认交易时间（检查失败）"

def load_watchlist():
    """加载自选股列表"""
    watchlist = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    code, name = line.split('|', 1)
                    # 转换为 ts_code 格式
                    if code.endswith('.HK'):
                        ts_code = code  # 港股已经是正确格式
                    elif code.endswith('.SZ') or code.endswith('.SH') or code.endswith('.BJ'):
                        ts_code = code  # A 股已经是正确格式
                    elif code.isdigit():
                        # A 股代码，需要添加后缀
                        if code.startswith('6'):
                            ts_code = f"{code}.SH"
                        elif code.startswith('0') or code.startswith('3'):
                            ts_code = f"{code}.SZ"
                        elif code.startswith('9') or code.startswith('8'):
                            ts_code = f"{code}.BJ"
                        else:
                            ts_code = f"{code}.SH"  # 默认
                    else:
                        # 美股或其他
                        ts_code = code
                    watchlist.append({'ts_code': ts_code, 'name': name, 'original_code': code})
    return watchlist

def get_realtime_data(pro, watchlist):
    """获取实时日线数据"""
    if not watchlist:
        return None
    
    # 分离 A 股、港股、美股
    a_stocks = [s for s in watchlist if s['ts_code'].endswith('.SH') or s['ts_code'].endswith('.SZ') or s['ts_code'].endswith('.BJ')]
    hk_stocks = [s for s in watchlist if s['ts_code'].endswith('.HK')]
    us_stocks = [s for s in watchlist if not s['ts_code'].endswith('.SH') and not s['ts_code'].endswith('.SZ') and not s['ts_code'].endswith('.BJ') and not s['ts_code'].endswith('.HK')]
    
    all_data = []
    
    # 获取 A 股实时数据
    if a_stocks:
        ts_codes = ','.join([s['ts_code'] for s in a_stocks])
        try:
            df = pro.rt_k(ts_code=ts_codes)
            log_api_call('rt_k', {'ts_code': ts_codes}, 'success')
            
            for _, row in df.iterrows():
                all_data.append({
                    'ts_code': row['ts_code'],
                    'name': row['name'],
                    'close': row['close'],
                    'pre_close': row['pre_close'],
                    'pct_change': ((row['close'] - row['pre_close']) / row['pre_close'] * 100) if row['pre_close'] else 0,
                    'change': row['close'] - row['pre_close'],
                    'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                })
        except Exception as e:
            log_error(f"获取 A 股实时数据失败：{str(e)}")
    
    # 获取港股实时数据
    if hk_stocks:
        ts_codes = ','.join([s['ts_code'] for s in hk_stocks])
        try:
            df = pro.hk_rt_k(ts_code=ts_codes)
            log_api_call('hk_rt_k', {'ts_code': ts_codes}, 'success')
            
            for _, row in df.iterrows():
                all_data.append({
                    'ts_code': row['ts_code'],
                    'name': row['name'],
                    'close': row['close'],
                    'pre_close': row['pre_close'],
                    'pct_change': ((row['close'] - row['pre_close']) / row['pre_close'] * 100) if row['pre_close'] else 0,
                    'change': row['close'] - row['pre_close'],
                    'trade_time': row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                })
        except Exception as e:
            log_error(f"获取港股实时数据失败：{str(e)}")
    
    return all_data

def check_alert_rules(data):
    """
    应用预警规则过滤数据
    通用规则：
    - 下跌 > 3% → 触发
    - 上涨 > 5% → 触发
    
    个股专属规则：
    - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%
    """
    alerts = []
    
    for stock in data:
        ts_code = stock['ts_code']
        pct_change = stock['pct_change']
        triggered = False
        reason = ""
        
        # 检查中国石油专属规则
        if ts_code == '601857.SH':
            if pct_change > 2:
                triggered = True
                reason = "🟢 涨幅 > 2%"
            elif pct_change < -1:
                triggered = True
                reason = "🔴 跌幅 > 1%"
        else:
            # 通用规则
            if pct_change < -3:
                triggered = True
                reason = "📉 下跌 > 3%"
            elif pct_change > 5:
                triggered = True
                reason = "📈 上涨 > 5%"
        
        if triggered:
            alerts.append({
                **stock,
                'alert_reason': reason
            })
    
    # 按涨跌幅绝对值排序
    alerts.sort(key=lambda x: abs(x['pct_change']), reverse=True)
    
    return alerts

def format_alert_message(alerts):
    """格式化预警消息"""
    now = datetime.now()
    
    # 表格头部
    lines = [
        "⚠️ **股价预警通知**",
        "",
        "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |",
        "|------|------|--------|--------|--------|------|"
    ]
    
    # 数据行（最多 10 条）
    for alert in alerts[:10]:
        pct_sign = '+' if alert['pct_change'] >= 0 else ''
        change_sign = '+' if alert['change'] >= 0 else ''
        time_str = alert['trade_time'][-5:] if len(alert['trade_time']) > 5 else alert['trade_time']
        
        lines.append(
            f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | ¥{alert['close']:.2f} | "
            f"{pct_sign}{alert['pct_change']:.2f}% | {change_sign}{alert['change']:.2f} | {time_str} |"
        )
    
    lines.extend([
        "",
        "⚙️ **预警规则**",
        "- 📉 下跌 > 3% → 触发",
        "- 📈 上涨 > 5% → 触发",
        "- 🟢 中国石油：涨幅 > 2% → 触发",
        "- 🔴 中国石油：跌幅 > 1% → 触发",
        "",
        f"**数据来源**: Tushare Pro",
        f"**更新时间**: {now.strftime('%Y-%m-%d %H:%M')}"
    ])
    
    return '\n'.join(lines)

def save_realtime_data(data, alerts):
    """保存实时数据到文件"""
    now = datetime.now()
    
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(f"数据时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("数据来源：Tushare Pro\n")
        f.write(f"预警数量：{len(alerts)}\n")
        f.write("-" * 80 + "\n")
        
        for stock in data:
            pct_sign = '+' if stock['pct_change'] >= 0 else ''
            change_sign = '+' if stock['change'] >= 0 else ''
            f.write(f"{stock['ts_code']}|{stock['name']}|{stock['close']:.2f}|{pct_sign}{stock['pct_change']:.2f}|{change_sign}{stock['change']:.2f}|{stock['trade_time']}\n")

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

def send_alerts(receivers, message):
    """发送预警消息"""
    if not receivers:
        return False
    
    targets_args = ' '.join([f'--targets {r}' for r in receivers])
    # 转义消息中的特殊字符
    escaped_message = message.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    
    cmd = f'openclaw message broadcast --channel feishu --account stock {targets_args} --message "{escaped_message}"'
    return cmd

def send_execution_log(log_data):
    """发送执行日志到群聊"""
    now = datetime.now()
    
    log_msg = f"📊 **实时股价监控执行日志**\n\n"
    log_msg += f"**执行时间**: {log_data['timestamp']}\n\n"
    
    log_msg += f"**API 调用记录** ({len(log_data['api_calls'])}次):\n"
    for call in log_data['api_calls']:
        log_msg += f"- {call['time']} | {call['api']} | {call['status']}\n"
    
    if log_data['errors']:
        log_msg += f"\n**错误记录** ({len(log_data['errors'])}个):\n"
        for err in log_data['errors']:
            log_msg += f"- {err['time']} | {err['error']}\n"
    else:
        log_msg += f"\n✅ 无错误\n"
    
    # 转义消息
    escaped_log = log_msg.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    cmd = f'openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message "{escaped_log}"'
    return cmd

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行实时股价监控任务...")
    
    # 获取 token
    token = get_token()
    if not token:
        log_error("未找到 Tushare token")
        print("错误：未找到 Tushare token")
        return
    
    # 初始化 pro
    pro = ts.pro_api(token)
    
    # 步骤 1: 检查市场状态
    print("步骤 1: 检查市场状态...")
    is_trading, status_msg = check_market_status(pro)
    print(f"市场状态：{status_msg}")
    
    if not is_trading:
        print(f"当前{status_msg}，结束任务。")
        # 发送执行日志
        log_cmd = send_execution_log(execution_log)
        print(f"执行日志：{log_cmd}")
        return
    
    # 步骤 2: 清空 realtime-data.txt
    print("步骤 2: 清空实时数据文件...")
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    
    # 步骤 3: 加载自选股并获取实时数据
    print("步骤 3: 获取实时数据...")
    watchlist = load_watchlist()
    print(f"自选股数量：{len(watchlist)}")
    
    data = get_realtime_data(pro, watchlist)
    if not data:
        print("未获取到实时数据，结束任务。")
        log_cmd = send_execution_log(execution_log)
        print(f"执行日志：{log_cmd}")
        return
    
    print(f"获取到 {len(data)} 条股票数据")
    
    # 步骤 4: 应用预警规则
    print("步骤 4: 应用预警规则...")
    alerts = check_alert_rules(data)
    print(f"触发预警数量：{len(alerts)}")
    
    if not alerts:
        print("无预警数据，结束任务。")
        # 保存数据
        save_realtime_data(data, alerts)
        log_cmd = send_execution_log(execution_log)
        print(f"执行日志：{log_cmd}")
        return
    
    # 步骤 5: 保存实时数据
    print("步骤 5: 保存实时数据...")
    save_realtime_data(data, alerts)
    
    # 步骤 6: 加载接收者并发送预警
    print("步骤 6: 发送预警通知...")
    receivers = load_receivers()
    print(f"接收者数量：{len(receivers)}")
    
    if receivers:
        message = format_alert_message(alerts)
        broadcast_cmd = send_alerts(receivers, message)
        print(f"广播命令：{broadcast_cmd}")
    
    # 步骤 7: 发送执行日志
    print("步骤 7: 发送执行日志...")
    log_cmd = send_execution_log(execution_log)
    print(f"执行日志命令：{log_cmd}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务执行完成！")

if __name__ == '__main__':
    main()
