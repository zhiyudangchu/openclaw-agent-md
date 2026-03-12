# TOOLS.md - Local Notes

## 注意事项
- 工作区：~/.openclaw/workspace-main-stock
- 所有的技能操作都只能在这个工作区下进行
- 包括创建文件、删除文件、修改文件
- 如果有skill要求你在~/下操作，统一重定向到~/.openclaw/workspace-main-stock

## 固定文件位置
- 自选股全部维护在~/.openclaw/workspace-main-stock/stock/stock-list.txt中
- 预警规则维护在~/.openclaw/workspace-main-stock/stock/alert-rules.md中
- 相关维护操作统一在上述文件中进行


## 常用技能速查

### 股票分析
- 优先使用tushare-data 技能获取数据,tushare_token已经配置在环境变量里，可通过env获取
- 实时数据定义：最近1分钟的数据
- 数据获取接口文档路径再tushare-data技能包下的references文件夹内，根据文档内容合理组装数据
- 重点关注**references/股票数据/行情数据**下的接口文档，其中包含股票相关的实时数据获取接口，每个文档都需要仔细学习
  - 如：实时日线: 用于涨跌预警的核心接口，对应的接口为：rt_k
  - 每个可调用的接口都优先使用可批量获取数据的参数，如：ts_code字段支持单个和多个（600000.SH 或者 600000.SH,000001.SZ），优先使用多个参数的调用方式，防止限流
- 数据要用至少两个接口进行校对，确保准确性和时效性

## 禁忌
- 非必要不自行定义脚本
- 不允许在工作空间外操作数据
