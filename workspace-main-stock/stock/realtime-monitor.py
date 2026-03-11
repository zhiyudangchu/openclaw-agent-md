#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
按照 realtime-data-cron-config.md 的要求执行
"""

import tushare as ts
import pandas as pd
import os
import sys
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

# 工作路径
WORK_DIR = os.path.expanduser('~/.openclaw/workspace-main-stock/stock')

def check_market_status():
    """
    步骤 1: 检查今日是否收盘或休市以及是否在交易时间内
    返回：True 表示可以继续，False 表示结束
    """
    print("===== 步骤 1: 检查市场状态 =====")
    today = datetime.now().strftime('%Y%m%d')
    
    try:
        # 获取上交所交易日历
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        
        if df.empty:
            print(f"⚠️  未获取到 {today} 的交易日历数据")
            return False
        
        is_open = df.iloc[0]['is_open']
        
        if is_open == '0':
            print(f"❌ 今日 ({today}) 休市，结束任务")
            return False
        
        # 检查当前时间是否在交易时间内 (9:30-11:30, 13:00-15:00)
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute
        
        # 上午交易时间：9:30-11:30 (570-690)
        # 下午交易时间：13:00-15:00 (780-900)
        morning_start = 9 * 60 + 30
        morning_end = 11 * 60 + 30
        afternoon_start = 13 * 60
        afternoon_end = 15 * 60
        
        if (morning_start <= current_time <= morning_end) or (afternoon_start <= current_time <= afternoon_end):
            print(f"✅ 市场开放中，当前时间：{now.strftime('%H:%M')}")
            return True
        else:
            print(f"⚠️  当前时间 {now.strftime('%H:%M')} 不在交易时间内")
            # 如果是收盘后 (15:00 之后)，仍然可以继续处理数据
            if current_time > afternoon_end:
                print("✅ 收盘后，仍可获取当日最终数据")
                return True
            else:
                print("❌ 非交易时间，结束任务")
                return False
                
    except Exception as e:
        print(f"❌ 检查市场状态失败：{e}")
        return False

def clear_realtime_data():
    """
    步骤 2: 清空 realtime-data.txt
    """
    print("\n===== 步骤 2: 清空实时数据文件 =====")
    filepath = os.path.join(WORK_DIR, 'realtime-data.txt')
    
    try:
        # 检查文件是否存在且有内容
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip():
                print("📁 发现已有数据，清空文件")
            else:
                print("📁 文件为空")
        else:
            print("📁 文件不存在，将创建新文件")
        
        # 清空文件（只保留表头）
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('ts_code,name,pre_close,high,open,low,close,vol,amount,num\n')
        
        print("✅ 文件已清空")
        return True
    except Exception as e:
        print(f"❌ 清空文件失败：{e}")
        return False

def get_realtime_data():
    """
    步骤 3: 获取自选股的实时日线数据
    返回：DataFrame 或 None
    """
    print("\n===== 步骤 3: 获取实时日线数据 =====")
    
    # 读取自选股列表
    watchlist_path = os.path.join(WORK_DIR, 'watchlist.txt')
    stock_codes = []
    
    try:
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    code, name = line.split('|')
                    # 添加后缀
                    if code.isdigit():
                        if code.startswith('6'):
                            code = code + '.SH'
                        elif code.startswith('0') or code.startswith('3'):
                            code = code + '.SZ'
                        elif code.startswith('9'):
                            code = code + '.BJ'
                    elif '.' not in code:
                        # 港股或美股，保持原样
                        pass
                    stock_codes.append(code)
        
        print(f"📋 自选股数量：{len(stock_codes)}")
        print(f"📋 股票代码：{', '.join(stock_codes)}")
        
    except Exception as e:
        print(f"❌ 读取自选股列表失败：{e}")
        return None
    
    # 批量获取实时日线数据
    try:
        ts_codes_str = ','.join(stock_codes)
        print(f"🔍 调用 rt_k 接口获取数据...")
        
        df = pro.rt_k(ts_code=ts_codes_str)
        
        if df is None or df.empty:
            print("❌ 未获取到数据")
            return None
        
        print(f"✅ 成功获取 {len(df)} 条数据")
        print(df.head())
        
        # 保存到文件
        filepath = os.path.join(WORK_DIR, 'realtime-data.txt')
        df.to_csv(filepath, index=False, encoding='utf-8', mode='a', header=False)
        print(f"✅ 数据已保存到 {filepath}")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取实时数据失败：{e}")
        return None

def apply_alert_rules(df):
    """
    步骤 4: 按照 alert-rules.md 中的预警规则过滤数据
    返回：满足条件的数据
    """
    print("\n===== 步骤 4: 应用预警规则 =====")
    
    if df is None or df.empty:
        print("❌ 无数据可过滤")
        return None
    
    # 计算涨跌幅
    df['pct_change'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
    df['change_amount'] = (df['close'] - df['pre_close']).round(2)
    
    alert_df = pd.DataFrame()
    
    # 通用规则
    # 1. 下跌 > 3% → 触发
    # 2. 上涨 > 5% → 触发
    
    # 个股专属规则
    # 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%
    
    for idx, row in df.iterrows():
        ts_code = row['ts_code']
        pct = row['pct_change']
        triggered = False
        reason = ""
        
        # 检查是否是中国石油
        if ts_code == '601857.SH':
            if pct > 2:
                triggered = True
                reason = f"🟢 涨幅 {pct}% > 2%"
            elif pct < -1:
                triggered = True
                reason = f"🔴 跌幅 {pct}% < -1%"
        else:
            # 通用规则
            if pct < -3:
                triggered = True
                reason = f"📉 下跌 {pct}% < -3%"
            elif pct > 5:
                triggered = True
                reason = f"📈 上涨 {pct}% > 5%"
        
        if triggered:
            row_dict = row.to_dict()
            row_dict['alert_reason'] = reason
            alert_df = pd.concat([alert_df, pd.DataFrame([row_dict])], ignore_index=True)
            print(f"⚠️  触发预警：{row['name']} ({ts_code}) - {reason}")
    
    if alert_df.empty:
        print("✅ 无股票触发预警规则")
        return None
    else:
        print(f"✅ 共 {len(alert_df)} 只股票触发预警")
        return alert_df

def send_alerts(alert_df):
    """
    步骤 6: 读取 receiver-list.txt，发送飞书消息
    """
    print("\n===== 步骤 6: 发送预警通知 =====")
    
    if alert_df is None or alert_df.empty:
        print("⚠️  无预警数据需要发送")
        return True
    
    # 读取接收者列表
    receiver_path = os.path.join(WORK_DIR, 'receiver-list.txt')
    receivers = []
    
    try:
        with open(receiver_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
        
        print(f"📬 接收者数量：{len(receivers)}")
        
    except Exception as e:
        print(f"❌ 读取接收者列表失败：{e}")
        return False
    
    # 构建消息内容（按照 alert-template.md 格式）
    # 读取 alert-template.md
    template_path = os.path.join(WORK_DIR, 'alert-template.md')
    
    # 按涨跌幅排序
    alert_df = alert_df.sort_values('pct_change', ascending=False)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股价预警通知**\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for idx, row in alert_df.iterrows():
        code = row['ts_code'].split('.')[0]
        name = row['name']
        price = f"¥{row['close']:.2f}"
        pct = f"+{row['pct_change']:.2f}%" if row['pct_change'] > 0 else f"{row['pct_change']:.2f}%"
        change = f"¥{row['change_amount']:.2f}"
        time_str = datetime.now().strftime('%H:%M')
        
        # 高亮异常
        if row['pct_change'] > 0:
            lines.append(f"| {code} | {name} | {price} | 📈{pct} | {change} | {time_str} |")
        else:
            lines.append(f"| {code} | {name} | {price} | 📉{pct} | {change} | {time_str} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 3% → 触发")
    lines.append("- 📈 上涨 > 5% → 触发")
    lines.append("- 🟢 中国石油：涨幅 > 2% → 触发")
    lines.append("- 🔴 中国石油：跌幅 > 1% → 触发")
    lines.append(f"\n**【数据来源】**")
    lines.append("- 数据来源：Tushare Pro")
    lines.append(f"- 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    message = '\n'.join(lines)
    
    # 构建命令
    targets_args = ' '.join([f'--targets {r}' for r in receivers])
    command = f'openclaw message broadcast --channel feishu --account stock {targets_args} --message "{message}"'
    
    print(f"\n📤 执行命令：{command}")
    
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 预警消息发送成功")
            return True
        else:
            print(f"❌ 发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 执行命令失败：{e}")
        return False

def log_execution(status, error_msg=None):
    """
    步骤 7: 记录任务执行情况并发送到群聊
    """
    print("\n===== 步骤 7: 记录任务执行日志 =====")
    
    # 构建日志消息
    log_lines = []
    log_lines.append("📊 **实时股价监控任务执行报告**")
    log_lines.append(f"- 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"- 执行状态：{'✅ 成功' if status else '❌ 失败'}")
    
    if error_msg:
        log_lines.append(f"- 错误信息：{error_msg}")
    
    message = '\n'.join(log_lines)
    
    # 发送到群聊
    command = f'openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message "{message}"'
    
    print(f"📤 执行命令：{command}")
    
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 执行日志发送成功")
            return True
        else:
            print(f"❌ 发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 执行命令失败：{e}")
        return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("实时股价监控任务启动")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    error_msg = None
    success = True
    
    try:
        # 步骤 1: 检查市场状态
        if not check_market_status():
            log_execution(False, "市场休市或非交易时间")
            return
        
        # 步骤 2: 清空实时数据文件
        if not clear_realtime_data():
            error_msg = "清空文件失败"
            success = False
        
        # 步骤 3: 获取实时数据
        df = get_realtime_data()
        if df is None:
            error_msg = "获取实时数据失败"
            success = False
            log_execution(success, error_msg)
            return
        
        # 步骤 4 & 5: 应用预警规则
        alert_df = apply_alert_rules(df)
        
        if alert_df is None or alert_df.empty:
            print("\n✅ 无预警触发，任务结束")
            log_execution(True)
            return
        
        # 步骤 6: 发送预警通知
        if not send_alerts(alert_df):
            error_msg = "发送预警通知失败"
            success = False
        
        # 步骤 7: 记录执行日志
        log_execution(success, error_msg)
        
    except Exception as e:
        error_msg = f"任务执行异常：{str(e)}"
        print(f"❌ {error_msg}")
        log_execution(False, error_msg)

if __name__ == "__main__":
    main()
