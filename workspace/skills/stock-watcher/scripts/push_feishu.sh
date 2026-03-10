#!/bin/bash
# 通过 exec 工具调用 message API 推送飞书

cd /home/openclaw/.openclaw/workspace/skills/stock-watcher/scripts

# 获取股票数据
STOCK_DATA=$(python3 -c "
import os, sys, requests, re
from bs4 import BeautifulSoup

WATCHLIST_FILE = os.path.expanduser('~/.clawdbot/stock_watcher/watchlist.txt')

def fetch_stock(code):
    url = f'https://stockpage.10jqka.com.cn/{code}/'
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        name = ''
        if title:
            t = title.get_text()
            if '(' in t: name = t.split('(')[0].strip()
        pct = re.findall(r'[-+]?\d+\.?\d*%', r.text)
        return {'code': code, 'name': name or code, 'pct': pct[0] if pct else 'N/A'}
    except: return None

with open(WATCHLIST_FILE, 'r') as f:
    lines = [l.strip().split('|')[0] for l in f if '|' in l and l.strip()]

rows = []
for c in lines[:5]:
    d = fetch_stock(c)
    if d:
        emoji = '🟢' if '+' in d['pct'] else '🔴' if d['pct'] != 'N/A' else '⚪'
        rows.append(f'{emoji} {d[\"code\"]:<8} {d[\"name\"]:<10} {d[\"pct\"]}')
        import time; time.sleep(1)
print('\\n'.join(rows))
")

# 构建消息
TIMESTAMP=$(date '+%m-%d %H:%M')
MESSAGE="🦞 **【股票行情快报】** ${TIMESTAMP}

\`\`\`
------------------------------
代码      名称        涨跌幅     
------------------------------
${STOCK_DATA}
------------------------------
\`\`\`

📊 **数据来源：** 同花顺实时行情
⏱️ **下次更新：** 5 分钟后

---
🦞 龙虾自动推送服务"

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 推送股价数据" >> ~/.clawdbot/stock_watcher/push.log

# 输出到 stdout（会被 cron 捕获）
echo "$MESSAGE"
