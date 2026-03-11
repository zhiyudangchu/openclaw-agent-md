import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 京东方 A 股票代码
ts_code = '000725.SZ'

print("=" * 80)
print("京东方 A (000725.SZ) - 基本面数据收集")
print("=" * 80)

# 1. 获取股票基本信息
print("\n【1】股票基本信息")
stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,area,industry,market,list_date,act_shr,tot_shr')
print(stock_info)

# 2. 获取公司基本信息
print("\n【2】公司基本信息")
try:
    company_info = pro.stock_company(ts_code=ts_code, fields='ts_code,chairman,manager,website,employee_total,introduction,province,city')
    print(company_info)
except Exception as e:
    print(f"获取公司信息失败：{e}")

# 3. 获取最新财务指标
print("\n【3】最新财务指标")
try:
    indicators = pro.fina_indicator(ts_code=ts_code, fields='ts_code,ann_date,roe,roa,grossprofit_margin,net_profit_margin,debt_to_assets,current_ratio,quick_ratio,eps,dpsps,operate_cash_flow_ps,assets_turnover_rt')
    indicators = indicators.sort_values('ann_date', ascending=False).head(12)
    print(indicators)
except Exception as e:
    print(f"获取财务指标失败：{e}")

# 4. 获取利润表主要数据
print("\n【4】利润表主要数据（年度）")
try:
    income = pro.income(ts_code=ts_code, fields='ts_code,ann_date,total_revenue,operating_profit,net_profit,interest_income,fee_income', start_date='20200101', end_date='20251231')
    income = income.sort_values('ann_date', ascending=False)
    print(income)
except Exception as e:
    print(f"获取利润表失败：{e}")

# 5. 获取资产负债表主要数据
print("\n【5】资产负债表主要数据")
try:
    balance = pro.balancesheet(ts_code=ts_code, fields='ts_code,ann_date,total_assets,total_liab,total_hldr_eqy_inc_min_int,non_current_assets,current_assets', start_date='20200101', end_date='20251231')
    balance = balance.sort_values('ann_date', ascending=False)
    print(balance)
except Exception as e:
    print(f"获取资产负债表失败：{e}")

# 6. 获取现金流量表主要数据
print("\n【6】现金流量表主要数据")
try:
    cashflow = pro.cashflow(ts_code=ts_code, fields='ts_code,ann_date,operate_cash_flow,invest_cash_flow,finance_cash_flow,free_cash_flow', start_date='20200101', end_date='20251231')
    cashflow = cashflow.sort_values('ann_date', ascending=False)
    print(cashflow)
except Exception as e:
    print(f"获取现金流量表失败：{e}")

# 7. 获取前十大股东
print("\n【7】前十大流通股东")
try:
    top10_holders = pro.top10_floatholders(ts_code=ts_code, ann_date='20241231')
    print(top10_holders)
except Exception as e:
    print(f"获取股东数据失败：{e}")

# 8. 获取概念板块信息
print("\n【8】所属概念板块")
try:
    concept_data = pro.concept_detail(ts_code=ts_code)
    print(concept_data)
except Exception as e:
    print(f"获取板块数据失败：{e}")

# 9. 获取行业分类
print("\n【9】申万行业分类")
try:
    # 获取申万行业成分
    sw_index = pro.index_classify(level='L1', src='SW2021')
    print(sw_index)
except Exception as e:
    print(f"获取行业分类失败：{e}")

# 10. 获取日线行情（用于计算估值）
print("\n【10】近期股价数据")
try:
    daily = pro.daily(ts_code=ts_code, start_date='20250101', end_date='20260311')
    daily = daily.sort_values('trade_date', ascending=False).head(20)
    print(daily)
except Exception as e:
    print(f"获取行情数据失败：{e}")

# 11. 获取业绩预告
print("\n【11】业绩预告")
try:
    forecast = pro.forecast(ts_code=ts_code, start_date='20240101', end_date='20251231')
    if len(forecast) > 0:
        print(forecast)
    else:
        print("无业绩预告数据")
except Exception as e:
    print(f"获取业绩预告失败：{e}")

# 12. 获取分红数据
print("\n【12】分红数据")
try:
    dividend = pro.dividend(ts_code=ts_code, start_date='20200101', end_date='20251231')
    if len(dividend) > 0:
        print(dividend)
    else:
        print("无分红数据")
except Exception as e:
    print(f"获取分红数据失败：{e}")

# 13. 获取管理层信息
print("\n【13】管理层信息")
try:
    managers = pro.stock_manager(ts_code=ts_code)
    if len(managers) > 0:
        print(managers.head(15))
    else:
        print("无管理层数据")
except Exception as e:
    print(f"获取管理层信息失败：{e}")

# 14. 获取机构调研
print("\n【14】机构调研记录")
try:
    visit_rec = pro.visit_record(ts_code=ts_code, start_date='20250101', end_date='20260311')
    if len(visit_rec) > 0:
        print(visit_rec.head(10))
    else:
        print("无调研记录")
except Exception as e:
    print(f"获取调研记录失败：{e}")

print("\n" + "=" * 80)
print("数据收集完成")
print("=" * 80)
