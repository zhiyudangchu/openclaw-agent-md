import tushare as ts

# 核心：替换成你自己的 tushare pro token
pro = ts.pro_api('ff592aa74b18d383dcd07f59f57fce0207e8b8675032f8284245c55e')

# 获取浦发银行600000.SH的1分钟实时数据
try:
    df = pro.rt_min(ts_code='600000.SH,601857.SH,600583.SH', freq='60MIN')
    
    # 打印数据结果
    print("=== 浦发银行1分钟实时数据 ===")
    print(df)

    print("=== 浦发银行实时k线数据 ===")
    cf = pro.rt_k(ts_code='600000.SH,601857.SH,600583.SH')
    print(cf)
    
    # 可选：保存为CSV文件到当前目录
    df.to_csv('spdb_min_data.csv', index=False)
    print("\n数据已保存为 spdb_min_data.csv（当前目录下）")

except Exception as e:
    print(f"\n运行失败：{str(e)}")
    print("\n常见问题：")
    print("1. token错误 → 检查tushare个人中心的接口TOKEN")
    print("2. 积分不足 → rt_min接口需要≥2000积分")
    print("3. 非交易时间 → 仅9:30-11:30/13:00-15:00有数据")
    print("4. 股票代码错误 → 浦发银行是600000.SH（不是60000.SH）")
