#!/usr/bin/env python3
"""
实时股价监控 - Cron 任务脚本 (使用东方财富接口)
按照 realtime-data-cron-config.md 要求执行
"""

import os
import sys
import requests
import json
from datetime import datetime

WATCHLIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/watchlist.txt")
REALTIME_DATA_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/realtime-data.txt")
ALERT_RESULTS_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/alert-results.txt")
RECEIVER_LIST_FILE = os.path.expanduser("~/.openclaw/workspace-main-stock/stock/receiver-list.txt")

def check_market_closed():
    """检查 A 股市场是否已收盘"""
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    # 周末休市
    if weekday >= 5:
        print(f"📭 今日是周末，市场已休市")
        return True
    
    # 交易时间：9:15-11:30, 13:00-15:00
    if hour < 9 or (hour == 9 and minute < 15):
        print(f"📭 市场尚未开盘 (当前时间：{hour:02d}:{minute:02d})")
        return True
    
    if hour >= 15:
        print(f"📭 市场已收盘 (当前时间：{hour:02d}:{minute:02d})")
        return True
    
    print(f"📈 市场交易中 (当前时间：{hour:02d}:{minute:02d})")
    return False

def get_eastmoney_data(code, name_hint):
    """通过东方财富接口获取实时行情"""
    try:
        # 转换代码格式为东方财富 secid 格式
        # 1 = 沪市，0 = 深市
        if code.endswith('.HK'):
            # 港股
            secid = code.replace('.HK', '')
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=118.{secid}&fields=f43,f44,f45,f46,f47,f48,f49,f13,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
        elif code.endswith('.US'):
            # 美股
            secid = code.replace('.US', '').lower()
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=105.{secid}&fields=f43,f44,f45,f46,f47,f48,f49,f13,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
        elif code.startswith('6') or code.startswith('9'):
            # 沪市
            secid = code.replace('.SH', '')
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{secid}&fields=f43,f44,f45,f46,f47,f48,f49,f13,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
        elif code.startswith('0') or code.startswith('3'):
            # 深市
            secid = code.replace('.SZ', '')
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=0.{secid}&fields=f43,f44,f45,f46,f47,f48,f49,f13,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
        else:
            # 默认沪市
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f13,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get('data'):
            d = data['data']
            name = d.get('f14', '') or name_hint  # 使用 API 返回的名称，如果没有则用 hint
            current_price = d.get('f43', 0) / 100  # 价格单位是分，转换为元
            prev_close = d.get('f44', 0) / 100
            price_change = current_price - prev_close
            pct_chg = (price_change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                'code': code.split('.')[0] if '.' in code else code,
                'name': name,
                'price': current_price,
                'pct_chg': pct_chg,
                'price_change': price_change,
                'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return None
    except Exception as e:
        print(f"错误 {code}: {e}", file=sys.stderr)
        return None

def load_watchlist():
    """加载自选股列表"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|')
                    stocks.append({'code': parts[0], 'name': parts[1] if len(parts) > 1 else parts[0]})
    return stocks

def check_alert_rules(code, name, pct_chg):
    """检查是否触发预警规则"""
    # 中国石油专属规则
    if code == '601857' or '中国石油' in name:
        if pct_chg > 2.0:
            return True, "中国石油专属规则 (涨>2%)"
        if pct_chg < -1.0:
            return True, "中国石油专属规则 (跌>1%)"
    
    # 通用规则
    if pct_chg > 5.0:
        return True, "通用规则 (涨>5%)"
    if pct_chg < -3.0:
        return True, "通用规则 (跌>3%)"
    
    return False, None

def load_receivers():
    """加载接收者列表"""
    receivers = []
    if os.path.exists(RECEIVER_LIST_FILE):
        with open(RECEIVER_LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
    return receivers

def send_feishu_alert(receivers, alert_data):
    """通过飞书推送预警数据"""
    if not receivers or not alert_data:
        return
    
    # 构建消息内容
    message = "⚠️ **股价预警通知**\n\n"
    message += "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 触发规则 |\n"
    message += "|------|------|--------|--------|--------|----------|\n"
    
    for stock in alert_data:
        change_emoji = "🔴" if stock['pct_chg'] >= 0 else "🟢"
        message += f"| {stock['code']} | {stock['name']} | ¥{stock['price']:.2f} | {change_emoji} {stock['pct_chg']:+.2f}% | ¥{stock['price_change']:.2f} | {stock['rule']} |\n"
    
    message += f"\n📊 数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 构建命令
    targets = ' '.join([f"--targets {r}" for r in receivers])
    cmd = f"openclaw message broadcast --channel feishu --account stock {targets} --message \"{message}\""
    
    print(f"\n📤 执行推送命令:")
    print(cmd)
    
    # 执行命令
    os.system(cmd)

def main():
    print("=" * 60)
    print("📊 实时股价监控任务")
    print(f"⏰ 执行时间：{datetime.now()}")
    print("=" * 60)
    
    # 步骤 1: 检查是否收盘
    print("\n【步骤 1】检查市场状态...")
    if check_market_closed():
        print("✅ 市场已收盘，结束本次任务")
        return
    
    # 步骤 2: 清空 realtime-data.txt
    print("\n【步骤 2】清空实时数据文件...")
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    print(f"✅ 已清空 {REALTIME_DATA_FILE}")
    
    # 步骤 3: 加载自选股列表
    print("\n【步骤 3】加载自选股列表...")
    stocks = load_watchlist()
    print(f"📋 共加载 {len(stocks)} 只股票")
    
    # 步骤 4: 获取实时数据
    print("\n【步骤 4】获取实时行情数据...")
    all_results = []
    
    for i, stock in enumerate(stocks):
        code = stock['code']
        name = stock['name']
        
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ")
        
        data = get_eastmoney_data(code, name)
        
        if data:
            all_results.append(data)
            change_symbol = "🔴" if data['pct_chg'] >= 0 else "🟢"
            print(f"✅ ¥{data['price']:.2f} ({data['pct_chg']:+.2f}%) {change_symbol}")
        else:
            print(f"❌ 失败")
        
        # 控制请求频率
        if i < len(stocks) - 1:
            import time
            time.sleep(0.3)
    
    # 步骤 5: 保存全部数据到 realtime-data.txt
    print("\n【步骤 5】保存实时数据...")
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 时间\n")
        for r in sorted(all_results, key=lambda x: x['pct_chg'], reverse=True):
            f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['trade_time']}\n")
    print(f"✅ 共获取 {len(all_results)} 只股票数据，保存至 {REALTIME_DATA_FILE}")
    
    # 步骤 6: 按预警规则过滤
    print("\n【步骤 6】应用预警规则过滤...")
    alert_results = []
    
    for stock in all_results:
        triggered, rule = check_alert_rules(stock['code'], stock['name'], stock['pct_chg'])
        if triggered:
            stock['rule'] = rule
            alert_results.append(stock)
            change_symbol = "🔴" if stock['pct_chg'] >= 0 else "🟢"
            print(f"⚠️ {stock['code']} {stock['name']}: ¥{stock['price']:.2f} ({stock['pct_chg']:+.2f}%) {change_symbol} - {rule}")
    
    if alert_results:
        print(f"\n✅ 共 {len(alert_results)} 只股票触发预警")
        
        # 保存预警数据
        with open(ALERT_RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write("代码 | 名称 | 现价 | 涨跌幅 | 涨跌额 | 触发规则 | 时间\n")
            for r in sorted(alert_results, key=lambda x: x['pct_chg'], reverse=True):
                f.write(f"{r['code']}|{r['name']}|¥{r['price']:.2f}|{r['pct_chg']:+.2f}%|¥{r['price_change']:.2f}|{r['rule']}|{r['trade_time']}\n")
        print(f"📁 预警数据保存至：{ALERT_RESULTS_FILE}")
        
        # 步骤 7: 推送预警数据
        print("\n【步骤 7】推送预警通知...")
        receivers = load_receivers()
        print(f"📬 接收者数量：{len(receivers)}")
        
        if receivers:
            send_feishu_alert(receivers, alert_results)
            print("✅ 预警通知已发送")
        else:
            print("⚠️ 无接收者，跳过推送")
    else:
        print("✅ 无股票触发预警规则")
        # 清空预警文件
        with open(ALERT_RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    
    print("\n" + "=" * 60)
    print("✅ 任务执行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
