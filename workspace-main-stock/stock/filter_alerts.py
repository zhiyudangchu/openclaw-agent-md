#!/usr/bin/env python3
import json
import sys
from datetime import datetime

# 读取实时数据
data_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'
with open(data_path, 'r') as f:
    content = f.read()
    # 找到 JSON 部分（跳过可能的日志输出）
    start_idx = content.find('[')
    if start_idx >= 0:
        data = json.loads(content[start_idx:])
    else:
        data = []

# 预警规则
def check_alert(stock):
    ts_code = stock.get('ts_code', '')
    name = stock.get('name', '')
    pct_change = stock.get('pct_change', 0)
    
    # 中国石油专属规则
    if ts_code == '601857.SH' or name == '中国石油':
        # 涨幅 > 2% 或 跌幅 > 1%
        if pct_change > 2 or pct_change < -1:
            return True
    else:
        # 通用规则：下跌 > 3% 或 上涨 > 5%
        if pct_change < -3 or pct_change > 5:
            return True
    
    return False

# 过滤出满足预警条件的股票
alerts = [stock for stock in data if check_alert(stock)]

# 按涨跌幅排序（绝对值大的在前）
alerts.sort(key=lambda x: abs(x.get('pct_change', 0)), reverse=True)

# 输出结果
print(json.dumps(alerts, ensure_ascii=False, indent=2))
