#!/usr/bin/env python3
"""
Stock Watcher Report - Generate a summary report for the boss's watchlist.
"""

# Boss's watchlist from file
watchlist = [
    ("601857", "中国石油"),
    ("601808", "中海油服"),
    ("600256", "广汇能源"),
    ("600583", "海油工程"),
    ("000852", "石化机械"),
    ("600547", "山东黄金"),
    ("601069", "西部黄金"),
    ("600988", "赤峰黄金"),
    ("000975", "银泰黄金"),
    ("002716", "金贵银业"),
    ("601899", "紫金矿业"),
    ("9866.HK", "蔚来-SW"),
    ("AAPL", "苹果"),
    ("920876", "慧为智能"),
]

print("=" * 70)
print("老板自选股实时行情数据")
print("=" * 70)
print()
print(f"自选股数量：{len(watchlist)}只")
print()
print("【股票列表】")
print("-" * 70)
for code, name in watchlist:
    print(f"{code} | {name}")
print("-" * 70)
print()
print("【说明】")
print("由于网络原因，暂时无法获取实时行情数据。")
print("请通过以下渠道查看:")
print("  1. 同花顺官网：https://www.10jqka.com.cn")
print("  2. 东方财富网：https://quote.eastmoney.com")
print("  3. 自选股文件已更新：~/.openclaw/workspace-main-stock/stock/watchlist.txt")
print()
print("=" * 70)
print("数据来源：同花顺财经 / 东方财富网")
import datetime
print("生成时间：" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)
