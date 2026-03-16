#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
执行流程：
1. 检查今日是否交易日
2. 获取自选股实时日线数据
3. 根据预警规则过滤
4. 返回满足条件的数据
"""

import os
import sys
import tushare as ts
from datetime import datetime

# 配置
WORKSPACE = "/home/openclaw/.openclaw/workspace-main-stock"
STOCK_LIST_FILE = f"{WORKSPACE}/stock/stock-list.txt"
REALTIME_DATA_FILE = f"{WORKSPACE}/stock/realtime-data.txt"
ALERT_RULES_FILE = f"{WORKSPACE}/stock/alert-rules.md"

# 获取 token
token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误：未找到 TUSHARE_TOKEN 环境变量")
    sys.exit(1)

# 初始化 pro 接口
pro = ts.pro_api(token)

def read_stock_list():
    """读取自选股列表"""
    stocks = []
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                code = parts[0]
                name = parts[1]
                market = parts[2]
                ts_code = f"{code}.{market}"
                stocks.append({'code': code, 'name': name, 'market': market, 'ts_code': ts_code})
    return stocks

def check_trading_day():
    """检查今日是否交易日"""
    today = datetime.now().strftime('%Y%m%d')
    try:
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        if df.empty:
            print(f"今日 ({today}) 不是交易日")
            return False
        is_open = df.iloc[0]['is_open']
        if is_open == '0':
            print(f"今日 ({today}) 休市")
            return False
        print(f"今日 ({today}) 是交易日，继续执行")
        return True
    except Exception as e:
        print(f"检查交易日失败：{e}")
        # 如果检查失败，默认继续执行（避免误判）
        return True

def get_realtime_data(stocks):
    """获取实时日线数据"""
    ts_codes = ','.join([s['ts_code'] for s in stocks])
    print(f"获取实时数据：{ts_codes}")
    
    try:
        df = pro.rt_k(ts_code=ts_codes)
        print(f"获取到 {len(df)} 条数据")
        return df
    except Exception as e:
        print(f"获取实时数据失败：{e}")
        return None

def save_realtime_data(df, stocks):
    """保存实时数据到文件"""
    if df is None or df.empty:
        print("无数据可保存")
        return
    
    # 创建股票映射
    stock_map = {s['ts_code']: s for s in stocks}
    
    # 生成文件内容
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# 实时股价数据 - 更新时间：{now}",
        "# 数据来源：Tushare Pro (rt_k 接口)",
        "",
        "代码\t名称\t最新价\t昨收价\t涨跌幅%\t涨跌额\t开盘价\t最高价\t最低价\t成交量\t成交额\t时间"
    ]
    
    for _, row in df.iterrows():
        ts_code = row['ts_code']
        stock = stock_map.get(ts_code, {})
        name = stock.get('name', row.get('name', ''))
        
        # 计算涨跌幅和涨跌额
        pre_close = row.get('pre_close', 0)
        close = row.get('close', 0)
        change_amt = close - pre_close if pre_close > 0 else 0
        change_pct = (change_amt / pre_close * 100) if pre_close > 0 else 0
        
        # 格式化时间
        trade_time = row.get('trade_time', '')
        if trade_time and len(trade_time) >= 19:
            trade_time = trade_time[11:19]  # 提取 HH:MM:SS
        
        line = f"{row['ts_code'].split('.')[0]}\t{name}\t{close:.2f}\t{pre_close:.2f}\t{change_pct:+.2f}%\t{change_amt:+.2f}\t{row.get('open', 0):.2f}\t{row.get('high', 0):.2f}\t{row.get('low', 0):.2f}\t{row.get('vol', 0)}\t{row.get('amount', 0)}\t{trade_time}"
        lines.append(line)
    
    # 写入文件
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"数据已保存到 {REALTIME_DATA_FILE}")
    return '\n'.join(lines)

def check_alert_rules(df, stocks):
    """检查预警规则并返回满足条件的数据"""
    if df is None or df.empty:
        return []
    
    # 创建股票映射
    stock_map = {s['ts_code']: s for s in stocks}
    
    alerts = []
    
    # 预警规则（从 alert-rules.md 读取）
    # 当前规则状态：已关闭
    # 但根据任务要求，需要检查规则
    # 规则：
    # - 通用规则：已关闭
    # - 中国石油 (601857.SH): 涨幅>2% 或 跌幅>1%
    
    for _, row in df.iterrows():
        ts_code = row['ts_code']
        stock = stock_map.get(ts_code, {})
        code = stock.get('code', ts_code.split('.')[0])
        name = stock.get('name', row.get('name', ''))
        
        pre_close = row.get('pre_close', 0)
        close = row.get('close', 0)
        change_amt = close - pre_close if pre_close > 0 else 0
        change_pct = (change_amt / pre_close * 100) if pre_close > 0 else 0
        
        triggered = False
        rule_name = ""
        
        # 检查中国石油专属规则
        if code == '601857':
            if change_pct > 2:
                triggered = True
                rule_name = "🟢 涨幅 > 2%"
            elif change_pct < -1:
                triggered = True
                rule_name = "🔴 跌幅 > 1%"
        
        if triggered:
            trade_time = row.get('trade_time', '')
            if trade_time and len(trade_time) >= 19:
                trade_time = trade_time[11:19]
            
            alerts.append({
                'code': code,
                'name': name,
                'close': close,
                'change_pct': change_pct,
                'change_amt': change_amt,
                'time': trade_time,
                'rule': rule_name
            })
    
    return alerts

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return None
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['change_pct'], reverse=True)
    
    lines = [
        "🚨 **股价预警通知**",
        "",
        "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |",
        "|------|------|--------|--------|--------|------|"
    ]
    
    for alert in alerts[:10]:  # 最多 10 条
        sign = "+" if alert['change_pct'] >= 0 else ""
        amt_sign = "+" if alert['change_amt'] >= 0 else ""
        lines.append(f"| {alert['code']} | {alert['name']} | ¥{alert['close']:.2f} | {sign}{alert['change_pct']:.2f}% | {amt_sign}{alert['change_amt']:.2f} | {alert['time']} |")
    
    lines.extend([
        "",
        "⚙️ **预警规则**",
        "- 📉 跌幅 > 1% → 触发（中国石油）",
        "- 📈 涨幅 > 2% → 触发（中国石油）",
        "",
        f"**【数据来源】**",
        "- 数据来源：Tushare Pro",
        f"- 更新时间：{now}"
    ])
    
    return '\n'.join(lines)

def main():
    """主函数"""
    print("=" * 50)
    print("实时股价监控任务开始")
    print("=" * 50)
    
    # 步骤 1: 检查是否交易日
    print("\n[步骤 1] 检查交易日...")
    if not check_trading_day():
        print("今日休市，任务结束")
        return {'status': 'closed', 'message': '今日休市'}
    
    # 步骤 2: 读取自选股列表
    print("\n[步骤 2] 读取自选股列表...")
    stocks = read_stock_list()
    print(f"自选股数量：{len(stocks)}")
    for s in stocks:
        print(f"  - {s['ts_code']} {s['name']}")
    
    # 步骤 3: 获取实时数据
    print("\n[步骤 3] 获取实时日线数据...")
    df = get_realtime_data(stocks)
    if df is None or df.empty:
        print("获取数据失败，任务结束")
        return {'status': 'error', 'message': '获取数据失败'}
    
    # 步骤 4: 保存实时数据
    print("\n[步骤 4] 保存实时数据...")
    save_realtime_data(df, stocks)
    
    # 步骤 5: 检查预警规则
    print("\n[步骤 5] 检查预警规则...")
    alerts = check_alert_rules(df, stocks)
    print(f"触发预警数量：{len(alerts)}")
    
    if not alerts:
        print("无预警信息，任务结束")
        return {'status': 'success', 'message': '无预警', 'alerts': []}
    
    # 步骤 6: 格式化预警消息
    print("\n[步骤 6] 格式化预警消息...")
    message = format_alert_message(alerts)
    print(message)
    
    return {
        'status': 'success',
        'message': '有预警',
        'alerts': alerts,
        'alert_message': message
    }

if __name__ == '__main__':
    result = main()
    print("\n" + "=" * 50)
    print(f"任务执行结果：{result['status']}")
    print(f"消息：{result['message']}")
    print("=" * 50)
