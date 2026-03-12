#!/usr/bin/env python3
"""根据预警规则过滤实时数据"""
import os
import re
from datetime import datetime

# 读取实时数据
data_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/realtime-data.txt')
with open(data_path, 'r') as f:
    lines = f.readlines()

# 解析数据行
stocks = []
for line in lines:
    line = line.strip()
    if line.startswith('#') or line.startswith('数据来源') or line.startswith('数据时间') or line.startswith('=') or line.startswith('-') or '代码 |' in line:
        continue
    if not line:
        continue
    
    # 解析格式：代码 | 名称 | 最新价 | 涨跌幅 | 涨跌额 | 昨收 | 时间
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 7:
        ts_code = parts[0]
        name = parts[1]
        price_str = parts[2].replace('¥', '')
        change_pct_str = parts[3].replace('%', '')
        change_str = parts[4].replace('¥', '')
        pre_close_str = parts[5].replace('¥', '')
        trade_time = parts[6]
        
        try:
            price = float(price_str)
            change_pct = float(change_pct_str)
            change = float(change_str)
            pre_close = float(pre_close_str)
            
            stocks.append({
                'ts_code': ts_code,
                'name': name,
                'price': price,
                'change_pct': change_pct,
                'change': change,
                'pre_close': pre_close,
                'time': trade_time
            })
        except Exception as e:
            print(f"解析失败：{line}, 错误：{e}")

print(f"解析到 {len(stocks)} 条股票数据")

# 预警规则
# 通用规则：下跌 > 1% 或 上涨 > 1%
# 个股专属规则：
#   - 中国石油 (601857.SH): 涨幅 > 2% 或 跌幅 > 1%

def check_alert(stock):
    ts_code = stock['ts_code']
    change_pct = stock['change_pct']
    
    # 通用规则
    if change_pct < -1.0 or change_pct > 1.0:
        return True
    
    return False

# 过滤满足预警条件的股票
alert_stocks = [s for s in stocks if check_alert(s)]

print(f"满足预警条件的股票：{len(alert_stocks)} 条")
for s in alert_stocks:
    print(f"  {s['ts_code']} {s['name']}: {s['change_pct']:+.2f}%")

# 按涨跌幅排序（绝对值大的在前）
alert_stocks.sort(key=lambda x: abs(x['change_pct']), reverse=True)

# 输出到文件
output_path = os.path.expanduser('~/.openclaw/workspace-main-stock/stock/alert-stocks.txt')
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(output_path, 'w') as f:
    f.write(f"数据来源：Tushare Pro\n")
    f.write(f"更新时间：{current_time}\n")
    f.write("\n")
    f.write("⚙️ 预警规则\n")
    f.write("- 📉 下跌 > 1% → 触发\n")
    f.write("- 📈 上涨 > 1% → 触发\n")
    f.write("\n")
    f.write("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |\n")
    f.write("|------|------|--------|--------|--------|------|\n")
    
    for s in alert_stocks:
        # 高亮异常波动
        flag = ""
        if s['change_pct'] > 2:
            flag = "🔥"
        elif s['change_pct'] < -2:
            flag = "⚠️"
        elif s['change_pct'] > 0:
            flag = "📈"
        else:
            flag = "📉"
        
        time_short = s['time'].split(' ')[1][:5] if ' ' in s['time'] else s['time']
        f.write(f"| {s['ts_code']} | {s['name']} | ¥{s['price']:.2f} | {s['change_pct']:+.2f}% | ¥{s['change']:+.2f} | {time_short} {flag}|\n")
    
    f.write("\n")
    f.write(f"**【数据来源】**\n")
    f.write(f"- 数据来源：Tushare Pro\n")
    f.write(f"- 更新时间：{current_time}\n")

print(f"预警数据已保存到 {output_path}")

# 输出用于推送的 markdown 格式
print("\n=== 推送内容 ===")
print(f"🚨 股价预警通知\n")
print(f"| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
print(f"|------|------|--------|--------|--------|------|")
for s in alert_stocks:
    flag = ""
    if s['change_pct'] > 2:
        flag = "🔥"
    elif s['change_pct'] < -2:
        flag = "⚠️"
    elif s['change_pct'] > 0:
        flag = "📈"
    else:
        flag = "📉"
    time_short = s['time'].split(' ')[1][:5] if ' ' in s['time'] else s['time']
    print(f"| {s['ts_code']} | {s['name']} | ¥{s['price']:.2f} | {s['change_pct']:+.2f}% | ¥{s['change']:+.2f} | {time_short} {flag}|")
print(f"\n⚙️ 预警规则")
print(f"- 📉 下跌 > 1% → 触发")
print(f"- 📈 上涨 > 1% → 触发")
print(f"\n**【数据来源】**")
print(f"- 数据来源：Tushare Pro")
print(f"- 更新时间：{current_time}")
