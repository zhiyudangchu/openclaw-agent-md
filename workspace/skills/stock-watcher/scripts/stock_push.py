#!/usr/bin/env python3
"""
股票行情定时推送到飞书
每 5 分钟推送一次监控组合的最新股价
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

# 配置路径
WATCHLIST_FILE = os.path.expanduser("~/.clawdbot/stock_watcher/watchlist.txt")
LOG_DIR = os.path.expanduser("~/.clawdbot/stock_watcher")
PUSH_LOG = os.path.join(LOG_DIR, "push.log")

# Feishu target (老板的 OpenID)
FEISHU_TARGET = "ou_9d907d39fb19b50579ba289b30041fc5"

def log_message(message):
    """记录日志"""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PUSH_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def fetch_stock_data(stock_code):
    """从同花顺获取股票数据"""
    url = f"https://stockpage.10jqka.com.cn/{stock_code}/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取名称
        title = soup.find('title')
        stock_name = ""
        if title:
            title_text = title.get_text()
            if '(' in title_text and ')' in title_text:
                stock_name = title_text.split('(')[0].strip()
        
        # 提取涨跌幅数据
        import re
        text_content = soup.get_text()
        percentages = re.findall(r'[-+]?\d+\.?\d*%', text_content)
        
        return {
            'code': stock_code,
            'name': stock_name or stock_code,
            'changes': percentages[:3] if percentages else []
        }
        
    except Exception as e:
        log_message(f"获取 {stock_code} 数据失败：{e}")
        return None

def send_feishu_message(stocks_data):
    """发送飞书消息（通过 OpenClaw message 工具）"""
    if not stocks_data:
        return False
    
    # 构建报表内容
    timestamp = datetime.now().strftime("%m-%d %H:%M")
    
    # 格式化表格行
    rows = []
    for stock in stocks_data:
        code = stock['code']
        name = stock['name']
        change = stock['changes'][0] if stock['changes'] else 'N/A'
        emoji = '🟢' if '+' in str(change) else '🔴' if change != 'N/A' else '⚪'
        rows.append(f"{emoji} {code} | {name} | {change}")
    
    content = f"""🦞 **【股票行情快报】** {timestamp}

```
{'-'*30}
{'代码':<10} {'名称':<8} {'涨跌幅':<8}
{'-'*30}
"""
    for stock in stocks_data:
        code = stock['code']
        name = stock['name']
        change = stock['changes'][0] if stock['changes'] else 'N/A'
        content += f"{code:<10} {name:<8} {change:<8}\n"
    
    content += f"{'-'*30}\n```\n\n📊 **数据来源：** 同花顺实时行情\n⏱️ **下次更新：** 5 分钟后\n\n---\n🦞 龙虾自动推送服务"
    
    # 调用 OpenClaw message API
    webhook_url = os.environ.get('OPENCLAW_WEBHOOK_URL')
    if webhook_url:
        try:
            response = requests.post(webhook_url, json={
                'action': 'send',
                'channel': 'feishu',
                'target': FEISHU_TARGET,
                'message': content
            }, timeout=10)
            return response.status_code == 200
        except Exception as e:
            log_message(f"Feishu 推送失败：{e}")
    
    # 打印输出（cron 环境下的调试模式）
    print(content)
    return True

def load_watchlist():
    """加载监控列表"""
    stocks = []
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    stocks.append(parts[0])
    return stocks

def main():
    """主推送函数"""
    log_message("=== 开始股价推送 ===")
    
    # 获取监控列表
    stock_codes = load_watchlist()
    if not stock_codes:
        log_message("监控列表为空")
        return
    
    # 获取所有股票数据
    stocks_data = []
    for code in stock_codes:
        data = fetch_stock_data(code)
        if data:
            stocks_data.append(data)
            time.sleep(1)  # 控制请求频率
    
    # 发送推送
    if stocks_data:
        success = send_feishu_message(stocks_data)
        if success:
            log_message(f"推送成功，共 {len(stocks_data)} 只股票")
        else:
            log_message("推送失败")

if __name__ == "__main__":
    main()
