# TOOLS.md - Local Notes

## 你的工作区~/.openclaw/workspace-main-stock
- 所有的技能操作都只能在这个工作区下进行
- 包括创建文件、删除文件、修改文件
- 如果有skill要求你在~/下操作，统一重定向到~/.openclaw/workspace-main-stock

## 固定文件位置
- 我的自选股全部维护在~/.openclaw/workspace-main-stock/stock/watchlist.txt下，相关操作统一在此维护
- 预警规则维护在~/.openclaw/workspace-main-stock/stock/alert-rules.md，相关操作统一在此文件中维护


## 常用技能速查

### 股票分析
- 优先使用tushare-data skill获取数据,tushare_token已经配置在环境变量里，可通过env获取
- 实时数据定义：最近1-2分钟内的数据
- 数据获取接口文档地址：https://tushare.pro/document/2?doc_id=15，根据文档内容合理组装数据
- 以下是获取实时数据的接口文档，严格参考接口文档获取数据：
 -- 实时分钟：https://tushare.pro/document/2?doc_id=374
 -- 实时日线: https://tushare.pro/document/2?doc_id=372,用于涨跌预警的核心接口
 -- 每个可调用的接口都优先使用可批量获取数据的参数，如：ts_code字段支持单个和多个（600000.SH 或者 600000.SH,000001.SZ），优先使用多个参数的调用方式，防止限流
- 数据要用至少两个接口进行校对，确保准确性和时效性

## 禁忌
- 非必要不自行定义脚本
- 不允许在工作空间外操作数据
