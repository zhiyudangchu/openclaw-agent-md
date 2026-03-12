#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送预警消息到飞书
"""

import os
import subprocess
from datetime import datetime

def load_alerts():
    """加载预警数据"""
    alerts = []
    data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    header_info = {}
    for line in lines:
        line = line.strip()
        if line.startswith('数据来源：'):
            header_info['source'] = line.replace('数据来源：', '')
        elif line.startswith('数据时间：'):
            header_info['time'] = line.replace('数据时间：', '')
        elif '|' in line and not line.startswith('-') and not line.startswith('=') and not line.startswith('代码 |'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                try:
                    ts_code = parts[0]
                    name = parts[1]
                    close = float(parts[2].replace('¥', ''))
                    pct_chg_str = parts[3].replace('%', '')
                    pct_chg = float(pct_chg_str)
                    change = float(parts[4].replace('¥', ''))
                    trade_time = parts[6] if len(parts) > 6 else ''
                    
                    # 检查是否触发预警
                    triggered = False
                    alert_rule = ""
                    
                    # 通用规则
                    if pct_chg < -1:
                        triggered = True
                        alert_rule = "📉 下跌 > 1%"
                    elif pct_chg > 1:
                        triggered = True
                        alert_rule = "📈 上涨 > 1%"
                    
                    if triggered:
                        alerts.append({
                            'ts_code': ts_code,
                            'name': name,
                            'close': close,
                            'pct_chg': pct_chg,
                            'change': change,
                            'trade_time': trade_time,
                            'alert_rule': alert_rule
                        })
                except Exception as e:
                    print(f"解析行失败：{line}, 错误：{e}")
    
    return header_info, alerts

def load_receivers():
    """加载接收者列表"""
    receivers = []
    receiver_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/receiver-list.txt')
    
    with open(receiver_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line:
            receivers.append(line)
    
    return receivers

def build_message(header_info, alerts):
    """构建预警消息"""
    # 按涨跌幅排序（降序）
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 **股价预警通知** 🚨\n")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for alert in alerts:
        # 格式化涨跌幅（带颜色标记）
        pct_str = f"{alert['pct_chg']:+.2f}%"
        change_str = f"¥{alert['change']:+.2f}"
        
        # 提取时间（HH:mm）
        time_str = alert['trade_time']
        if ' ' in time_str:
            time_str = time_str.split(' ')[1][:5]
        
        lines.append(f"| {alert['ts_code'].split('.')[0]} | {alert['name']} | ¥{alert['close']:.2f} | {pct_str} | {change_str} | {time_str} |")
    
    lines.append("\n⚙️ **预警规则**")
    lines.append("- 📉 下跌 > 1% → 触发")
    lines.append("- 📈 上涨 > 1% → 触发")
    lines.append("\n**【数据来源】**")
    lines.append(f"- 数据来源：{header_info.get('source', 'Tushare Pro')}")
    lines.append(f"- 更新时间：{header_info.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}")
    
    return '\n'.join(lines)

def send_broadcast(message, receivers):
    """发送广播消息"""
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
    
    # 执行命令
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"返回码：{result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    
    return result.returncode == 0

def main():
    print("===== 发送预警消息 =====")
    
    # 加载数据
    header_info, alerts = load_alerts()
    print(f"加载到 {len(alerts)} 条预警数据")
    
    if len(alerts) == 0:
        print("无预警数据，结束任务")
        return False
    
    # 加载接收者
    receivers = load_receivers()
    print(f"接收者数量：{len(receivers)}")
    
    # 构建消息
    message = build_message(header_info, alerts)
    print(f"\n消息内容:\n{message}\n")
    
    # 发送消息
    success = send_broadcast(message, receivers)
    
    if success:
        print("\n消息发送成功!")
    else:
        print("\n消息发送失败!")
    
    return success

if __name__ == "__main__":
    main()
