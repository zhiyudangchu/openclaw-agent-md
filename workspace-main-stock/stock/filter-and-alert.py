#!/usr/bin/env python3
"""
过滤预警数据并发送飞书通知
"""

import subprocess
from datetime import datetime

INPUT_FILE = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"
OUTPUT_FILE = "/home/openclaw/workspace-main-stock/stock/alert-data.txt"

# Alert rules
ALERT_DROP_THRESHOLD = -3.0  # Generic: drop > 3%
ALERT_RISE_THRESHOLD = 5.0   # Generic: rise > 5%

# Special rules for 中国石油 (601857)
SPECIAL_STOCK_RULES = {
    '601857': {
        'name': '中国石油',
        'rise_threshold': 2.0,   # Rise > 2% triggers
        'drop_threshold': -1.0   # Drop > 1% triggers
    }
}

def parse_stock_data(line):
    """解析股票数据行"""
    parts = line.strip().split('|')
    if len(parts) >= 5:
        return {
            'code': parts[0],
            'name': parts[1],
            'price': parts[2],
            'change_pct': float(parts[3].replace('%', '').replace('+', '')),
            'price_change': parts[4],
            'time': parts[5] if len(parts) > 5 else ''
        }
    return None

def check_alert_rules(stock_data):
    """检查是否触发预警规则"""
    code = stock_data['code']
    change = stock_data['change_pct']
    
    # Check special rules first
    if code in SPECIAL_STOCK_RULES:
        rule = SPECIAL_STOCK_RULES[code]
        if change > rule['rise_threshold'] or change < rule['drop_threshold']:
            return True
        return False
    
    # Check generic rules
    if change > ALERT_RISE_THRESHOLD or change < ALERT_DROP_THRESHOLD:
        return True
    
    return False

def main():
    print(f"🔍 开始过滤预警数据 - {datetime.now()}")
    
    # Read data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) <= 1:
        print("⚠️  数据文件为空或格式错误")
        return
    
    # Skip header line
    header = lines[0].strip()
    data_lines = lines[1:]
    
    alert_results = []
    
    for line in data_lines:
        if not line.strip():
            continue
        
        stock = parse_stock_data(line)
        if stock:
            if check_alert_rules(stock):
                alert_results.append(stock)
                print(f"⚠️  {stock['code']} {stock['name']}: {stock['price']} ({stock['change_pct']:+.2f}%) - 触发预警!")
    
    # Sort by change percentage (descending)
    alert_results.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"✅ 过滤完成！触发预警：{len(alert_results)} 只")
    
    if alert_results:
        # Write alert data
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(header + "\n")
            for r in alert_results:
                f.write(f"{r['code']}|{r['name']}|{r['price']}|{r['change_pct']:+.2f}%|{r['price_change']}|{r['time']}\n")
        
        print(f"📁 预警数据保存至：{OUTPUT_FILE}")
        
        # Build Feishu message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_lines = [
            "⚠️ 股价预警通知",
            f"时间：{timestamp}",
            "",
            "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |",
            "|------|------|--------|--------|-------|------|"
        ]
        
        for r in alert_results:
            time_str = r['time'].split(' ')[1][:5] if r['time'] else timestamp.split(' ')[1][:5]
            message_lines.append(f"| {r['code']} | {r['name']} | {r['price']} | {r['change_pct']:+.2f}% | {r['price_change']} | {time_str} |")
        
        message_lines.extend([
            "",
            "⚙️ 预警规则",
            "• 📉 下跌 > 3% → 触发",
            "• 📈 上涨 > 5% → 触发",
            "• 中国石油：涨幅>2% 或 跌幅>1% → 触发"
        ])
        
        message = "\n".join(message_lines)
        
        print(f"\n📤 准备发送飞书预警通知...")
        print(f"接收用户：ou_9d907d39fb19b50579ba289b30041fc5")
        
        # Send via Feishu using openclaw CLI
        cmd = ['openclaw', 'message', 'send', '--channel', 'feishu', '--account', 'stock', 
               '--message', message, '--target', 'ou_9d907d39fb19b50579ba289b30041fc5']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ 飞书通知发送成功!")
            else:
                print(f"❌ 发送失败：{result.stderr}")
        except Exception as e:
            print(f"❌ 发送异常：{e}")
    else:
        print(f"\n✅ 无触发预警的股票，无需发送通知")

if __name__ == "__main__":
    main()
