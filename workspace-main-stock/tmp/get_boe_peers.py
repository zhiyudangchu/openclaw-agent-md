import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

print("=" * 80)
print("京东方 A - 同行业可比公司估值数据收集")
print("=" * 80)

# 显示面板行业主要可比公司
peer_companies = [
    ('000725.SZ', '京东方 A'),
    ('000050.SZ', '深天马 A'),
    ('000100.SZ', 'TCL 科技'),
    ('688036.SH', '传音控股'),
    ('300088.SZ', '长信科技'),
    ('300433.SZ', '蓝思科技'),
    ('002387.SZ', '维信诺'),
    ('688127.SH', '蓝特光学'),
]

print("\n【可比公司列表】")
for code, name in peer_companies:
    print(f"  {code} - {name}")

# 获取各公司最新行情和估值数据
print("\n【可比公司估值数据】")
valuation_data = []

for ts_code, name in peer_companies:
    try:
        # 获取最新行情
        daily = pro.daily(ts_code=ts_code, start_date='20260301', end_date='20260311')
        if len(daily) == 0:
            continue
        latest_price = daily.sort_values('trade_date', ascending=False).iloc[0]['close']
        
        # 获取基本财务数据
        fina_main = pro.fina_main_ts(ts_code=ts_code, fields='ts_code,ann_date,basic_eps,diluted_eps,total_revenue,net_profit')
        if len(fina_main) == 0:
            continue
        
        # 获取股本数据
        stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,tot_shr,act_shr')
        if len(stock_info) == 0:
            continue
        
        tot_shr = stock_info.iloc[0]['tot_shr']
        market_cap = latest_price * tot_shr / 100000000  # 亿元
        
        # 获取最新 ROE 和 PB
        indicators = pro.fina_indicator(ts_code=ts_code, fields='ts_code,ann_date,roe')
        latest_roe = indicators.sort_values('ann_date', ascending=False).iloc[0]['roe'] if len(indicators) > 0 else None
        
        # 获取每股净资产
        per_share = pro.fina_per_share(ts_code=ts_code, fields='ts_code,ann_date,bps')
        latest_bps = per_share.sort_values('ann_date', ascending=False).iloc[0]['bps'] if len(per_share) > 0 else None
        
        # 计算 PE 和 PB
        latest_eps = fina_main.sort_values('ann_date', ascending=False).iloc[0]['basic_eps'] if len(fina_main) > 0 else None
        
        pe = latest_price / latest_eps if latest_eps and latest_eps > 0 else None
        pb = latest_price / latest_bps if latest_bps and latest_bps > 0 else None
        
        valuation_data.append({
            '代码': ts_code,
            '名称': name,
            '股价': round(latest_price, 2),
            '市值 (亿)': round(market_cap, 2),
            'PE(TTM)': round(pe, 2) if pe else 'N/A',
            'PB': round(pb, 2) if pb else 'N/A',
            'ROE(%)': round(latest_roe, 2) if latest_roe else 'N/A',
            'EPS': round(latest_eps, 4) if latest_eps else 'N/A',
            'BPS': round(latest_bps, 2) if latest_bps else 'N/A',
        })
        
    except Exception as e:
        print(f"获取 {ts_code} 数据失败：{e}")
        continue

# 创建 DataFrame 并排序
df_valuation = pd.DataFrame(valuation_data)
print("\n可比公司估值比较：")
print(df_valuation.to_string(index=False))

# 计算行业平均和中位数
pe_values = [x for x in df_valuation['PE(TTM)'] if isinstance(x, (int, float))]
pb_values = [x for x in df_valuation['PB'] if isinstance(x, (int, float))]

if pe_values:
    print(f"\n行业 PE 平均值：{sum(pe_values)/len(pe_values):.2f}")
    print(f"行业 PE 中位数：{sorted(pe_values)[len(pe_values)//2]:.2f}")

if pb_values:
    print(f"行业 PB 平均值：{sum(pb_values)/len(pb_values):.2f}")
    print(f"行业 PB 中位数：{sorted(pb_values)[len(pb_values)//2]:.2f}")

# 京东方 A 的排名
boe_row = df_valuation[df_valuation['代码'] == '000725.SZ']
if len(boe_row) > 0:
    boe_pe = boe_row.iloc[0]['PE(TTM)']
    boe_pb = boe_row.iloc[0]['PB']
    
    if isinstance(boe_pe, (int, float)):
        pe_rank = sum(1 for x in pe_values if isinstance(x, (int, float)) and x < boe_pe) + 1
        print(f"\n京东方 A PE 排名：{pe_rank}/{len(pe_values)} (从小到大)")
    
    if isinstance(boe_pb, (int, float)):
        pb_rank = sum(1 for x in pb_values if isinstance(x, (int, float)) and x < boe_pb) + 1
        print(f"京东方 A PB 排名：{pb_rank}/{len(pb_values)} (从小到大)")

print("\n" + "=" * 80)
