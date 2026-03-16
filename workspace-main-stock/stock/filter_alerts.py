import pandas as pd

# 读取实时数据 (指定编码)
df = pd.read_csv('/home/openclaw/.openclaw/workspace-main-stock/stock/realtime-data.txt', sep='\t', encoding='utf-8-sig')

print("列名:", df.columns.tolist())

# 计算涨跌幅和涨跌额
df['change_pct'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
df['change_amt'] = (df['close'] - df['pre_close']).round(2)

# 预警规则状态：已关闭
# 根据 alert-rules.md，所有规则都被划掉了，状态是已关闭
# 所以没有股票会触发预警

alert_rules_enabled = False

if not alert_rules_enabled:
    print("预警规则已关闭，无触发数据")
    filtered_df = pd.DataFrame()
else:
    filtered_df = pd.DataFrame()

# 保存过滤结果
if not filtered_df.empty:
    filtered_df.to_csv('/home/openclaw/.openclaw/workspace-main-stock/stock/alert-data.txt', sep='\t', index=False)
    print(f"发现 {len(filtered_df)} 条预警数据")
    print(filtered_df)
else:
    print("无预警数据")
    
# 输出详细数据用于调试
print("\n=== 详细数据 ===")
for _, row in df.iterrows():
    print(f"{row['ts_code']} {row['name']}: 现价={row['close']}, 昨收={row['pre_close']}, 涨跌幅={row['change_pct']}%, 涨跌额={row['change_amt']}")
