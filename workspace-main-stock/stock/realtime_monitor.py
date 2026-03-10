#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本 - 使用 tushare 实时接口
按照 realtime-data-cron-config.md 的要求执行
"""

import os
import sys
import tushare as ts
from datetime import datetime

# 配置
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORKSPACE, 'stock')
WATCHLIST_FILE = os.path.join(STOCK_DIR, 'watchlist.txt')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')

# 初始化 tushare
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

def read_watchlist():
    """读取自选股列表"""
    stocks = []
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                code, name = line.split('|')
                stocks.append({'code': code, 'name': name})
    return stocks

def check_market_status():
    """检查今日是否交易日且未收盘"""
    today = datetime.now().strftime('%Y%m%d')
    # 获取交易日历
    try:
        cal = pro.trade_cal(exchange='SSE', start_date=today, end_date=today, is_open='1')
        if cal.empty:
            print(f"今日 ({today}) 不是交易日，结束任务")
            return False
        
        # 检查当前时间是否在交易时间内
        now = datetime.now()
        current_time = now.strftime('%H%M')
        
        # A 股交易时间：9:30-11:30, 13:00-15:00
        if current_time < '0930' or (current_time >= '1130' and current_time < '1300') or current_time >= '1500':
            print(f"当前时间 {current_time} 不在交易时间内，结束任务")
            return False
        
        print(f"今日是交易日，当前在交易时间内")
        return True
    except Exception as e:
        print(f"检查交易日历失败：{e}")
        # 如果获取失败，默认继续
        return True

def clear_realtime_data():
    """清空 realtime-data.txt"""
    if os.path.exists(REALTIME_DATA_FILE):
        with open(REALTIME_DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if content:
            with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            print("已清空 realtime-data.txt")

def get_realtime_data(stocks):
    """获取实时数据 - 使用实时日线接口"""
    # 转换股票代码格式为 tushare 格式
    ts_codes = []
    stock_map = {}
    
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        
        # 处理不同市场的股票代码
        if code.endswith('.HK'):
            # 港股 - 保持原样
            ts_code = code.upper()
        elif code.endswith('.SH') or code.endswith('.SZ'):
            ts_code = code.upper()
        elif code.isdigit():
            # A 股，需要判断市场
            if code.startswith('6') or code.startswith('9'):
                ts_code = f"{code}.SH"
            elif code.startswith('0') or code.startswith('3'):
                ts_code = f"{code}.SZ"
            else:
                ts_code = f"{code}.SH"  # 默认
        else:
            # 美股等
            ts_code = code.upper()
        
        ts_codes.append(ts_code)
        stock_map[ts_code] = name
    
    print(f"获取股票数据：{ts_codes}")
    
    # 获取实时日线数据
    all_data = []
    
    # 尝试使用通用行情接口
    try:
        # 分批获取，避免限流
        batch_size = 5
        
        for i in range(0, len(ts_codes), batch_size):
            batch_codes = ts_codes[i:i+batch_size]
            
            for ts_code in batch_codes:
                try:
                    # 使用实时日线接口
                    df = pro.daily(ts_code=ts_code, start_date=datetime.now().strftime('%Y%m%d'), 
                                  end_date=datetime.now().strftime('%Y%m%d'))
                    
                    if not df.empty:
                        row = df.iloc[0]
                        name = stock_map.get(ts_code, '未知')
                        
                        # 计算涨跌幅
                        pre_close = row['pre_close']
                        close = row['close']
                        change = close - pre_close
                        pct_chg = (change / pre_close) * 100 if pre_close > 0 else 0
                        
                        all_data.append({
                            'code': ts_code.split('.')[0],
                            'name': name,
                            'price': close,
                            'change_pct': pct_chg,
                            'change_amount': change,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except Exception as e:
                    print(f"获取 {ts_code} 失败：{e}")
                    # 标记为 N/A
                    name = stock_map.get(ts_code, '未知')
                    all_data.append({
                        'code': ts_code.split('.')[0],
                        'name': name,
                        'price': None,
                        'change_pct': None,
                        'change_amount': None,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return all_data
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        return []

def save_realtime_data(data):
    """保存实时数据到文件"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write("代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间\n")
        for item in data:
            if item['price'] is not None:
                f.write(f"{item['code']} | {item['name']} | ¥{item['price']:.2f} | {item['change_pct']:+.2f}% | ¥{item['change_amount']:.2f} | {item['timestamp']}\n")
            else:
                f.write(f"{item['code']} | {item['name']} | N/A | N/A | N/A | {item['timestamp']}\n")
    print(f"已保存 {len(data)} 条数据到 realtime-data.txt")

def check_alert_rules(data):
    """检查预警规则"""
    alerts = []
    
    for item in data:
        if item['price'] is None:
            continue
            
        code = item['code']
        name = item['name']
        change_pct = item['change_pct']
        triggered = False
        reason = ""
        
        # 通用规则
        if change_pct < -3:
            triggered = True
            reason = f"📉 下跌 {change_pct:.2f}% > 3%"
        elif change_pct > 5:
            triggered = True
            reason = f"📈 上涨 {change_pct:.2f}% > 5%"
        
        # 个股专属规则 - 中国石油 (601857)
        if code == '601857':
            if change_pct > 2:
                triggered = True
                reason = f"🟢 中国石油涨幅 {change_pct:.2f}% > 2%"
            elif change_pct < -1:
                triggered = True
                reason = f"🔴 中国石油跌幅 {change_pct:.2f}% > 1%"
        
        if triggered:
            alerts.append({
                **item,
                'alert_reason': reason
            })
    
    return alerts

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return ""
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_pct'] if x['change_pct'] else 0, reverse=True)
    
    # 构建表格
    lines = ["⚠️ 股价预警通知", ""]
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|-------|------|")
    
    for alert in alerts[:10]:  # 最多 10 条
        lines.append(f"| {alert['code']} | {alert['name']} | ¥{alert['price']:.2f} | {alert['change_pct']:+.2f}% | ¥{alert['change_amount']:.2f} | {alert['timestamp'].split(' ')[1][:5]} |")
    
    lines.append("")
    lines.append("⚙️ 预警规则")
    lines.append("• 📉 下跌 > 3% → 触发")
    lines.append("• 📈 上涨 > 5% → 触发")
    lines.append("• 🟢 中国石油：涨幅 > 2% 或 跌幅 > 1% → 触发")
    
    return "\n".join(lines)

def read_receiver_list():
    """读取接收者列表"""
    receiver_file = os.path.join(STOCK_DIR, 'receiver-list.txt')
    receivers = []
    if os.path.exists(receiver_file):
        with open(receiver_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    receivers.append(line)
    return receivers

def send_alert(message, receivers):
    """发送预警消息"""
    if not receivers or not message:
        print("没有接收者或没有消息内容")
        return
    
    # 构建命令
    targets = ' '.join([f'--targets {r}' for r in receivers])
    cmd = f'openclaw message broadcast --channel feishu --account stock {targets} --message "{message}"'
    print(f"执行命令：{cmd}")
    
    # 执行命令
    os.system(cmd)

def main():
    print("=" * 50)
    print("实时股价监控任务开始")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 步骤 1: 检查市场状态
    if not check_market_status():
        print("任务结束")
        return
    
    # 步骤 2: 清空实时数据文件
    clear_realtime_data()
    
    # 步骤 3: 读取自选股
    stocks = read_watchlist()
    print(f"读取到 {len(stocks)} 只自选股")
    
    # 步骤 4: 获取实时数据
    data = get_realtime_data(stocks)
    if not data:
        print("未获取到实时数据，任务结束")
        return
    
    # 步骤 5: 保存实时数据
    save_realtime_data(data)
    
    # 步骤 6: 检查预警规则
    alerts = check_alert_rules(data)
    if not alerts:
        print("没有触发预警的股票，任务结束")
        return
    
    print(f"发现 {len(alerts)} 条预警信息")
    
    # 步骤 7: 读取接收者列表并发送
    receivers = read_receiver_list()
    print(f"接收者数量：{len(receivers)}")
    
    message = format_alert_message(alerts)
    send_alert(message, receivers)
    
    print("=" * 50)
    print("任务完成")
    print("=" * 50)

if __name__ == '__main__':
    main()
