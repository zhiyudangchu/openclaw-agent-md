import pandas as pd
from datetime import datetime

# 读取实时数据
data_path = '/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt'

# 跳过前 3 行元数据，读取 CSV 数据
with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    metadata = lines[:3]
    csv_data = ''.join(lines[4:])  # 跳过前 3 行元数据和第 4 行空行

import io
df = pd.read_csv(io.StringIO(csv_data), sep='|')

# 计算涨跌幅
df['pct_change'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)

print("=== 实时数据（含涨跌幅）===")
print(df[['ts_code', 'name', 'close', 'pre_close', 'pct_change']].to_string(index=False))

# 预警规则（根据 alert-rules.md，当前状态：已关闭）
# 规则已注释，不触发任何预警
alert_rules_active = False

# 如果规则开启，应用以下逻辑：
# 通用规则：
# - 下跌 > 1% → 触发
# - 上涨 > 1% → 触发
# 个股专属规则：
# 1. 中国石油 (601857.SH):
#    🟢 涨幅 > 2% → 触发预警
#    🔴 跌幅 > 1% → 触发预警

if not alert_rules_active:
    print("\n⚠️  预警规则状态：已关闭")
    print("无满足条件的预警数据")
    alert_df = pd.DataFrame()
else:
    # 应用预警规则
    alert_conditions = []
    
    # 通用规则
    alert_conditions.append((df['pct_change'] > 1) | (df['pct_change'] < -1))
    
    # 个股专属规则 - 中国石油
    cnpc_mask = df['ts_code'] == '601857.SH'
    cnpc_alert = ((df['pct_change'] > 2) | (df['pct_change'] < -1)) & cnpc_mask
    
    alert_mask = (df['pct_change'] > 1) | (df['pct_change'] < -1)
    alert_df = df[alert_mask]

print(f"\n满足预警条件的记录数：{len(alert_df)}")

# 保存过滤结果
if len(alert_df) > 0:
    alert_df.to_csv('/home/openclaw/.openclaw/workspace-main-stock/stock/alert-data.txt', sep='|', index=False)
    print("预警数据已保存")
else:
    # 创建空文件标记
    with open('/home/openclaw/.openclaw/workspace-main-stock/stock/alert-data.txt', 'w', encoding='utf-8') as f:
        f.write("无预警数据\n")
    print("无预警数据，任务结束")
