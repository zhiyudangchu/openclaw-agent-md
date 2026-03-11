import os
import tushare as ts
import pandas as pd
from datetime import datetime

# 读取环境变量中的 token
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口实例
pro = ts.pro_api(token)

# 神火股份股票代码
ts_code = '000933.SZ'

print("=" * 60)
print("神火股份 (000933.SZ) - 基本面数据收集")
print("=" * 60)

# 1. 获取股票基本信息
print("\n【1】股票基本信息")
stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,area,industry,market,list_date')
print(stock_info)

# 2. 获取公司基本信息
print("\n【2】公司基本信息")
try:
    company_info = pro.stock_company(ts_code=ts_code, fields='ts_code,chairman,manager,website,employee_total,introduction')
    print(company_info)
except Exception as e:
    print(f"获取公司信息失败：{e}")

# 3. 获取最新财务指标
print("\n【3】最新财务指标")
try:
    # 获取最近4个季度的财务指标
    indicators = pro.fina_indicator(ts_code=ts_code, fields='ts_code,ann_date,roe,roa,grossprofit_margin,net_profit_margin,debt_to_assets,current_ratio,quick_ratio,eps,dpsps,operate_cash_flow_ps')
    indicators = indicators.sort_values('ann_date', ascending=False).head(8)
    print(indicators)
except Exception as e:
    print(f"获取财务指标失败：{e}")

# 4. 获取利润表主要数据
print("\n【4】利润表主要数据")
try:
    income = pro.income(ts_code=ts_code, fields='ts_code,ann_date,total_revenue,operating_profit,net_profit', start_date='20220101', end_date='20251231')
    income = income.sort_values('ann_date', ascending=False)
    print(income)
except Exception as e:
    print(f"获取利润表失败：{e}")

# 5. 获取资产负债表主要数据
print("\n【5】资产负债表主要数据")
try:
    balance = pro.balancesheet(ts_code=ts_code, fields='ts_code,ann_date,total_assets,total_liab,total_hldr_eqy_inc_min_int', start_date='20220101', end_date='20251231')
    balance = balance.sort_values('ann_date', ascending=False)
    print(balance)
except Exception as e:
    print(f"获取资产负债表失败：{e}")

# 6. 获取现金流量表主要数据
print("\n【6】现金流量表主要数据")
try:
    cashflow = pro.cashflow(ts_code=ts_code, fields='ts_code,ann_date,operate_cash_flow,invest_cash_flow,finance_cash_flow', start_date='20220101', end_date='20251231')
    cashflow = cashflow.sort_values('ann_date', ascending=False)
    print(cashflow)
except Exception as e:
    print(f"获取现金流量表失败：{e}")

# 7. 获取前十大股东
print("\n【7】前十大股东")
try:
    top10_holders = pro.top10_holders(ts_code=ts_code, ann_date='20241231')
    print(top10_holders)
except Exception as e:
    print(f"获取股东数据失败：{e}")

# 8. 获取行业板块信息
print("\n【8】所属板块")
try:
    # 获取概念板块
    concept_data = pro.concept_detail(ts_code=ts_code)
    print(concept_data)
except Exception as e:
    print(f"获取板块数据失败：{e}")

# 9. 获取煤炭行业指数
print("\n【9】煤炭行业相关数据")
try:
    # 获取申万煤炭行业指数
    coal_index = pro.index_daily(ts_code='801180.SI', start_date='20240101', end_date='20260310')
    if len(coal_index) > 0:
        print(f"煤炭行业指数最新数据：")
        print(coal_index.tail())
except Exception as e:
    print(f"获取行业指数失败：{e}")

# 10. 获取管理层信息
print("\n【10】管理层信息")
try:
    managers = pro.stock_manager(ts_code=ts_code)
    if len(managers) > 0:
        print(managers.head(10))
except Exception as e:
    print(f"获取管理层信息失败：{e}")

print("\n" + "=" * 60)
print("数据收集完成")
print("=" * 60)
