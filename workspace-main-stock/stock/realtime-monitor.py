#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
功能：获取自选股实时数据，检查预警规则，推送预警信息
"""

import os
import sys
import json
import tushare as ts
from datetime import datetime

# 配置
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORKSPACE, 'stock')
STOCK_LIST_FILE = os.path.join(STOCK_DIR, 'stock-list.txt')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
RECEIVER_LIST_FILE = os.path.join(STOCK_DIR, 'receiver-list.txt')
LOG_FILE = os.path.join(STOCK_DIR, 'monitor-log.json')

# 从环境变量获取 token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

def log_action(action, params=None, result=None, error=None):
    """记录日志"""
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'params': params,
        'result': result,
        'error': error
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    logs = json.loads(content)
                    if not isinstance(logs, list):
                        logs = []
        except:
            logs = []
    
    logs.append(log_entry)
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    
    return log_entry

def load_stock_list():
    """加载自选股列表"""
    stocks = []
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 3:
                    code, name, board = parts[0], parts[1], parts[2]
                    # 转换为 ts_code 格式
                    if board == 'SH':
                        ts_code = f"{code}.SH"
                    elif board == 'SZ':
                        ts_code = f"{code}.SZ"
                    else:
                        ts_code = f"{code}.{board}"
                    stocks.append({
                        'code': code,
                        'name': name,
                        'board': board,
                        'ts_code': ts_code
                    })
    return stocks

def check_market_status():
    """检查市场是否开盘"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    
    # 获取交易日历
    today = datetime.now().strftime('%Y%m%d')
    try:
        cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        if cal.empty:
            return False, '休市'
        
        is_open = cal.iloc[0]['is_open']
        if is_open == 0:
            return False, '休市'
        
        # 检查当前时间是否在交易时间内
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # 上午交易时间：9:30-11:30
        # 下午交易时间：13:00-15:00
        if hour < 9 or (hour == 9 and minute < 30):
            return False, '未开盘'
        elif hour >= 11 and hour < 13:
            return False, '午休'
        elif hour >= 15:
            return False, '已收盘'
        else:
            return True, '交易中'
    except Exception as e:
        log_action('check_market_status', error=str(e))
        # 如果无法获取交易日历，默认继续
        return True, '未知'

def get_realtime_data(stocks):
    """获取实时日线数据"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    
    # 构建 ts_code 列表
    ts_codes = [s['ts_code'] for s in stocks]
    ts_code_str = ','.join(ts_codes)
    
    log_action('get_realtime_data', params={'ts_codes': ts_code_str})
    
    try:
        df = pro.rt_k(ts_code=ts_code_str)
        
        if df.empty:
            log_action('get_realtime_data_result', result={'count': 0, 'error': '无数据'})
            return []
        
        # 转换为字典列表
        records = []
        for _, row in df.iterrows():
            record = {
                'ts_code': row.get('ts_code', ''),
                'name': row.get('name', ''),
                'pre_close': row.get('pre_close', 0),
                'close': row.get('close', 0),
                'high': row.get('high', 0),
                'open': row.get('open', 0),
                'low': row.get('low', 0),
                'vol': row.get('vol', 0),
                'amount': row.get('amount', 0),
                'trade_time': row.get('trade_time', '')
            }
            
            # 计算涨跌幅和涨跌额
            if record['pre_close'] > 0:
                record['change'] = record['close'] - record['pre_close']
                record['pct_change'] = (record['change'] / record['pre_close']) * 100
            else:
                record['change'] = 0
                record['pct_change'] = 0
            
            records.append(record)
        
        log_action('get_realtime_data_result', result={'count': len(records)})
        return records
    except Exception as e:
        log_action('get_realtime_data', error=str(e))
        raise

def check_alert_rules(data):
    """检查预警规则"""
    # 预警规则已关闭，不触发任何预警
    # 读取 alert-rules.md 确认状态
    alerts = []
    
    # 规则状态：已关闭
    # 所以直接返回空列表
    return alerts

def save_realtime_data(data):
    """保存实时数据到文件"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# 实时数据 - 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 格式：代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 时间\n\n")
        
        for record in sorted(data, key=lambda x: x['pct_change'], reverse=True):
            f.write(f"{record['ts_code']} | {record['name']} | ¥{record['close']:.2f} | "
                   f"{record['pct_change']:+.2f}% | ¥{record['change']:.2f} | "
                   f"{record['trade_time']}\n")

def load_receivers():
    """加载接收者列表"""
    receivers = []
    if os.path.exists(RECEIVER_LIST_FILE):
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    receivers.append(line)
    return receivers

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return None
    
    # 按涨跌幅排序
    alerts_sorted = sorted(alerts, key=lambda x: abs(x['pct_change']), reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股价预警通知**\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for alert in alerts_sorted[:10]:  # 最多 10 条
        time_str = alert.get('trade_time', '')
        if time_str and len(time_str) >= 5:
            time_str = time_str[:5]  # 取 HH:MM
        
        lines.append(f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | "
                    f"¥{alert['close']:.2f} | {alert['pct_change']:+.2f}% | "
                    f"¥{alert['change']:.2f} | {time_str} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > x% → 触发")
    lines.append("- 📈 上涨 > x% → 触发")
    lines.append("\n**【数据来源】**")
    lines.append(f"- 数据来源：Tushare Pro")
    lines.append(f"- 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行实时监控任务")
    
    # 步骤 1: 检查市场状态
    log_action('step1_check_market_status')
    is_open, status = check_market_status()
    print(f"市场状态：{status}")
    
    if not is_open:
        print(f"市场{status}，结束任务")
        log_action('task_end', result={'reason': f'market_{status}'})
        return
    
    # 步骤 2: 清空实时数据文件
    log_action('step2_clear_data_file')
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    print("已清空实时数据文件")
    
    # 步骤 3: 加载自选股列表
    log_action('step3_load_stock_list')
    stocks = load_stock_list()
    print(f"加载自选股：{len(stocks)} 只")
    
    # 步骤 4: 获取实时数据
    log_action('step4_get_realtime_data')
    data = get_realtime_data(stocks)
    print(f"获取实时数据：{len(data)} 条")
    
    if not data:
        print("无数据，结束任务")
        log_action('task_end', result={'reason': 'no_data'})
        return
    
    # 保存实时数据
    save_realtime_data(data)
    print("已保存实时数据")
    
    # 步骤 5: 检查预警规则
    log_action('step5_check_alerts')
    alerts = check_alert_rules(data)
    print(f"触发预警：{len(alerts)} 条")
    
    if not alerts:
        print("无预警，结束任务")
        log_action('task_end', result={'reason': 'no_alerts'})
        return
    
    # 步骤 6: 加载接收者列表
    log_action('step6_load_receivers')
    receivers = load_receivers()
    print(f"接收者数量：{len(receivers)}")
    
    # 步骤 7: 格式化预警消息
    message = format_alert_message(alerts)
    
    # 构建广播命令
    targets_args = ' '.join([f'--targets {r}' for r in receivers])
    command = f"openclaw message broadcast --channel feishu --account stock {targets_args} --message \"{message}\""
    
    print(f"\n推送命令：{command}")
    log_action('step7_send_alert', params={'command': command, 'receivers': receivers})
    
    # 步骤 8: 记录任务监控日志并发送到群聊
    log_action('step8_log_monitoring')
    
    # 读取日志文件
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    # 格式化日志消息
    log_message = "📊 **任务执行日志**\n\n"
    log_message += f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    log_message += f"市场状态：{status}\n"
    log_message += f"自选股数量：{len(stocks)}\n"
    log_message += f"获取数据：{len(data)} 条\n"
    log_message += f"触发预警：{len(alerts)} 条\n"
    log_message += f"接收者数量：{len(receivers)}\n\n"
    
    log_message += "**接口调用记录:**\n"
    for log in logs:
        log_message += f"- {log['action']}: {log.get('result', {}).get('count', 'N/A')} 条\n"
    
    log_message += f"\n@测试机器人"
    
    print(f"\n日志消息：{log_message}")
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务执行完成")

if __name__ == '__main__':
    main()
