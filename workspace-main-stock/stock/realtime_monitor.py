#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时股价监控脚本
- 获取自选股实时日线数据
- 根据预警规则过滤
- 输出预警数据
"""

import os
import sys
import json
import tushare as ts
from datetime import datetime

# 工作区路径
WORKSPACE = "/home/openclaw/.openclaw/workspace-main-stock"
STOCK_DIR = os.path.join(WORKSPACE, "stock")

# 文件路径
STOCK_LIST_FILE = os.path.join(STOCK_DIR, "stock-list.txt")
REALTIME_DATA_FILE = os.path.join(STOCK_DIR, "realtime-data.txt")
ALERT_RULES_FILE = os.path.join(STOCK_DIR, "alert-rules.md")
MONITOR_LOG_FILE = os.path.join(STOCK_DIR, "monitor-log.json")

def load_stock_list():
    """加载自选股列表"""
    stocks = []
    with open(STOCK_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                code, name, market = parts[0], parts[1], parts[2]
                ts_code = f"{code}.{market}"
                stocks.append({"ts_code": ts_code, "name": name})
    return stocks

def load_alert_rules():
    """加载预警规则"""
    rules = {
        "generic": {
            "fall_threshold": -1.0,  # 下跌 > 1%
            "rise_threshold": 1.0     # 上涨 > 1%
        },
        "stocks": {}
    }
    
    with open(ALERT_RULES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析个股专属规则
    lines = content.split('\n')
    current_stock = None
    for line in lines:
        line = line.strip()
        if line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
            # 个股规则标题，如 "1. 中国石油 (601857.SH)*:"
            if '(' in line and ')' in line:
                start = line.find('(') + 1
                end = line.find(')')
                ts_code = line[start:end]
                current_stock = ts_code
                rules["stocks"][current_stock] = {
                    "rise_threshold": 2.0,  # 默认
                    "fall_threshold": -1.0  # 默认
                }
        elif current_stock and ('🟢' in line or '🔴' in line):
            # 解析具体规则
            if '🟢' in line and '涨幅' in line:
                # 🟢 涨幅 > 2% → 触发预警
                if '>' in line and '%' in line:
                    val = line.split('>')[1].split('%')[0].strip()
                    try:
                        rules["stocks"][current_stock]["rise_threshold"] = float(val)
                    except:
                        pass
            elif '🔴' in line and ('跌幅' in line or '跌' in line):
                # 🔴 跌幅 > 1% → 触发预警
                if '>' in line and '%' in line:
                    val = line.split('>')[1].split('%')[0].strip()
                    try:
                        rules["stocks"][current_stock]["fall_threshold"] = -float(val)
                    except:
                        pass
    
    return rules

def get_realtime_data(stocks):
    """获取实时日线数据"""
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("ERROR: TUSHARE_TOKEN 环境变量未设置")
        return None
    
    pro = ts.pro_api(token)
    
    # 构建 ts_code 列表
    ts_codes = [s["ts_code"] for s in stocks]
    ts_code_str = ','.join(ts_codes)
    
    try:
        # 调用 rt_k 接口获取实时日线
        df = pro.rt_k(ts_code=ts_code_str)
        
        if df is None or df.empty:
            print("ERROR: 未获取到数据")
            return None
        
        # 转换为字典列表
        records = []
        for _, row in df.iterrows():
            record = {
                "ts_code": row.get('ts_code', ''),
                "name": row.get('name', ''),
                "pre_close": float(row.get('pre_close', 0)),
                "close": float(row.get('close', 0)),
                "high": float(row.get('high', 0)),
                "open": float(row.get('open', 0)),
                "low": float(row.get('low', 0)),
                "vol": int(row.get('vol', 0)),
                "amount": float(row.get('amount', 0)),
                "trade_time": row.get('trade_time', '')
            }
            # 计算涨跌幅和涨跌额
            if record["pre_close"] > 0:
                record["change_amt"] = record["close"] - record["pre_close"]
                record["change_pct"] = (record["change_amt"] / record["pre_close"]) * 100
            else:
                record["change_amt"] = 0
                record["change_pct"] = 0
            records.append(record)
        
        return records
    except Exception as e:
        print(f"ERROR: 获取数据失败 - {str(e)}")
        return None

def check_alert(data, rules):
    """检查是否触发预警"""
    ts_code = data["ts_code"]
    change_pct = data["change_pct"]
    
    # 获取该股票的规则
    if ts_code in rules["stocks"]:
        stock_rule = rules["stocks"][ts_code]
        rise_threshold = stock_rule.get("rise_threshold", 1.0)
        fall_threshold = stock_rule.get("fall_threshold", -1.0)
    else:
        # 使用通用规则
        rise_threshold = rules["generic"]["rise_threshold"]
        fall_threshold = rules["generic"]["fall_threshold"]
    
    # 检查是否触发
    if change_pct >= rise_threshold or change_pct <= fall_threshold:
        return True
    return False

def format_alert_message(alerts):
    """格式化预警消息"""
    if not alerts:
        return ""
    
    # 按涨跌幅排序
    alerts.sort(key=lambda x: x["change_pct"], reverse=True)
    
    # 构建表格
    lines = []
    lines.append("🚨 股价预警通知")
    lines.append("")
    lines.append("| 代码 | 名称 | 当前价 | 涨跌幅 | 涨跌额 | 时间 |")
    lines.append("|------|------|--------|--------|--------|------|")
    
    for alert in alerts:
        ts_code = alert["ts_code"]
        name = alert["name"]
        close = alert["close"]
        change_pct = alert["change_pct"]
        change_amt = alert["change_amt"]
        trade_time = alert.get("trade_time", "")
        
        # 格式化时间
        if trade_time:
            try:
                dt = datetime.strptime(trade_time, "%Y%m%d%H%M%S")
                time_str = dt.strftime("%H:%M")
            except:
                time_str = trade_time
        else:
            time_str = datetime.now().strftime("%H:%M")
        
        # 格式化涨跌幅
        if change_pct >= 0:
            change_pct_str = f"+{change_pct:.2f}%"
        else:
            change_pct_str = f"{change_pct:.2f}%"
        
        # 格式化涨跌额
        if change_amt >= 0:
            change_amt_str = f"¥{change_amt:.2f}"
        else:
            change_amt_str = f"¥{change_amt:.2f}"
        
        lines.append(f"| {ts_code.split('.')[0]} | {name} | ¥{close:.2f} | {change_pct_str} | {change_amt_str} | {time_str} |")
    
    lines.append("")
    lines.append("⚙️ 预警规则")
    lines.append("- 📉 下跌 > 1% → 触发")
    lines.append("- 📈 上涨 > 1% → 触发")
    lines.append("")
    lines.append("**【数据来源】**")
    lines.append("- 数据来源：Tushare Pro")
    lines.append(f"- 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return '\n'.join(lines)

def save_realtime_data(data):
    """保存实时数据到文件"""
    with open(REALTIME_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_monitor_log(log_data):
    """保存监控日志"""
    with open(MONITOR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def main():
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
        "errors": []
    }
    
    try:
        # 步骤 1: 加载自选股列表
        log_data["steps"].append({"step": 1, "action": "load_stock_list", "status": "start"})
        stocks = load_stock_list()
        log_data["steps"].append({"step": 1, "action": "load_stock_list", "status": "success", "data": stocks})
        print(f"已加载 {len(stocks)} 只自选股")
        
        # 步骤 2: 加载预警规则
        log_data["steps"].append({"step": 2, "action": "load_alert_rules", "status": "start"})
        rules = load_alert_rules()
        log_data["steps"].append({"step": 2, "action": "load_alert_rules", "status": "success", "data": rules})
        print(f"已加载预警规则")
        
        # 步骤 3: 获取实时数据
        log_data["steps"].append({"step": 3, "action": "get_realtime_data", "status": "start"})
        realtime_data = get_realtime_data(stocks)
        if realtime_data is None:
            log_data["steps"].append({"step": 3, "action": "get_realtime_data", "status": "failed", "error": "获取数据失败"})
            log_data["errors"].append("获取实时数据失败")
            save_monitor_log(log_data)
            sys.exit(1)
        log_data["steps"].append({"step": 3, "action": "get_realtime_data", "status": "success", "count": len(realtime_data)})
        print(f"已获取 {len(realtime_data)} 条实时数据")
        
        # 步骤 4: 保存实时数据（清空后写入）
        log_data["steps"].append({"step": 4, "action": "save_realtime_data", "status": "start"})
        save_realtime_data(realtime_data)
        log_data["steps"].append({"step": 4, "action": "save_realtime_data", "status": "success"})
        print(f"已保存实时数据到 {REALTIME_DATA_FILE}")
        
        # 步骤 5: 检查预警
        log_data["steps"].append({"step": 5, "action": "check_alerts", "status": "start"})
        alerts = []
        for data in realtime_data:
            if check_alert(data, rules):
                alerts.append(data)
        log_data["steps"].append({"step": 5, "action": "check_alerts", "status": "success", "alert_count": len(alerts)})
        print(f"发现 {len(alerts)} 条预警数据")
        
        if not alerts:
            print("无预警数据，任务结束")
            save_monitor_log(log_data)
            sys.exit(0)
        
        # 步骤 6: 格式化预警消息
        log_data["steps"].append({"step": 6, "action": "format_message", "status": "start"})
        message = format_alert_message(alerts)
        log_data["steps"].append({"step": 6, "action": "format_message", "status": "success"})
        
        # 步骤 7: 输出消息（由外部脚本处理推送）
        log_data["steps"].append({"step": 7, "action": "output_message", "status": "start"})
        print("\n=== 预警消息 ===")
        print(message)
        print("=== 结束 ===\n")
        
        # 保存预警消息到文件供外部读取
        alert_msg_file = os.path.join(STOCK_DIR, "alert-message.txt")
        with open(alert_msg_file, 'w', encoding='utf-8') as f:
            f.write(message)
        log_data["steps"].append({"step": 7, "action": "output_message", "status": "success", "file": alert_msg_file})
        
        # 保存日志
        save_monitor_log(log_data)
        print("监控日志已保存")
        
    except Exception as e:
        log_data["errors"].append(str(e))
        save_monitor_log(log_data)
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
