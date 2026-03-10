#!/usr/bin/env python3
"""
Fetch real-time stock data, filter by alert rules, and send Feishu notification.
"""
import requests
import subprocess
from datetime import datetime

watchlist_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/watchlist.txt"
output_file = "/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt"

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

def get_stock_data(code):
    """Fetch stock data from East Money API."""
    # Convert code to secid format
    if code.endswith('.HK'):
        secid = f"120.{code.replace('.HK', '')}"
    elif code.startswith('6') or code.startswith('9'):
        secid = f"1.{code}"
    elif code.startswith('0') or code.startswith('3'):
        secid = f"0.{code}"
    elif code.startswith('68'):
        secid = f"1.{code}"  # STAR market
    else:
        secid = f"1.{code}"  # Default to Shanghai
    
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f57,f58,f170,f47,f48&_=1234567890"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('rc') == 0 and data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100 if d.get('f43') else 0
            change_pct = d.get('f170', 0) / 100 if d.get('f170') else 0
            price_change = price * (change_pct / 100) if price else 0
            volume = d.get('f47', 0)
            amount = d.get('f48', 0)
            
            # Format volume and amount
            if volume >= 100000000:
                vol_str = f"{volume/100000000:.2f}亿"
            elif volume >= 10000:
                vol_str = f"{volume/10000:.2f}万"
            else:
                vol_str = f"{volume:.2f}"
                
            if amount >= 100000000:
                amt_str = f"{amount/100000000:.1f}亿"
            elif amount >= 10000:
                amt_str = f"{amount/10000:.1f}万"
            else:
                amt_str = f"{amount:.1f}"
            
            return {
                'code': d.get('f57', code.split('.')[0] if '.' in code else code),
                'name': d.get('f58', 'Unknown'),
                'price': price,
                'change_pct': change_pct,
                'price_change': price_change,
                'volume': vol_str,
                'amount': amt_str
            }
    except Exception as e:
        print(f"Error fetching {code}: {e}")
    
    return None

def check_alert_rules(stock_data):
    """Check if stock triggers alert rules."""
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

# Read watchlist
with open(watchlist_file, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

print(f"📊 开始获取实时行情 - {datetime.now()}")
print(f"📋 自选股数量：{len(lines)}")

results = []
alert_results = []

for i, line in enumerate(lines):
    parts = line.split('|')
    if len(parts) >= 1:
        code = parts[0]
        name = parts[1] if len(parts) > 1 else ''
        
        print(f"[{i+1}/{len(lines)}] 获取 {code} {name}...", end=" ")
        
        data = get_stock_data(code)
        
        if data:
            results.append(data)
            change_symbol = "🔴" if data['change_pct'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['change_pct']:+.2f}%) {change_symbol}")
            
            # Check alert rules
            if check_alert_rules(data):
                alert_results.append(data)
                print(f"   ⚠️ 触发预警!")
        else:
            print(f"❌ 失败")

# Sort alert results by change percentage (descending)
alert_results.sort(key=lambda x: x['change_pct'], reverse=True)

# Write all data to realtime-data.txt
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
    for r in results:
        price_str = f"¥{r['price']:.2f}"
        change_str = f"{r['change_pct']:+.2f}%"
        change_amt = f"¥{r['price_change']:.2f}"
        f.write(f"{r['code']}|{r['name']}|{price_str}|{change_str}|{change_amt}|{timestamp}\n")

print(f"\n{'='*60}")
print(f"✅ 完成！共获取 {len(results)} 只股票数据")
print(f"⚠️  触发预警：{len(alert_results)} 只")
print(f"📁 数据保存至：{output_file}")

# Send Feishu notification if there are alerts
if alert_results:
    print(f"\n📤 准备发送飞书预警通知...")
    
    # Build message according to alert-template.md
    message_lines = [
        "⚠️ 股价预警通知",
        f"时间：{timestamp}",
        "",
        "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |",
        "|------|------|--------|--------|-------|------|"
    ]
    
    for r in alert_results:
        price_str = f"¥{r['price']:.2f}"
        change_str = f"{r['change_pct']:+.2f}%"
        change_amt = f"¥{r['price_change']:.2f}"
        time_str = timestamp.split(' ')[1][:5]  # HH:MM
        message_lines.append(f"| {r['code']} | {r['name']} | {price_str} | {change_str} | {change_amt} | {time_str} |")
    
    message_lines.extend([
        "",
        "⚙️ 预警规则",
        "• 📉 下跌 > 3% → 触发",
        "• 📈 上涨 > 5% → 触发",
        "• 中国石油：涨幅>2% 或 跌幅>1% → 触发"
    ])
    
    message = "\n".join(message_lines)
    
    # Send via Feishu
    cmd = f"openclaw message send --channel feishu --account stock --message '{message}' --target ou_9d907d39fb19b50579ba289b30041fc5"
    print(f"执行命令：{cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ 飞书通知发送成功!")
        else:
            print(f"❌ 发送失败：{result.stderr}")
    except Exception as e:
        print(f"❌ 发送异常：{e}")
else:
    print(f"\n✅ 无触发预警的股票，无需发送通知")
