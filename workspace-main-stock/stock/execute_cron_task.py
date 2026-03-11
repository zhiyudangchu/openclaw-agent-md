#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控 cron 任务执行脚本
功能：
1. 检查今日是否交易日
2. 获取自选股实时日线数据
3. 根据预警规则过滤
4. 推送预警数据到飞书
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加 tushare 路径
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace-main-stock/skills/tushare-data'))

import tushare as ts

# 初始化
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 配置
WATCHLIST_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/watchlist.txt')
REALTIME_DATA_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
ALERT_RULES_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-rules.md')
RECEIVER_LIST_FILE = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')

# 任务日志
task_log = {
    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "steps": [],
    "errors": []
}

def log_step(step_name, status, details=""):
    """记录任务步骤"""
    task_log["steps"].append({
        "step": step_name,
        "status": status,
        "details": details,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    print(f"[{step_name}] {status}: {details}")

def check_trading_day():
    """检查今日是否交易日"""
    today = datetime.now().strftime('%Y%m%d')
    try:
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        if df.empty:
            log_step("检查交易日", "错误", "无法获取交易日历")
            return False
        
        is_open = df.iloc[0]['is_open']
        if is_open == 1:
            log_step("检查交易日", "成功", f"今日 ({today}) 是交易日")
            return True
        else:
            log_step("检查交易日", "休市", f"今日 ({today}) 休市")
            return False
    except Exception as e:
        log_step("检查交易日", "错误", str(e))
        return False

def load_watchlist():
    """加载自选股列表"""
    stocks = []
    try:
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    code, name = line.split('|')
                    # 添加后缀
                    if '.' not in code:
                        if code.startswith('6') or code.startswith('9') or code.startswith('688'):
                            code = code + '.SH'
                        elif code.startswith('0') or code.startswith('3'):
                            code = code + '.SZ'
                        elif code.startswith('920'):
                            code = code + '.BJ'
                    stocks.append(code)
        log_step("加载自选股", "成功", f"共 {len(stocks)} 只股票")
        return stocks
    except Exception as e:
        log_step("加载自选股", "错误", str(e))
        return []

def fetch_realtime_data(stocks):
    """获取实时日线数据"""
    try:
        # 构建 ts_code 参数
        ts_codes = ','.join(stocks)
        df = pro.rt_k(ts_code=ts_codes)
        
        if df.empty:
            log_step("获取实时数据", "错误", "未获取到数据")
            return None
        
        log_step("获取实时数据", "成功", f"获取 {len(df)} 条数据")
        return df
    except Exception as e:
        log_step("获取实时数据", "错误", str(e))
        return None

def save_realtime_data(df):
    """保存实时数据到文件"""
    try:
        # 清空文件
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("数据来源：Tushare Pro\n")
            f.write("-" * 80 + "\n")
            
            for idx, row in df.iterrows():
                # 计算涨跌幅
                pre_close = row.get('pre_close', 0)
                close = row.get('close', 0)
                if pre_close > 0:
                    pct_change = ((close - pre_close) / pre_close) * 100
                    change = close - pre_close
                else:
                    pct_change = 0
                    change = 0
                
                # 格式化输出
                line = f"{row['ts_code']}|{row.get('name', 'N/A')}|{close:.2f}|{pct_change:.2f}|{change:.2f}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f.write(line)
            
            f.write("=" * 80 + "\n")
        
        log_step("保存数据", "成功", f"已保存到 {REALTIME_DATA_FILE}")
        return True
    except Exception as e:
        log_step("保存数据", "错误", str(e))
        return False

def filter_alerts(df):
    """根据预警规则过滤数据"""
    alerts = []
    
    try:
        for idx, row in df.iterrows():
            pre_close = row.get('pre_close', 0)
            close = row.get('close', 0)
            ts_code = row['ts_code']
            name = row.get('name', 'N/A')
            
            if pre_close > 0:
                pct_change = ((close - pre_close) / pre_close) * 100
                change = close - pre_close
            else:
                pct_change = 0
                change = 0
            
            alert_reason = None
            
            # 通用规则
            if pct_change < -3:
                alert_reason = f"📉 {name} 下跌 > 3% ({pct_change:.2f}%)"
            elif pct_change > 5:
                alert_reason = f"📈 {name} 上涨 > 5% ({pct_change:.2f}%)"
            
            # 个股专属规则 - 中国石油 (601857.SH)
            if ts_code == '601857.SH':
                if pct_change > 2:
                    alert_reason = f"🟢 {name} 涨幅 > 2% ({pct_change:.2f}%)"
                elif pct_change < -1:
                    alert_reason = f"🔴 {name} 跌幅 > 1% ({pct_change:.2f}%)"
            
            if alert_reason:
                alerts.append({
                    'ts_code': ts_code,
                    'name': name,
                    'close': close,
                    'pct_change': pct_change,
                    'change': change,
                    'time': datetime.now().strftime('%H:%M'),
                    'alert_reason': alert_reason
                })
        
        # 按涨跌幅排序
        alerts.sort(key=lambda x: x['pct_change'], reverse=True)
        
        log_step("过滤预警", "成功", f"发现 {len(alerts)} 条预警")
        return alerts
    except Exception as e:
        log_step("过滤预警", "错误", str(e))
        return []

def load_receivers():
    """加载接收者列表"""
    receivers = []
    try:
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
        log_step("加载接收者", "成功", f"共 {len(receivers)} 个接收者")
        return receivers
    except Exception as e:
        log_step("加载接收者", "错误", str(e))
        return []

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return ""
    
    # 构建表格
    lines = []
    lines.append("🚨 **股票预警通知**\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for alert in alerts[:10]:  # 最多 10 条
        sign = "+" if alert['pct_change'] >= 0 else ""
        lines.append(f"| {alert['ts_code']} | {alert['name']} | ¥{alert['close']:.2f} | {sign}{alert['pct_change']:.2f}% | ¥{alert['change']:.2f} | {alert['time']} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 🟢 中国石油 涨幅 > 2% → 触发")
    lines.append("- 🔴 中国石油 跌幅 > 1% → 触发")
    lines.append(f"\n**数据来源**: Tushare Pro")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return "\n".join(lines)

def send_alerts(receivers, message):
    """发送预警消息"""
    if not receivers or not message:
        log_step("发送预警", "跳过", "无接收者或无预警数据")
        return
    
    try:
        # 构建命令
        targets = " ".join([f"--targets {r}" for r in receivers])
        cmd = f"openclaw message broadcast --channel feishu --account stock {targets} --message '{message}'"
        
        log_step("发送预警", "执行", f"命令：{cmd}")
        os.system(cmd)
        log_step("发送预警", "成功", "预警已发送")
    except Exception as e:
        log_step("发送预警", "错误", str(e))

def send_task_log():
    """发送任务日志到群聊"""
    try:
        log_message = f"📊 **任务执行日志**\n\n"
        log_message += f"**执行时间**: {task_log['timestamp']}\n\n"
        
        log_message += "**执行步骤**:\n"
        for step in task_log['steps']:
            status_emoji = "✅" if step['status'] == "成功" else "❌" if step['status'] == "错误" else "⚠️"
            log_message += f"- {status_emoji} {step['step']}: {step['status']} - {step['details']}\n"
        
        if task_log['errors']:
            log_message += "\n**错误信息**:\n"
            for error in task_log['errors']:
                log_message += f"- {error}\n"
        
        cmd = f"openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message '{log_message}'"
        os.system(cmd)
        
        print(f"[任务日志] 已发送到群聊")
    except Exception as e:
        print(f"[任务日志] 发送失败：{e}")

def main():
    print("=" * 60)
    print("实时股价监控任务启动")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 步骤 1: 检查交易日
    if not check_trading_day():
        log_step("任务终止", "休市", "今日非交易日")
        send_task_log()
        return
    
    # 步骤 2: 清空实时数据文件
    try:
        with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
            f.write("")
        log_step("清空数据文件", "成功", "已清空 realtime-data.txt")
    except Exception as e:
        log_step("清空数据文件", "错误", str(e))
    
    # 步骤 3: 加载自选股
    stocks = load_watchlist()
    if not stocks:
        log_step("任务终止", "错误", "自选股列表为空")
        send_task_log()
        return
    
    # 步骤 4: 获取实时数据
    df = fetch_realtime_data(stocks)
    if df is None or df.empty:
        log_step("任务终止", "错误", "获取实时数据失败")
        send_task_log()
        return
    
    # 步骤 5: 保存实时数据
    save_realtime_data(df)
    
    # 步骤 6: 过滤预警
    alerts = filter_alerts(df)
    if not alerts:
        log_step("任务完成", "无预警", "未发现满足预警规则的股票")
        send_task_log()
        return
    
    # 步骤 7: 加载接收者并发送预警
    receivers = load_receivers()
    if receivers:
        message = format_alert_message(alerts)
        send_alerts(receivers, message)
    
    # 步骤 8: 发送任务日志
    send_task_log()
    
    print("=" * 60)
    print("任务执行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
