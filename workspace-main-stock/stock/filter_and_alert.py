#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤预警数据并发送通知
"""

import json
import os
from datetime import datetime

# 预警规则
# 通用规则：下跌 > 3% 或 上涨 > 5%
GENERAL_DROP_THRESHOLD = -3.0
GENERAL_RISE_THRESHOLD = 5.0

# 个股专属规则
SPECIAL_RULES = {
    '601857.SH': {  # 中国石油
        'rise_threshold': 2.0,  # 涨幅 > 2%
        'drop_threshold': -1.0  # 跌幅 > 1%
    }
}

def load_realtime_data():
    """加载实时数据"""
    data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    stocks = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('数据时间：'):
                continue
            if line.startswith('数据来源：'):
                continue
            if line.startswith('---'):
                continue
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 6:
                stocks.append({
                    'ts_code': parts[0],
                    'name': parts[1],
                    'close': float(parts[2]),
                    'change_pct': float(parts[3]),
                    'change_amt': float(parts[4]),
                    'trade_time': parts[5]
                })
    
    return stocks

def check_alert(stock):
    """检查股票是否触发预警"""
    ts_code = stock['ts_code']
    change_pct = stock['change_pct']
    
    # 检查是否有专属规则
    if ts_code in SPECIAL_RULES:
        rule = SPECIAL_RULES[ts_code]
        if change_pct > rule['rise_threshold']:
            return True, f"专属规则：涨幅{change_pct:.2f}% > {rule['rise_threshold']}%"
        if change_pct < rule['drop_threshold']:
            return True, f"专属规则：跌幅{change_pct:.2f}% < {rule['drop_threshold']}%"
    else:
        # 通用规则
        if change_pct > GENERAL_RISE_THRESHOLD:
            return True, f"通用规则：涨幅{change_pct:.2f}% > {GENERAL_RISE_THRESHOLD}%"
        if change_pct < GENERAL_DROP_THRESHOLD:
            return True, f"通用规则：跌幅{change_pct:.2f}% < {GENERAL_DROP_THRESHOLD}%"
    
    return False, None

def format_alert_message(alerts):
    """格式化预警消息"""
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_pct'], reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股票预警通知** 🚨")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for alert in alerts:
        change_sign = "+" if alert['change_pct'] > 0 else ""
        amt_sign = "+" if alert['change_amt'] > 0 else ""
        time_str = alert['trade_time'].split(' ')[1][:5]  # HH:MM
        
        lines.append(f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | ¥{alert['close']:.2f} | {change_sign}{alert['change_pct']:.2f}% | {amt_sign}{alert['change_amt']:.2f} | {time_str} |")
    
    lines.append("")
    lines.append("⚙️ **预警规则**")
    lines.append(f"- 📉 下跌 > {abs(GENERAL_DROP_THRESHOLD)}% → 触发")
    lines.append(f"- 📈 上涨 > {GENERAL_RISE_THRESHOLD}% → 触发")
    lines.append("- 中国石油：涨幅 > 2% 或 跌幅 > 1% → 触发")
    lines.append("")
    lines.append(f"**数据来源**：Tushare Pro")
    lines.append(f"**更新时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return "\n".join(lines)

def load_receivers():
    """加载接收者列表"""
    receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    receivers = []
    
    with open(receiver_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                receivers.append(line)
    
    return receivers

def main():
    print("===== 过滤预警并发送通知 =====")
    
    # 加载实时数据
    print("\n[步骤 1] 加载实时数据...")
    stocks = load_realtime_data()
    print(f"加载到 {len(stocks)} 只股票数据")
    
    # 过滤预警
    print("\n[步骤 2] 过滤预警数据...")
    alerts = []
    for stock in stocks:
        triggered, reason = check_alert(stock)
        if triggered:
            print(f"  ⚠️ {stock['ts_code']} {stock['name']}: {stock['change_pct']:.2f}% - {reason}")
            alerts.append(stock)
        else:
            print(f"  ✓ {stock['ts_code']} {stock['name']}: {stock['change_pct']:.2f}% - 未触发")
    
    if not alerts:
        print("\n无预警数据，结束任务")
        return {'status': 'no_alerts', 'message': '无预警数据'}
    
    print(f"\n共 {len(alerts)} 只股票触发预警")
    
    # 格式化消息
    print("\n[步骤 3] 格式化预警消息...")
    message = format_alert_message(alerts)
    print(message)
    
    # 保存预警消息
    alert_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-data.txt')
    with open(alert_path, 'w', encoding='utf-8') as f:
        f.write(message)
    print(f"\n预警数据已保存到：{alert_path}")
    
    # 加载接收者
    print("\n[步骤 4] 加载接收者列表...")
    receivers = load_receivers()
    print(f"接收者数量：{len(receivers)}")
    
    # 构建发送命令
    targets_args = " ".join([f"--targets {r}" for r in receivers])
    # 转义消息中的特殊字符
    escaped_message = message.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    
    command = f"openclaw message broadcast --channel feishu --account stock {targets_args} --message \"{escaped_message}\""
    
    print("\n[步骤 5] 发送预警通知...")
    print(f"命令：{command}")
    
    # 执行发送命令
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"发送结果：{result.stdout}")
    if result.stderr:
        print(f"错误信息：{result.stderr}")
    
    return {
        'status': 'success',
        'alerts_count': len(alerts),
        'receivers_count': len(receivers)
    }

if __name__ == "__main__":
    result = main()
    print("\n===== 执行完成 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))
