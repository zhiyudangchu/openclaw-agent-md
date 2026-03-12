#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控 Cron 任务
按照 realtime-data-cron-config.md 的要求执行完整流程
"""

import os
import sys
import json
import subprocess
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
RECEIVER_LIST_FILE = os.path.join(STOCK_DIR, 'receiver-list.txt')
ALERT_TEMPLATE_FILE = os.path.join(STOCK_DIR, 'alert-template.md')

# 任务监控日志
TASK_LOG = {
    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'api_calls': [],
    'errors': []
}

def log_api_call(api_name, params, result_status, result_summary=''):
    """记录 API 调用"""
    TASK_LOG['api_calls'].append({
        'api': api_name,
        'params': params,
        'status': result_status,
        'result': result_summary,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def log_error(error_msg, context=''):
    """记录错误"""
    TASK_LOG['errors'].append({
        'error': error_msg,
        'context': context,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def read_stock_list():
    """读取自选股列表"""
    stocks = []
    try:
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
        log_api_call('read_stock_list', {'file': STOCK_LIST_FILE}, 'success', f'{len(stocks)} stocks')
    except Exception as e:
        log_error(str(e), 'read_stock_list')
        raise
    return stocks

def check_market_status():
    """
    检查市场是否收盘或休市
    返回：True=未收盘/未休市，False=已收盘/休市
    """
    try:
        # 获取环境变量中的 token
        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            log_error('未找到 TUSHARE_TOKEN 环境变量', 'check_market_status')
            return False
        
        pro = ts.pro_api(token)
        
        # 获取交易日历
        today = datetime.now().strftime('%Y%m%d')
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, fields='cal_date,is_open')
        
        if df.empty:
            log_error('无法获取交易日历', 'check_market_status')
            return False
        
        is_open = df.iloc[0]['is_open']
        log_api_call('trade_cal', {'date': today}, 'success', f'is_open={is_open}')
        
        if is_open == 0:
            print(f"今日 ({today}) 休市")
            return False
        
        # 检查当前时间是否在交易时间内
        current_time = datetime.now()
        hour = current_time.hour
        minute = current_time.minute
        
        # A 股交易时间：9:30-11:30, 13:00-15:00
        is_trading_time = False
        if (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30):
            is_trading_time = True
        elif (hour == 13) or (hour == 14) or (hour == 15 and minute <= 0):
            is_trading_time = True
        
        if not is_trading_time:
            print(f"当前时间 {current_time.strftime('%H:%M')} 已收盘")
            return False
        
        return True
        
    except Exception as e:
        log_error(str(e), 'check_market_status')
        return False

def clear_realtime_data():
    """清空 realtime-data.txt 文件"""
    try:
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        print(f"已清空 {REALTIME_DATA_FILE}")
    except Exception as e:
        log_error(str(e), 'clear_realtime_data')
        raise

def get_realtime_data(stocks):
    """获取实时日线数据"""
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        log_error('未找到 TUSHARE_TOKEN 环境变量', 'get_realtime_data')
        return None
    
    pro = ts.pro_api(token)
    
    # 构建 ts_code 列表
    ts_codes = [s['ts_code'] for s in stocks]
    ts_code_str = ','.join(ts_codes)
    
    print(f"获取实时数据：{ts_code_str}")
    
    try:
        # 调用 rt_k 接口获取实时日线
        df = pro.rt_k(ts_code=ts_code_str)
        print(f"获取到 {len(df)} 条数据")
        
        log_api_call('rt_k', {'ts_code': ts_code_str}, 'success', f'{len(df)} records')
        
        return df
    except Exception as e:
        log_error(str(e), 'get_realtime_data')
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
        return True, '🔴 跌幅 > 1%'
    if pct_change > 1.0:
        return True, '📈 上涨 > 1%'
    
    # 个股专属规则：中国石油 (601857.SH)
    if code == '601857.SH':
        if pct_change > 2.0:
            return True, '🟢 涨幅 > 2%'
        if pct_change < -1.0:
            return True, '🔴 跌幅 > 1%'
    
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
            
            # 处理时间
            trade_time = row.get('trade_time', '')
            if not trade_time:
                trade_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            alerts.append({
                'ts_code': ts_code,
                'code': ts_code.split('.')[0],
                'name': row.get('name', stock_info.get('name', '')),
                'close': row['close'],
                'pre_close': row['pre_close'],
                'change': change,
                'pct_change': pct_change,
                'rule': rule_type,
                'trade_time': trade_time
            })
    
    # 按涨跌幅绝对值排序
    alerts.sort(key=lambda x: abs(x['pct_change']), reverse=True)
    
    return alerts

def save_realtime_data(df, alerts):
    """保存实时数据和预警数据到文件"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# 实时数据更新时间：{current_time}\n")
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
    
    print(f"数据已保存到：{REALTIME_DATA_FILE}")
    return alerts

def load_receivers():
    """加载接收者列表"""
    receivers = []
    try:
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
        log_api_call('load_receivers', {'file': RECEIVER_LIST_FILE}, 'success', f'{len(receivers)} receivers')
    except Exception as e:
        log_error(str(e), 'load_receivers')
        raise
    return receivers

def build_alert_message(alerts):
    """构建预警消息"""
    current_time = datetime.now().strftime('%H:%M')
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    lines = []
    lines.append("🚨 **股价预警通知** 🚨\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for alert in alerts:
        pct_str = f"{alert['pct_change']:+.2f}%"
        change_str = f"¥{alert['change']:+.2f}"
        
        # 提取时间（HH:mm）
        time_str = alert['trade_time']
        if len(time_str) > 8:
            time_str = time_str[-8:][:5]
        
        lines.append(f"| {alert['code']} | {alert['name']} | ¥{alert['close']:.2f} | {pct_str} | {change_str} | {time_str} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 1% → 触发")
    lines.append("- 📈 上涨 > 1% → 触发")
    lines.append("- 🟢 中国石油涨幅 > 2% → 触发")
    lines.append("- 🔴 中国石油跌幅 > 1% → 触发")
    lines.append(f"\n**【数据来源】**")
    lines.append(f"- 数据来源：Tushare Pro")
    lines.append(f"- 更新时间：{update_time}")
    
    return '\n'.join(lines)

def send_alerts(message, receivers):
    """发送预警消息到飞书"""
    # 构建命令
    cmd = [
        'openclaw', 'message', 'broadcast',
        '--channel', 'feishu',
        '--account', 'stock'
    ]
    
    # 添加接收者
    for receiver in receivers:
        cmd.extend(['--targets', receiver])
    
    # 添加消息
    cmd.extend(['--message', message])
    
    print(f"执行命令：{' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        log_api_call('send_broadcast', 
                    {'receivers': len(receivers), 'message_len': len(message)}, 
                    'success' if result.returncode == 0 else 'failed',
                    result.stdout[:200] if result.stdout else '')
        
        if result.returncode != 0:
            log_error(f"发送失败：{result.stderr}", 'send_alerts')
            return False
        
        print(f"消息发送成功!")
        return True
    except Exception as e:
        log_error(str(e), 'send_alerts')
        return False

def send_task_log():
    """发送任务监控日志到群聊"""
    chat_id = 'oc_e5021f4489531f598034cdfc2e0394f6'
    
    # 构建日志消息
    log_message = []
    log_message.append("📊 **实时股价监控任务执行日志**")
    log_message.append(f"执行时间：{TASK_LOG['start_time']}")
    log_message.append(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message.append("")
    
    # API 调用统计
    log_message.append(f"**API 调用次数**: {len(TASK_LOG['api_calls'])}")
    for call in TASK_LOG['api_calls']:
        log_message.append(f"- {call['api']}: {call['status']} ({call['result']})")
    
    log_message.append("")
    
    # 错误统计
    if TASK_LOG['errors']:
        log_message.append(f"**错误数量**: {len(TASK_LOG['errors'])}")
        for err in TASK_LOG['errors']:
            log_message.append(f"- ❌ {err['error']} ({err['context']})")
    else:
        log_message.append("**错误数量**: 0")
    
    message = '\n'.join(log_message)
    
    # 构建命令
    cmd = [
        'openclaw', 'message', 'send',
        '--channel', 'feishu',
        '--account', 'stock',
        '--target', chat_id,
        '--message', message
    ]
    
    print(f"发送任务日志到群聊：{' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("任务日志发送成功!")
        else:
            print(f"任务日志发送失败：{result.stderr}")
            log_error(f"发送日志失败：{result.stderr}", 'send_task_log')
    except Exception as e:
        log_error(str(e), 'send_task_log')
        print(f"发送任务日志失败：{e}")

def main():
    print("=" * 60)
    print("实时股价监控 Cron 任务开始")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 步骤 1: 检查市场状态
        print("\n[步骤 1] 检查市场状态...")
        if not check_market_status():
            print("市场已收盘或休市，任务结束")
            TASK_LOG['end_reason'] = 'market_closed'
            send_task_log()
            return
        
        print("市场交易中，继续执行...")
        
        # 步骤 2: 读取自选股列表
        print("\n[步骤 2] 读取自选股列表...")
        stocks = read_stock_list()
        print(f"自选股数量：{len(stocks)}")
        for s in stocks:
            print(f"  - {s['ts_code']} {s['name']}")
        
        # 步骤 3: 清空 realtime-data.txt
        print("\n[步骤 3] 清空 realtime-data.txt...")
        clear_realtime_data()
        
        # 步骤 4: 获取实时日线数据
        print("\n[步骤 4] 获取实时日线数据...")
        df = get_realtime_data(stocks)
        if df is None or len(df) == 0:
            print("未获取到数据，任务结束")
            TASK_LOG['end_reason'] = 'no_data'
            send_task_log()
            return
        
        # 步骤 5: 应用预警规则过滤
        print("\n[步骤 5] 应用预警规则过滤...")
        alerts = format_alert_data(df, stocks)
        print(f"触发预警的股票数量：{len(alerts)}")
        
        # 步骤 6: 保存数据
        print("\n[步骤 6] 保存数据到文件...")
        save_realtime_data(df, alerts)
        
        # 步骤 7: 检查是否有预警数据
        if len(alerts) == 0:
            print("无预警数据，任务结束")
            TASK_LOG['end_reason'] = 'no_alerts'
            send_task_log()
            return
        
        # 步骤 8: 加载接收者列表
        print("\n[步骤 7] 加载接收者列表...")
        receivers = load_receivers()
        print(f"接收者数量：{len(receivers)}")
        
        # 步骤 9: 构建预警消息
        print("\n[步骤 8] 构建预警消息...")
        message = build_alert_message(alerts)
        print(f"\n消息内容:\n{message}\n")
        
        # 步骤 10: 发送预警消息
        print("\n[步骤 9] 发送预警消息...")
        send_alerts(message, receivers)
        
        # 步骤 11: 发送任务监控日志
        print("\n[步骤 10] 发送任务监控日志...")
        send_task_log()
        
        print("\n" + "=" * 60)
        print("实时股价监控 Cron 任务完成")
        print("=" * 60)
        
    except Exception as e:
        log_error(str(e), 'main')
        print(f"\n任务执行失败：{e}")
        send_task_log()
        sys.exit(1)

if __name__ == '__main__':
    main()
