#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控任务执行脚本
按照 realtime-data-cron-config.md 的要求执行
"""

import os
import sys
import tushare as ts
from datetime import datetime

# 工作路径
WORK_DIR = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORK_DIR, 'stock')

# 文件路径
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
WATCHLIST_FILE = os.path.join(STOCK_DIR, 'watchlist.txt')
ALERT_RULES_FILE = os.path.join(STOCK_DIR, 'alert-rules.md')
RECEIVER_LIST_FILE = os.path.join(STOCK_DIR, 'receiver-list.txt')

# 日志记录
task_log = []

def log_message(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {msg}"
    task_log.append(log_entry)
    print(log_entry)

def check_trading_day():
    """步骤 1: 检查今日是否交易日以及是否在交易时间内"""
    log_message("步骤 1: 检查交易日状态")
    
    try:
        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            log_message("错误: 未找到 TUSHARE_TOKEN 环境变量")
            return False
        
        pro = ts.pro_api(token)
        
        # 获取今天日期
        today = datetime.now().strftime('%Y%m%d')
        
        # 查询交易日历
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        
        if df.empty:
            log_message(f"错误: 无法获取 {today} 的交易日历")
            return False
        
        is_open = df.iloc[0]['is_open']
        
        if is_open == '0':
            log_message(f"今日 ({today}) 休市，结束任务")
            return False
        
        # 检查当前时间是否在交易时间内
        now = datetime.now()
        current_time = now.strftime('%H%M')
        
        # 上午交易时间：9:30-11:30，下午交易时间：13:00-15:00
        is_trading_time = (
            ('0930' <= current_time <= '1130') or 
            ('1300' <= current_time <= '1500')
        )
        
        if not is_trading_time:
            log_message(f"当前时间 {current_time} 不在交易时间内，结束任务")
            return False
        
        log_message(f"今日是交易日，当前在交易时间内，继续执行")
        return True
        
    except Exception as e:
        log_message(f"检查交易日状态时出错：{str(e)}")
        return False

def clear_realtime_data():
    """步骤 2: 清空 realtime-data.txt"""
    log_message("步骤 2: 清空实时数据文件")
    
    try:
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        log_message("实时数据文件已清空")
        return True
    except Exception as e:
        log_message(f"清空文件时出错：{str(e)}")
        return False

def get_watchlist():
    """获取自选股列表"""
    try:
        stocks = []
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    code, name = line.split('|')
                    # 转换代码格式为 tushare 格式
                    if '.' not in code:
                        if code.startswith('6') or code.startswith('9'):
                            code = f"{code}.SH"
                        elif code.startswith('0') or code.startswith('3'):
                            code = f"{code}.SZ"
                        elif code.startswith('4') or code.startswith('8'):
                            code = f"{code}.BJ"
                    stocks.append({'code': code, 'name': name})
        log_message(f"获取到 {len(stocks)} 只自选股")
        return stocks
    except Exception as e:
        log_message(f"读取自选股列表时出错：{str(e)}")
        return []

def fetch_realtime_data(stocks):
    """步骤 3: 获取实时日线数据"""
    log_message("步骤 3: 获取实时日线数据")
    
    try:
        token = os.getenv('TUSHARE_TOKEN')
        pro = ts.pro_api(token)
        
        # 构建 ts_code 列表
        ts_codes = [stock['code'] for stock in stocks]
        ts_code_str = ','.join(ts_codes)
        
        log_message(f"请求 rt_k 接口，代码：{ts_code_str}")
        
        # 调用 rt_k 接口获取实时日线数据
        df = pro.rt_k(ts_code=ts_code_str)
        
        if df.empty:
            log_message("警告: 未获取到实时数据")
            return None
        
        log_message(f"成功获取 {len(df)} 条实时数据")
        
        # 保存到文件
        save_data = []
        for _, row in df.iterrows():
            close = row.get('close', 0)
            pre_close = row.get('pre_close', 0)
            
            # 计算涨跌幅和涨跌额
            if pre_close > 0:
                change_pct = ((close - pre_close) / pre_close) * 100
                change_amt = close - pre_close
            else:
                change_pct = 0
                change_amt = 0
            
            # 获取交易时间
            trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            data_line = {
                'ts_code': row.get('ts_code', ''),
                'name': row.get('name', ''),
                'close': close,
                'pre_close': pre_close,
                'change_pct': change_pct,
                'change_amt': change_amt,
                'trade_time': trade_time,
                'high': row.get('high', 0),
                'open': row.get('open', 0),
                'low': row.get('low', 0),
                'vol': row.get('vol', 0),
                'amount': row.get('amount', 0)
            }
            save_data.append(data_line)
        
        # 写入文件
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            for item in save_data:
                f.write(f"{item['ts_code']}|{item['name']}|{item['close']}|{item['change_pct']}|{item['change_amt']}|{item['trade_time']}\n")
        
        log_message(f"实时数据已保存到 {REALTIME_DATA_FILE}")
        return save_data
        
    except Exception as e:
        log_message(f"获取实时数据时出错：{str(e)}")
        return None

def check_alert_rules(data):
    """步骤 4: 按照预警规则过滤数据"""
    log_message("步骤 4: 应用预警规则过滤")
    
    alert_stocks = []
    
    # 通用规则
    general_down_threshold = -3.0  # 下跌 > 3%
    general_up_threshold = 5.0     # 上涨 > 5%
    
    # 个股专属规则
    special_rules = {
        '601857.SH': {'up': 2.0, 'down': -1.0}  # 中国石油
    }
    
    for item in data:
        ts_code = item['ts_code']
        change_pct = item['change_pct']
        triggered = False
        rule_desc = ""
        
        # 检查是否有特殊规则
        if ts_code in special_rules:
            rule = special_rules[ts_code]
            if change_pct > rule['up']:
                triggered = True
                rule_desc = f"特殊规则：涨幅>{rule['up']}%"
            elif change_pct < rule['down']:
                triggered = True
                rule_desc = f"特殊规则：跌幅>{abs(rule['down'])}%"
        else:
            # 通用规则
            if change_pct < general_down_threshold:
                triggered = True
                rule_desc = f"通用规则：下跌>{abs(general_down_threshold)}%"
            elif change_pct > general_up_threshold:
                triggered = True
                rule_desc = f"通用规则：上涨>{general_up_threshold}%"
        
        if triggered:
            item['alert_rule'] = rule_desc
            alert_stocks.append(item)
            log_message(f"预警触发：{item['name']} ({ts_code}) 涨跌幅={change_pct:.2f}% - {rule_desc}")
    
    log_message(f"共 {len(alert_stocks)} 只股票触发预警")
    return alert_stocks

def get_receivers():
    """步骤 6: 读取接收者列表"""
    try:
        receivers = []
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
        log_message(f"获取到 {len(receivers)} 个接收者")
        return receivers
    except Exception as e:
        log_message(f"读取接收者列表时出错：{str(e)}")
        return []

def format_alert_message(alert_stocks):
    """格式化预警消息"""
    # 按涨跌幅排序
    alert_stocks_sorted = sorted(alert_stocks, key=lambda x: x['change_pct'], reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股价预警通知** 🚨\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for item in alert_stocks_sorted[:10]:  # 最多 10 条
        close = item['close']
        change_pct = item['change_pct']
        change_amt = item['change_amt']
        trade_time = item['trade_time']
        
        # 格式化涨跌幅
        if change_pct >= 0:
            change_pct_str = f"+{change_pct:.2f}%"
        else:
            change_pct_str = f"{change_pct:.2f}%"
        
        # 格式化涨跌额
        if change_amt >= 0:
            change_amt_str = f"¥{change_amt:.2f}"
        else:
            change_amt_str = f"¥{change_amt:.2f}"
        
        # 时间只显示时分
        time_str = trade_time.split(' ')[1][:5] if ' ' in trade_time else trade_time[-5:]
        
        lines.append(f"| {item['ts_code'].split('.')[0]} | {item['name']} | ¥{close:.2f} | {change_pct_str} | {change_amt_str} | {time_str} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 🇨🇳 中国石油：涨幅>2% 或 跌幅>1% → 触发")
    lines.append("\n**数据来源**: Tushare Pro")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def send_alerts(receivers, message):
    """步骤 6: 发送预警消息"""
    log_message("步骤 6: 发送预警消息")
    
    if not receivers:
        log_message("警告：没有接收者")
        return False
    
    # 构建命令
    targets_args = ' '.join([f'--targets {r}' for r in receivers])
    # 转义消息中的特殊字符
    escaped_message = message.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    command = f'openclaw message broadcast --channel feishu --account stock {targets_args} --message "{escaped_message}"'
    
    log_message(f"执行命令：{command}")
    
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_message("预警消息发送成功")
            return True
        else:
            log_message(f"发送失败：{result.stderr}")
            return False
    except Exception as e:
        log_message(f"发送消息时出错：{str(e)}")
        return False

def send_task_log():
    """步骤 7: 发送任务日志到群聊"""
    log_message("步骤 7: 发送任务日志到监控群")
    
    # 构建日志消息
    log_content = '\n'.join(task_log)
    escaped_log = log_content.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    
    command = f'openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message "{escaped_log}"'
    
    log_message(f"执行命令：{command}")
    
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_message("任务日志发送成功")
            return True
        else:
            log_message(f"发送日志失败：{result.stderr}")
            return False
    except Exception as e:
        log_message(f"发送日志时出错：{str(e)}")
        return False

def main():
    """主函数"""
    log_message("=" * 50)
    log_message("实时股价监控任务开始执行")
    log_message("=" * 50)
    
    # 步骤 1: 检查交易日
    if not check_trading_day():
        log_message("任务结束：非交易日或不在交易时间")
        send_task_log()
        return
    
    # 步骤 2: 清空数据文件
    if not clear_realtime_data():
        log_message("任务结束：无法清空数据文件")
        send_task_log()
        return
    
    # 获取自选股列表
    stocks = get_watchlist()
    if not stocks:
        log_message("任务结束：自选股列表为空")
        send_task_log()
        return
    
    # 步骤 3: 获取实时数据
    data = fetch_realtime_data(stocks)
    if not data:
        log_message("任务结束：无法获取实时数据")
        send_task_log()
        return
    
    # 步骤 4: 应用预警规则
    alert_stocks = check_alert_rules(data)
    
    # 步骤 5: 检查是否有触发预警的股票
    if not alert_stocks:
        log_message("没有股票触发预警，任务结束")
        send_task_log()
        return
    
    # 步骤 6: 获取接收者并发送预警
    receivers = get_receivers()
    if receivers:
        message = format_alert_message(alert_stocks)
        send_alerts(receivers, message)
    
    # 步骤 7: 发送任务日志
    send_task_log()
    
    log_message("=" * 50)
    log_message("实时股价监控任务执行完成")
    log_message("=" * 50)

if __name__ == '__main__':
    main()
