#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控任务执行脚本
按照 realtime-data-cron-config.md 要求执行
"""

import tushare as ts
import pandas as pd
import os
from datetime import datetime
import json

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN', 'ff592aa74b18d383dcd07f59f57fce0207e8b8675032f8284245c55e')

# 初始化 pro 接口
pro = ts.pro_api(token)

# 工作路径
WORK_DIR = os.path.expanduser('~/.openclaw/workspace-main-stock/stock')

# 任务监控日志
task_log = {
    "api_calls": [],
    "errors": []
}

def log_api_call(api_name, params, result_count, error=None):
    """记录 API 调用"""
    task_log["api_calls"].append({
        "api": api_name,
        "params": params,
        "result_count": result_count,
        "error": error,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def check_trading_status():
    """
    步骤 1: 检查今日是否收盘或休市以及是否在交易时间内
    返回：True 表示可以继续，False 表示结束
    """
    print("\n===== 步骤 1: 检查交易状态 =====")
    try:
        # 获取交易日历
        today = datetime.now().strftime('%Y%m%d')
        cal_data = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        
        if cal_data.empty:
            print("无法获取交易日历")
            log_api_call("trade_cal", {"exchange": "SSE", "date": today}, 0, "No data returned")
            return False
        
        is_open = cal_data.iloc[0]['is_open']
        
        if not is_open:
            print(f"今日 ({today}) 休市")
            log_api_call("trade_cal", {"exchange": "SSE", "date": today}, 1)
            return False
        
        # 检查当前时间是否在交易时间内
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # 上午交易时间：9:30-11:30
        # 下午交易时间：13:00-15:00
        is_morning = (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30)
        is_afternoon = (hour == 13 and minute >= 0) or (hour == 14) or (hour == 15 and minute <= 0)
        
        if is_morning or is_afternoon:
            print(f"当前时间 {now.strftime('%H:%M')} 在交易时间内")
            log_api_call("trade_cal", {"exchange": "SSE", "date": today}, 1)
            return True
        else:
            print(f"当前时间 {now.strftime('%H:%M')} 不在交易时间内")
            log_api_call("trade_cal", {"exchange": "SSE", "date": today}, 1)
            # 即使是非交易时间，如果是当天，仍然可以获取实时数据
            return True
            
    except Exception as e:
        print(f"检查交易状态失败：{e}")
        log_api_call("trade_cal", {"exchange": "SSE", "date": today}, 0, str(e))
        task_log["errors"].append(f"检查交易状态失败：{e}")
        return False

def clear_realtime_data():
    """
    步骤 2: 清空 realtime-data.txt
    """
    print("\n===== 步骤 2: 清空实时数据文件 =====")
    realtime_file = os.path.join(WORK_DIR, 'realtime-data.txt')
    try:
        with open(realtime_file, 'w', encoding='utf-8') as f:
            f.write('')
        print(f"已清空：{realtime_file}")
    except Exception as e:
        print(f"清空文件失败：{e}")
        task_log["errors"].append(f"清空文件失败：{e}")

def get_watchlist():
    """读取自选股列表"""
    watchlist_file = os.path.join(WORK_DIR, 'watchlist.txt')
    watchlist = []
    try:
        with open(watchlist_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|')
                    code = parts[0]
                    # 转换为 tushare 格式
                    if '.' in code:  # 已经是完整格式如 9866.HK
                        ts_code = code
                    else:  # 需要添加后缀
                        if code.startswith('6') or code.startswith('9'):
                            ts_code = f"{code}.SH"
                        else:
                            ts_code = f"{code}.SZ"
                    watchlist.append(ts_code)
        print(f"读取到 {len(watchlist)} 只股票")
        return watchlist
    except Exception as e:
        print(f"读取自选股列表失败：{e}")
        task_log["errors"].append(f"读取自选股列表失败：{e}")
        return []

def get_realtime_data(watchlist):
    """
    步骤 3: 使用 rt_k 接口获取实时日线数据
    """
    print("\n===== 步骤 3: 获取实时日线数据 =====")
    
    if not watchlist:
        print("自选股列表为空")
        return None
    
    try:
        # 使用 rt_k 接口获取实时日线
        ts_codes = ','.join(watchlist)
        print(f"请求代码：{ts_codes}")
        
        data = pro.rt_k(ts_code=ts_codes)
        
        log_api_call("rt_k", {"ts_code": ts_codes}, len(data) if data is not None else 0)
        
        if data is None or data.empty:
            print("未获取到数据")
            return None
        
        print(f"获取到 {len(data)} 条数据")
        
        # 保存到文件
        realtime_file = os.path.join(WORK_DIR, 'realtime-data.txt')
        results = []
        
        for _, row in data.iterrows():
            ts_code = row['ts_code']
            name = row.get('name', ts_code)
            close = row.get('close', 0)
            pre_close = row.get('pre_close', close)
            
            # 计算涨跌幅和涨跌额
            if pre_close > 0:
                pct_chg = ((close - pre_close) / pre_close) * 100
            else:
                pct_chg = 0
            change = close - pre_close
            
            # 获取交易时间
            trade_time = row.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            results.append({
                'ts_code': ts_code,
                'name': name,
                'close': close,
                'pct_chg': pct_chg,
                'change': change,
                'trade_time': trade_time,
                'pre_close': pre_close
            })
        
        # 写入文件
        with open(realtime_file, 'w', encoding='utf-8') as f:
            f.write(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("数据来源：Tushare Pro (rt_k 接口)\n")
            f.write("-" * 80 + "\n")
            for r in results:
                line = f"{r['ts_code']}|{r['name']}|{r['close']:.2f}|{r['pct_chg']:.2f}|{r['change']:.2f}|{r['trade_time']}"
                f.write(line + "\n")
        
        print(f"数据已保存到：{realtime_file}")
        return results
        
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        log_api_call("rt_k", {"ts_code": ts_codes}, 0, str(e))
        task_log["errors"].append(f"获取实时数据失败：{e}")
        return None

def filter_alerts(data):
    """
    步骤 4: 按照预警规则过滤数据
    
    通用规则:
    - 下跌 > 3% → 触发
    - 上涨 > 5% → 触发
    
    个股专属规则:
    - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%
    """
    print("\n===== 步骤 4: 过滤预警数据 =====")
    
    if not data:
        return []
    
    alerts = []
    
    for stock in data:
        ts_code = stock['ts_code']
        pct_chg = stock['pct_chg']
        name = stock['name']
        
        triggered = False
        reason = ""
        
        # 检查中国石油专属规则
        if ts_code == '601857.SH':
            if pct_chg > 2:
                triggered = True
                reason = "涨幅 > 2% (中国石油专属)"
            elif pct_chg < -1:
                triggered = True
                reason = "跌幅 > 1% (中国石油专属)"
        else:
            # 通用规则
            if pct_chg < -3:
                triggered = True
                reason = "下跌 > 3%"
            elif pct_chg > 5:
                triggered = True
                reason = "上涨 > 5%"
        
        if triggered:
            alerts.append({
                **stock,
                'alert_reason': reason
            })
            print(f"⚠️ {ts_code} {name}: {pct_chg:.2f}% - {reason}")
    
    print(f"\n共触发 {len(alerts)} 条预警")
    return alerts

def read_receivers():
    """
    步骤 6: 读取接收者列表
    """
    print("\n===== 步骤 6: 读取接收者列表 =====")
    receiver_file = os.path.join(WORK_DIR, 'receiver-list.txt')
    receivers = []
    try:
        with open(receiver_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
        print(f"读取到 {len(receivers)} 个接收者")
        return receivers
    except Exception as e:
        print(f"读取接收者列表失败：{e}")
        task_log["errors"].append(f"读取接收者列表失败：{e}")
        return []

def format_alert_message(alerts):
    """
    步骤 7: 按照 alert-template.md 格式推送数据
    """
    print("\n===== 步骤 7: 格式化预警消息 =====")
    
    if not alerts:
        return ""
    
    # 按涨跌幅排序
    alerts_sorted = sorted(alerts, key=lambda x: x['pct_chg'], reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股价预警通知**\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for alert in alerts_sorted[:10]:  # 最多 10 条
        ts_code = alert['ts_code'].replace('.SH', '').replace('.SZ', '').replace('.HK', '')
        name = alert['name']
        close = alert['close']
        pct_chg = alert['pct_chg']
        change = alert['change']
        time_str = alert['trade_time']
        
        # 格式化涨跌幅
        if pct_chg >= 0:
            pct_str = f"+{pct_chg:.2f}%"
        else:
            pct_str = f"{pct_chg:.2f}%"
        
        # 格式化涨跌额
        if change >= 0:
            change_str = f"￥{change:.2f}"
        else:
            change_str = f"￥{change:.2f}"
        
        lines.append(f"| {ts_code} | {name} | ¥{close:.2f} | {pct_str} | {change_str} | {time_str} |")
    
    lines.append("\n\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 🛢️ 中国石油：涨幅 > 2% 或 跌幅 > 1%")
    lines.append(f"\n**数据来源**: Tushare Pro (rt_k 接口)")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    message = '\n'.join(lines)
    print(message)
    return message

def send_alerts(receivers, message):
    """
    步骤 6: 发送预警消息
    """
    if not receivers or not message:
        print("没有接收者或消息为空，跳过发送")
        return
    
    # 构建命令
    targets = ' '.join([f'--targets {r}' for r in receivers])
    # 转义消息中的特殊字符
    escaped_message = message.replace('"', '\\"').replace('$', '\\$')
    
    cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{escaped_message}"'
    print(f"\n===== 发送预警消息 =====")
    print(f"命令：{cmd}")
    
    try:
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"发送结果：{result.stdout}")
        if result.stderr:
            print(f"错误：{result.stderr}")
    except Exception as e:
        print(f"发送消息失败：{e}")
        task_log["errors"].append(f"发送消息失败：{e}")

def send_task_log():
    """
    任务监控：发送任务执行日志到群聊
    """
    print("\n===== 发送任务监控日志 =====")
    
    log_content = f"📊 **实时股价监控任务执行日志**\n\n"
    log_content += f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    log_content += f"**API 调用记录** ({len(task_log['api_calls'])} 次):\n"
    for call in task_log['api_calls']:
        log_content += f"- {call['api']}: {call.get('result_count', 0)} 条数据"
        if call.get('error'):
            log_content += f" ❌ {call['error']}"
        log_content += f" @ {call['timestamp']}\n"
    
    if task_log['errors']:
        log_content += f"\n**错误记录** ({len(task_log['errors'])} 个):\n"
        for err in task_log['errors']:
            log_content += f"- ❌ {err}\n"
    else:
        log_content += f"\n✅ 无错误\n"
    
    cmd = f'openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message "{log_content}"'
    print(f"命令：{cmd}")
    
    try:
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"发送结果：{result.stdout}")
    except Exception as e:
        print(f"发送日志失败：{e}")

def main():
    print("=" * 60)
    print("实时股价监控任务")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 步骤 1: 检查交易状态
    if not check_trading_status():
        print("不在交易时间或休市，结束任务")
        send_task_log()
        return
    
    # 步骤 2: 清空实时数据文件
    clear_realtime_data()
    
    # 读取自选股列表
    watchlist = get_watchlist()
    if not watchlist:
        print("自选股列表为空，结束任务")
        send_task_log()
        return
    
    # 步骤 3: 获取实时数据
    data = get_realtime_data(watchlist)
    if not data:
        print("获取数据失败，结束任务")
        send_task_log()
        return
    
    # 步骤 4: 过滤预警数据
    alerts = filter_alerts(data)
    
    # 步骤 5: 如果没有预警数据，结束任务
    if not alerts:
        print("无预警数据，结束任务")
        send_task_log()
        return
    
    # 步骤 6: 读取接收者列表
    receivers = read_receivers()
    
    # 步骤 7: 格式化并发送预警消息
    message = format_alert_message(alerts)
    send_alerts(receivers, message)
    
    # 发送任务监控日志
    send_task_log()
    
    print("\n===== 任务执行完成 =====")

if __name__ == "__main__":
    main()
