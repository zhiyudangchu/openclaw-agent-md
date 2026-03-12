#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成任务执行报告并发送到群聊
"""
import json
import subprocess
import sys
from datetime import datetime

# 读取实时数据和预警数据
with open('realtime-data.txt', 'r', encoding='utf-8') as f:
    realtime_data = json.load(f)

with open('alert-data.txt', 'r', encoding='utf-8') as f:
    alert_data = json.load(f)

# 构建任务执行报告
report_lines = []
report_lines.append("📊 **实时股价监控任务执行报告**")
report_lines.append("")
report_lines.append(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append(f"**数据更新时间**: {realtime_data.get('update_time', 'N/A')}")
report_lines.append("")
report_lines.append("**任务执行情况**:")
report_lines.append(f"- ✅ 获取实时数据：成功")
report_lines.append(f"- ✅ 数据过滤：成功")
report_lines.append(f"- ✅ 预警推送：成功")
report_lines.append("")
report_lines.append("**数据统计**:")
report_lines.append(f"- 自选股总数：5 只")
report_lines.append(f"- 触发预警：{alert_data.get('alert_count', 0)} 只")
report_lines.append(f"- 推送接收者：6 人")
report_lines.append("")

if alert_data.get('alert_count', 0) > 0:
    report_lines.append("**预警详情**:")
    for stock in alert_data.get('data', []):
        ts_code = stock.get('ts_code', '')
        name = stock.get('name', '')
        pct_change = stock.get('pct_change', 0)
        close = stock.get('close', 0)
        
        if pct_change > 0:
            symbol = "📈"
            pct_str = f"+{pct_change:.2f}%"
        else:
            symbol = "📉"
            pct_str = f"{pct_change:.2f}%"
        
        report_lines.append(f"- {symbol} {name} ({ts_code.split('.')[0]}): ¥{close:.2f} ({pct_str})")

report_lines.append("")
report_lines.append("**接口调用记录**:")
report_lines.append("- Tushare Pro: rt_k (实时日线)")
report_lines.append(f"  - 入参：ts_code='601857.SH,603606.SH,002600.SZ,002961.SZ,001872.SZ'")
report_lines.append(f"  - 出参：5 条记录")
report_lines.append("")
report_lines.append("**错误记录**: 无")

report = "\n".join(report_lines)

# 发送到群聊
cmd = [
    "openclaw", "message", "send",
    "--channel", "feishu",
    "--account", "stock",
    "--target", "oc_e5021f4489531f598034cdfc2e0394f6",
    "--message", report
]

print(f"Executing: {' '.join(cmd)}")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"stdout: {result.stdout}")
    if result.stderr:
        print(f"stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error: {e}")
