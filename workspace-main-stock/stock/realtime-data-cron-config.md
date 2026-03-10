## 实时数据获取操作

**重要提示**
- 你的工作路径：~/.openclaw/workspace-main-stock
- 自定义文件存放路径：~/.openclaw/workspace-main-stock/stock
- 你独享的skill存放路径：~/.openclaw/workspace-main-stock/skills
- 以下描述中没有具体路径的文件都是自定义文件，存放在自定义路径下，如'realtime-data.txt'实际路径为：~/.openclaw/workspace-main-stock/stock/realtime-data.txt；
- 指定了具体路径的文件，按照指定路径读取，如：~/.openclaw/workspace-main-stock/TOOLS.md；
- 如果你需要新建文件，统一存放在自定义路径下；
- 如果存在可用脚本，优先复用，不满足当前场景时才允许创建新脚本。
- 执行到不存在的文件时，请严格检查是否时按照上述要求执行的。

### 操作流程

1、使用tushare-data skill，获取数据判断今日是否收盘或休市，未收盘或休市，则进行下一步；否则，结束本次任务；
2、如果realtime-data.txt里的内容不为空，则清空后进行下一步；否则直接进行下一步；
3、阅读~/.openclaw/workspace-main-stock/TOOLS.md内的skill使用说明，严格按照要求使用skill；
4、使用tushare-data skill，按照get-data-template.md内的格式要求获取自选股的实时日线数据，保存在realtime-data.txt里；
5、按照alert-rules.md中的预警规则和以下条件过滤获取到的实时数据：
   - 满足预警规则中任意一条条件；
   - 只返回满足预警规则的数据；
6、如果存在满足条件的数据，则进行下一步；否则，结束本次任务。
7、读取receiver-list.txt接受者用户列表文件，使用命令openclaw message broadcast --channel feishu --account stock --targets <user_id1> --targets <user_id2>... --message <xxx>，
   将预警数据通过飞书(feishu)渠道推送给列表文件中的用户；
   - --targets <user_id> 参数可重复
8、推送数据格式严格按照alert-template.md的内容要求。
