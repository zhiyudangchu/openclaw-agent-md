#!/usr/bin/env python3
"""
智能股票监控系统 - 带预警功能
支持：腾讯控股 (00700.HK)、贵州茅台 (600519.SH)、苹果 (AAPL.US)
预警条件：下跌>3% / 上涨>5% / 成交量翻倍 / 股价 100-500 元区间
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

# 配置路径
WATCHLIST_FILE = os.path.expanduser("~/.clawdbot/stock_watcher/watchlist.txt")
LOG_DIR = os.path.expanduser("~/.clawdbot/stock_watcher/alerts")
LOG_FILE = os.path.join(LOG_DIR, "alert.log")

# 预警阈值配置
ALERT_CONFIG = {
    'price_lower': 100,      # 股价下限
    'price_upper': 500,      # 股价上限
    'drop_threshold': 3.0,   # 下跌阈值 (%)
    'rise_threshold': 5.0,   # 上涨阈值 (%)
}

def ensure_log_dir():
    """确保日志目录存在"""
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message):
    """记录日志"""
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def get_stock_data(stock_code):
    """从同花顺获取股票数据（A 股/港股）"""
    try:
        url = f"https://stockpage.10jqka.com.cn/{stock_code}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取关键信息
            data = {'code': stock_code, 'name': None, 'price': None, 
                    'change_pct': None, 'volume': None}
            
            # 尝试获取标题中的名称
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if '(' in title_text and ')' in title_text:
                    data['name'] = title_text.split('(')[0].strip()
            
            # 获取当前价格和涨跌幅（可能需要解析具体页面元素）
            price_elems = soup.find_all(class_='price')
            if price_elems:
                for elem in price_elems[:2]:
                    text = elem.get_text().strip()
                    if '%' in text:
                        try:
                            data['change_pct'] = float(text.replace('%', '').replace('+', ''))
                        except:
                            pass
                    else:
                        try:
                            data['price'] = float(text)
                        except:
                            pass
            
            return data
    except Exception as e:
        log_message(f"获取 {stock_code} 数据失败：{e}")
    return None

def check_alerts(stock_data, historical_data=None):
    """检查预警条件"""
    alerts = []
    
    if not stock_data or not stock_data['price']:
        return alerts
    
    price = stock_data['price']
    change_pct = stock_data['change_pct'] if stock_data['change_pct'] else 0
    code = stock_data['code']
    name = stock_data['name'] or code
    
    # 1. 价格区间预警
    if price < ALERT_CONFIG['price_lower']:
        alerts.append(f"⚠️ 价格低于 {ALERT_CONFIG['price_lower']} 元 ({price:.2f})")
    elif price > ALERT_CONFIG['price_upper']:
        alerts.append(f"⚠️ 价格高于 {ALERT_CONFIG['price_upper']} 元 ({price:.2f})")
    
    # 2. 涨跌幅预警
    if change_pct <= -ALERT_CONFIG['drop_threshold']:
        alerts.append(f"🔻 下跌超过 {ALERT_CONFIG['drop_threshold']}% ({change_pct}%)")
    elif change_pct >= ALERT_CONFIG['rise_threshold']:
        alerts.append(f"🔺 上涨超过 {ALERT_CONFIG['rise_threshold']}% ({change_pct}%)")
    
    # 3. 成交量翻倍预警（需历史对比）
    if historical_data and historical_data.get('volume'):
        current_volume = stock_data.get('volume', 0)
        if current_volume and current_volume >= historical_data['volume'] * 2:
            alerts.append(f"📊 成交量翻倍 ({current_volume})")
    
    return alerts

def send_feishu_alert(alerts, stock_data):
    """发送飞书预警消息"""
    if not alerts:
        return
    
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL')
    if not webhook_url:
        log_message("FEISHU_WEBHOOK_URL 未配置，跳过推送")
        return
    
    name = stock_data['name'] or stock_data['code']
    price = stock_data['price'] or 'N/A'
    
    message = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🦞 股票预警提醒"},
                "template": "red"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**股票：** {name}\n**现价：** {price}\n\n**预警内容:**\n" + "\n".join([f"- {a}" for a in alerts])}}
            ]
        }
    }
    
    try:
        requests.post(webhook_url, json=message, timeout=10)
        log_message(f"预警消息已发送至飞书：{name}")
    except Exception as e:
        log_message(f"飞书推送失败：{e}")

def load_watchlist():
    """加载监控列表"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    stocks.append({'code': parts[0], 'name': parts[1] if len(parts) > 1 else parts[0]})
    return stocks

def main():
    """主监控循环"""
    print(f"🦞 股票监控系统启动 - {datetime.now()}")
    log_message("=== 监控任务开始 ===")
    
    stocks = load_watchlist()
    print(f"监控标的数量：{len(stocks)}")
    
    all_alerts = []
    
    for stock in stocks:
        code = stock['code']
        print(f"正在检查 {code}...")
        
        # 获取实时数据
        data = get_stock_data(code)
        if data:
            # 检查预警
            alerts = check_alerts(data)
            if alerts:
                all_alerts.extend([(data, alerts)])
                log_message(f"{code} 触发预警：{alerts}")
        
        # 每次请求间隔 1 秒，避免过快
        time.sleep(1)
    
    # 发送所有预警
    for data, alerts in all_alerts:
        send_feishu_alert(alerts, data)
    
    print(f"本轮检查完成，共发现 {len(all_alerts)} 个预警")
    log_message(f"本轮检查完成，预警数：{len(all_alerts)}")

if __name__ == "__main__":
    main()
