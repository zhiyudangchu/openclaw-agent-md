#!/usr/bin/env python3
import json
from datetime import datetime

# 读取预警数据
alerts_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/alerts-data.txt'
with open(alerts_path, 'r') as f:
    alerts = json.load(f)

# 生成表格格式的消息（飞书支持 Markdown）
# 按涨跌幅排序
alerts.sort(key=lambda x: x.get('pct_change', 0), reverse=True)

# 构建消息
current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

# 表头
message = "🚨 **股票预警通知**\n\n"
message += "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |\n"
message += "|------|------|--------|--------|-------|------|\n"

for stock in alerts:
    ts_code = stock.get('ts_code', '')
    name = stock.get('name', '')
    close = stock.get('close', 0)
    pct_change = stock.get('pct_change', 0)
    change = stock.get('change', 0)
    trade_time = stock.get('trade_time', '')[:16].replace(' ', ' ')  # 取 HH:mm
    
    # 格式化涨跌
    if pct_change >= 0:
        pct_str = f"+{pct_change:.2f}%"
        change_str = f"¥{change:.2f}"
    else:
        pct_str = f"{pct_change:.2f}%"
        change_str = f"¥{change:.2f}"
    
    # 代码去掉后缀便于显示
    code_short = ts_code.split('.')[0]
    
    message += f"| {code_short} | {name} | ¥{close:.2f} | {pct_str} | {change_str} | {trade_time[-5:]} |\n"

message += f"\n⚙️ **预警规则**\n"
message += "• 📉 下跌 > 3% → 触发\n"
message += "• 📈 上涨 > 5% → 触发\n"
message += "• 🛢️ 中国石油：涨幅 > 2% 或 跌幅 > 1% → 触发\n"
message += f"\n【数据来源】Tushare Pro\n"
message += f"更新时间：{current_time}"

print(message)
