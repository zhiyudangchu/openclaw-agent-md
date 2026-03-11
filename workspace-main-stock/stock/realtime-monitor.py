#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
功能：
1. 检查今日是否收盘
2. 获取自选股实时日线数据
3. 按预警规则过滤
4. 输出预警数据
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 初始化 tushare
import tushare as ts

token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 文件路径
WATCHLIST_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
REALTIME_DATA_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
ALERT_RULES_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-rules.md')

# 记录接口调用日志
api_logs = []

def log_api_call(interface, params, result_count, status='success', error=None):
    """记录 API 调用"""
    api_logs.append({
        'interface': interface,
        'params': params,
        'result_count': result_count,
        'status': status,
        'error': error,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def check_market_status():
    """检查今日是否收盘或休市"""
    today = datetime.now().strftime('%Y%m%d')
    weekday = datetime.now().weekday()
    
    # 周末休市
    if weekday >= 5:
        print(f"今日是周末，市场休市")
        return False
    
    # 检查交易日历
    try:
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        if df.empty or df.iloc[0]['is_open'] == 0:
            print(f"今日 ({today}) 是休市日")
            log_api_call('trade_cal', {'exchange': 'SSE', 'start_date': today, 'end_date': today}, 0)
            return False
        log_api_call('trade_cal', {'exchange': 'SSE', 'start_date': today, 'end_date': today}, 1)
    except Exception as e:
        print(f"检查交易日历失败：{e}")
        log_api_call('trade_cal', {'exchange': 'SSE', 'start_date': today, 'end_date': today}, 0, 'error', str(e))
        return False
    
    # 检查当前时间（A 股交易时间：9:30-11:30, 13:00-15:00）
    now = datetime.now()
    current_time = now.strftime('%H%M')
    
    # 未开盘或已收盘
    if current_time < '0930' or current_time > '1500':
        print(f"当前时间 {current_time}，市场未开盘或已收盘")
        return False
    
    print(f"市场交易中，当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    return True

def load_watchlist():
    """加载自选股列表"""
    watchlist = []
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                code, name = line.split('|', 1)
                # 转换代码格式
                if '.' not in code:
                    if code.startswith('6'):
                        code = f"{code}.SH"
                    elif code.startswith('0') or code.startswith('3'):
                        code = f"{code}.SZ"
                    elif code.startswith('9') or code.startswith('8'):
                        code = f"{code}.BJ"
                watchlist.append({'ts_code': code, 'name': name})
    return watchlist

def get_realtime_data(watchlist):
    """获取实时日线数据"""
    # 构建 ts_code 参数，支持批量获取
    ts_codes = ','.join([stock['ts_code'] for stock in watchlist])
    
    try:
        print(f"获取实时日线数据：{ts_codes}")
        df = pro.rt_k(ts_code=ts_codes)
        log_api_call('rt_k', {'ts_code': ts_codes}, len(df) if df is not None else 0)
        
        if df is None or df.empty:
            print("未获取到实时数据")
            return None
        
        print(f"成功获取 {len(df)} 条实时数据")
        return df
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        log_api_call('rt_k', {'ts_code': ts_codes}, 0, 'error', str(e))
        return None

def apply_alert_rules(df):
    """
    应用预警规则过滤数据
    通用规则：
    - 下跌 > 3% → 触发
    - 上涨 > 5% → 触发
    
    个股专属规则：
    - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1% → 触发
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 计算涨跌幅
    df['pct_chg'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
    
    alert_data = []
    
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        pct_chg = row['pct_chg']
        name = row.get('name', '')
        
        triggered = False
        reason = ''
        
        # 检查个股专属规则
        if ts_code == '601857.SH':  # 中国石油
            if pct_chg > 2:
                triggered = True
                reason = '🟢 涨幅 > 2%'
            elif pct_chg < -1:
                triggered = True
                reason = '🔴 跌幅 > 1%'
        else:
            # 通用规则
            if pct_chg < -3:
                triggered = True
                reason = '📉 下跌 > 3%'
            elif pct_chg > 5:
                triggered = True
                reason = '📈 上涨 > 5%'
        
        if triggered:
            alert_data.append({
                'ts_code': ts_code,
                'name': name,
                'close': row['close'],
                'pct_chg': pct_chg,
                'change_amount': round(row['close'] - row['pre_close'], 2),
                'trade_time': row.get('trade_time', datetime.now().strftime('%Y%m%d%H%M%S')),
                'reason': reason
            })
    
    if alert_data:
        result_df = pd.DataFrame(alert_data)
        # 按涨跌幅排序
        result_df = result_df.sort_values('pct_chg', ascending=False)
        return result_df
    
    return pd.DataFrame()

def format_alert_message(df):
    """格式化预警消息为表格形式"""
    if df is None or df.empty:
        return ""
    
    lines = []
    lines.append("🚨 **股价预警通知** 🚨\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 | 触发原因 |")
    lines.append("|------|------|--------|--------|--------|------|----------|")
    
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        close = f"¥{row['close']:.2f}"
        pct_chg = f"{row['pct_chg']:+.2f}%"
        change_amount = f"¥{row['change_amount']:+.2f}"
        # 格式化时间
        trade_time = row['trade_time']
        if len(str(trade_time)) >= 12:
            time_str = f"{str(trade_time)[8:10]}:{str(trade_time)[10:12]}"
        else:
            time_str = datetime.now().strftime('%H:%M')
        reason = row['reason']
        
        lines.append(f"| {ts_code.split('.')[0]} | {name} | {close} | {pct_chg} | {change_amount} | {time_str} | {reason} |")
    
    lines.append("\n")
    lines.append("⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 中国石油：🟢 涨幅 > 2% / 🔴 跌幅 > 1% → 触发")
    lines.append("\n")
    lines.append(f"**数据来源**: Tushare Pro")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def save_realtime_data(df):
    """保存实时数据到文件"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        if df is not None and not df.empty:
            f.write(df.to_csv(index=False, sep='|'))
        else:
            f.write('')
    print(f"实时数据已保存到 {REALTIME_DATA_FILE}")

def load_receiver_list():
    """加载接收者列表"""
    receiver_file = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    receivers = []
    with open(receiver_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    return receivers

def get_api_logs_message():
    """生成 API 调用日志消息"""
    lines = []
    lines.append("📊 **任务执行日志**\n")
    lines.append(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**调用接口数**: {len(api_logs)}\n")
    
    for log in api_logs:
        status_emoji = '✅' if log['status'] == 'success' else '❌'
        lines.append(f"{status_emoji} **接口**: {log['interface']}")
        lines.append(f"   参数：{log['params']}")
        lines.append(f"   结果数：{log['result_count']}")
        lines.append(f"   状态：{log['status']}")
        if log['error']:
            lines.append(f"   错误：{log['error']}")
        lines.append(f"   时间：{log['timestamp']}")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    print("=" * 60)
    print("实时股价监控任务启动")
    print("=" * 60)
    
    # 步骤 1: 检查市场状态
    print("\n【步骤 1】检查市场状态...")
    if not check_market_status():
        print("市场已收盘或休市，任务结束")
        # 即使市场休市，也要记录日志
        log_api_call('market_status_check', {}, 0, 'success', '市场休市')
        return get_api_logs_message()
    
    # 步骤 2: 清空 realtime-data.txt
    print("\n【步骤 2】清空实时数据文件...")
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    print("已清空 realtime-data.txt")
    
    # 步骤 3: 加载自选股并获取实时数据
    print("\n【步骤 3】获取实时日线数据...")
    watchlist = load_watchlist()
    print(f"自选股数量：{len(watchlist)}")
    
    realtime_df = get_realtime_data(watchlist)
    if realtime_df is None or realtime_df.empty:
        print("未获取到有效数据，任务结束")
        return get_api_logs_message()
    
    # 保存实时数据
    save_realtime_data(realtime_df)
    
    # 步骤 4: 应用预警规则
    print("\n【步骤 4】应用预警规则过滤...")
    alert_df = apply_alert_rules(realtime_df)
    
    if alert_df is None or alert_df.empty:
        print("无满足预警规则的数据，任务结束")
        return get_api_logs_message()
    
    print(f"满足预警规则的股票数：{len(alert_df)}")
    
    # 步骤 5: 格式化预警消息
    print("\n【步骤 5】格式化预警消息...")
    alert_message = format_alert_message(alert_df)
    print("\n" + alert_message)
    
    # 步骤 6: 加载接收者列表并构建命令
    print("\n【步骤 6】准备发送预警通知...")
    receivers = load_receiver_list()
    print(f"接收者数量：{len(receivers)}")
    
    # 构建飞书推送命令
    targets_args = ' '.join([f'--targets {r}' for r in receivers])
    # 对消息内容进行转义，避免 shell 解析问题
    safe_message = alert_message.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    send_command = f'openclaw message broadcast --channel feishu --account stock {targets_args} --message "{safe_message}"'
    
    print("\n飞书推送命令:")
    print(send_command)
    
    # 返回需要执行的命令和日志
    return {
        'alert_message': alert_message,
        'send_command': send_command,
        'receivers': receivers,
        'api_logs': get_api_logs_message()
    }

if __name__ == '__main__':
    result = main()
    
    # 输出结果供 shell 脚本使用
    if isinstance(result, dict):
        print("\n" + "=" * 60)
        print("任务执行完成")
        print("=" * 60)
        # 将命令写入临时文件
        with open('/tmp/stock_alert_command.sh', 'w') as f:
            f.write(result['send_command'])
        print(f"\n预警推送命令已写入 /tmp/stock_alert_command.sh")
        
        # 将 API 日志写入临时文件
        with open('/tmp/stock_api_logs.txt', 'w') as f:
            f.write(result['api_logs'])
        print(f"API 日志已写入 /tmp/stock_api_logs.txt")
    else:
        # 市场休市等情况
        with open('/tmp/stock_api_logs.txt', 'w') as f:
            f.write(result)
        print(f"API 日志已写入 /tmp/stock_api_logs.txt")
