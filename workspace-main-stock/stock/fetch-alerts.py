#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
功能：获取实时数据、应用预警规则、发送飞书通知
"""

import json
import subprocess
from datetime import datetime
import os

# 配置路径
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-main-stock')
STOCK_DIR = os.path.join(WORKSPACE, 'stock')
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, 'realtime-data.txt')
WATCHLIST_FILE = os.path.join(STOCK_DIR, 'watchlist.txt')
LOG_FILE = os.path.join(STOCK_DIR, 'execution-log.jsonl')

# 预警规则
ALERT_RULES = {
    'default': {'rise_threshold': 0.05, 'fall_threshold': -0.03},
    '601857': {'rise_threshold': 0.02, 'fall_threshold': -0.01}  # 中国石油专属规则
}

def log_event(event_type, data):
    """记录执行日志"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'data': data
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

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

def fetch_realtime_data_tushare(stocks):
    """使用 tushare 获取实时日线数据 (rt_k 接口)"""
    log_event('api_call_start', {'interface': 'tushare.rt_k', 'stocks': [s['code'] for s in stocks]})
    
    try:
        import tushare as ts
        
        # 初始化（需要 token，从环境变量读取）
        token = os.environ.get('TUSHARE_TOKEN', '')
        if not token:
            # 尝试从配置文件读取
            config_path = os.path.join(STOCK_DIR, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    token = config.get('tushare_token', '')
        
        if not token:
            raise Exception("Tushare token not found")
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        results = []
        for stock in stocks:
            code = stock['code']
            try:
                # 使用 rt_k 接口获取实时日线数据
                df = pro.rt_k(ts_code=code, asset='A')
                
                if df is not None and len(df) > 0:
                    row = df.iloc[0]
                    result = {
                        'code': code,
                        'name': stock['name'],
                        'close': float(row['close']) if pd.notna(row.get('close')) else 0,
                        'pct_chg': float(row['pct_chg']) if pd.notna(row.get('pct_chg')) else 0,
                        'pre_close': float(row['pre_close']) if pd.notna(row.get('pre_close')) else 0,
                        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    result['change_amt'] = result['close'] - result['pre_close']
                    results.append(result)
                    log_event('api_success', {'code': code, 'data': result})
                else:
                    log_event('api_empty', {'code': code})
                    
            except Exception as e:
                log_event('api_error', {'code': code, 'error': str(e)})
        
        return results
        
    except ImportError:
        log_event('error', {'type': 'ImportError', 'message': 'tushare library not installed'})
        # 回退到同花顺网页抓取
        return fetch_realtime_data_10jqka(stocks)
    except Exception as e:
        log_event('error', {'type': 'Exception', 'message': str(e)})
        return []

def fetch_realtime_data_10jqka(stocks):
    """使用同花顺获取实时数据作为备用"""
    import urllib.request
    import re
    
    results = []
    for stock in stocks:
        code = stock['code']
        try:
            # 同花顺实时数据接口
            url = f'http://hqdata.niuniutrade.com/lqdn/{code}.json'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5)
            data = response.read().decode('utf-8')
            
            # 解析数据
            match = re.search(r'"lastPrice":([\d.]+),"changeRate":(-?\d+\.?\d*)', data)
            if match:
                price = float(match.group(1))
                pct = float(match.group(2))
                results.append({
                    'code': code,
                    'name': stock['name'],
                    'close': price,
                    'pct_chg': pct,
                    'pre_close': price / (1 + pct/100) if pct != 0 else price,
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                log_event('api_success', {'code': code, 'source': '10jqka', 'data': {'close': price, 'pct_chg': pct}})
        except Exception as e:
            log_event('api_error', {'code': code, 'source': '10jqka', 'error': str(e)})
    
    return results

def check_market_status():
    """检查是否收盘或休市"""
    now = datetime.now()
    hour, minute = now.hour, now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # 周末休市
    if weekday >= 5:
        return True, "周末休市"
    
    # 交易时间：9:30-11:30, 13:00-15:00
    morning_start, morning_end = 9 * 60 + 30, 11 * 60 + 30
    afternoon_start, afternoon_end = 13 * 60, 15 * 60
    current_minutes = hour * 60 + minute
    
    if not (morning_start <= current_minutes < morning_end or afternoon_start <= current_minutes < afternoon_end):
        return True, "非交易时间"
    
    return False, "交易中"

def apply_alert_rules(stock_data):
    """应用预警规则过滤数据"""
    alerts = []
    
    for stock in stock_data:
        code = stock['code'].split('.')[0]  # 去掉后缀
        pct = stock['pct_chg']
        
        # 获取该股的预警规则
        rules = ALERT_RULES.get(code, ALERT_RULES['default'])
        rise_threshold = rules['rise_threshold'] * 100  # 转换为百分比
        fall_threshold = rules['fall_threshold'] * 100
        
        triggered = False
        reason = ""
        
        if pct > rise_threshold:
            triggered = True
            reason = f"上涨超过{rise_threshold:.1f}%"
        elif pct < fall_threshold:
            triggered = True
            reason = f"下跌超过{abs(fall_threshold):.1f}%"
        
        if triggered:
            stock['trigger_reason'] = reason
            alerts.append(stock)
    
    return alerts

def format_alert_message(alerts):
    """格式化预警消息"""
    now = datetime.now()
    header = f"⚠️ 实时股价预警通知\n更新时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "=" * 50 + "\n\n"
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x['pct_chg'], reverse=True)
    
    table_header = "| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 触发原因 |\n"
    table_header += "|------|------|--------|--------|--------|----------|\n"
    
    lines = [header, table_header]
    
    for stock in alerts:
        change_sign = "+" if stock['change_amt'] >= 0 else ""
        pct_sign = "+" if stock['pct_chg'] >= 0 else ""
        row = f"| {stock['code']} | {stock['name']} | ¥{stock['close']:.2f} | {pct_sign}{stock['pct_chg']:.2f}% | {change_sign}{stock['change_amt']:.2f} | {stock['trigger_reason']} |\n"
        lines.append(row)
    
    footer = f"\n⚙️ 预警规则\n- 📉 下跌 > 3% → 触发 (个股可能不同)\n- 📈 上涨 > 5% → 触发 (个股可能不同)\n\n数据来源：Tushare Pro / 同花顺"
    
    return ''.join(lines) + footer

def send_feishu_broadcast(message, receivers):
    """通过飞书广播推送消息"""
    cmd_parts = [
        'openclaw', 'message', 'broadcast',
        '--channel', 'feishu',
        '--account', 'stock',
    ]
    
    for receiver in receivers:
        cmd_parts.extend(['--targets', receiver])
    
    # message 参数需要在最后
    cmd_parts.extend(['--message', message])
    
    log_event('broadcast_command', {'command': ' '.join(cmd_parts), 'receivers': receivers})
    
    result = subprocess.run(cmd_parts, capture_output=True, text=True)
    
    return {
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }

def send_log_to_group(log_content, group_id='oc_e5021f4489531f598034cdfc2e0394f6'):
    """发送日志到群聊"""
    cmd = [
        'openclaw', 'message', 'send',
        '--channel', 'feishu',
        '--account', 'stock',
        '--target', group_id,
        '--message', log_content
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def main():
    """主函数"""
    log_event('task_start', {'message': '实时股价监控任务开始'})
    
    # 步骤 1：检查市场状态
    is_closed, reason = check_market_status()
    log_event('market_status', {'is_closed': is_closed, 'reason': reason})
    
    if is_closed:
        log_event('task_end', {'reason': reason})
        print(f"市场未开盘：{reason}")
        return
    
    print("市场交易中，继续获取数据...")
    
    # 步骤 2：清空 realtime-data.txt
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write("")
    log_event('file_cleared', {'file': REALTIME_DATA_FILE})
    
    # 步骤 3：读取自选股并获取实时数据
    stocks = read_watchlist()
    log_event('watchlist_loaded', {'count': len(stocks), 'stocks': [s['code'] for s in stocks]})
    
    stock_data = fetch_realtime_data_tushare(stocks)
    log_event('data_fetched', {'count': len(stock_data)})
    
    # 写入实时数据文件
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("数据来源：Tushare Pro\n")
        f.write("-" * 80 + "\n")
        for stock in stock_data:
            f.write(f"{stock['code']}|{stock['name']}|{stock['close']:.2f}|{stock['pct_chg']:.2f}|{stock['change_amt']:.2f}|{stock['datetime']}\n")
        f.write("=" * 80 + "\n")
    
    # 步骤 4：应用预警规则
    alerts = apply_alert_rules(stock_data)
    log_event('alerts_filtered', {'count': len(alerts)})
    
    if not alerts:
        log_event('task_end', {'reason': '无满足预警条件的股票'})
        print("本次暂无满足预警条件的股票")
        return
    
    # 步骤 5：读取接收者列表
    with open(os.path.join(STOCK_DIR, 'receiver-list.txt'), 'r', encoding='utf-8') as f:
        receivers = [line.strip() for line in f if line.strip()]
    
    # 步骤 6：发送预警通知
    message = format_alert_message(alerts)
    
    broadcast_result = send_feishu_broadcast(message, receivers)
    log_event('broadcast_result', {'result': broadcast_result})
    
    print(f"已发送 {len(alerts)} 条预警信息给 {len(receivers)} 个接收者")
    
    # 步骤 7：发送执行日志到群聊
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    log_send_result = send_log_to_group(log_content)
    log_event('log_sent', {'result': log_send_result})
    
    log_event('task_complete', {'alerts_sent': len(alerts)})
    print("任务完成!")

if __name__ == '__main__':
    main()
