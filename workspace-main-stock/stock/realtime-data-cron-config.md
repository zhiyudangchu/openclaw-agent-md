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

- 1、使用tushare-data技能，获取数据判断今日是否收盘或休市，未收盘或休市，则进行下一步；否则，结束本次任务；
- 2、如果realtime-data.txt里的内容不为空，则清空后进行下一步；否则直接进行下一步；
- 3、使用tushare-data技能，按照get-data-template.md内的格式要求获取自选股的**实时**日线数据，注意这里是**实时日线**，不要从历史日线获取数据，保存在realtime-data.txt里；
   - 实时日线的接口是：rt_k
- 4、按照alert-rules.md中的预警规则和以下条件过滤获取到的实时数据：
   - 满足预警规则中任意一条条件；
   - 只返回满足预警规则的数据；
- 5、如果存在满足条件的数据，则进行下一步；否则，结束本次任务。
- 6、读取**receiver-list.txt**接受者用户列表文件，使用命令```openclaw message broadcast --channel feishu --account stock --targets <user_id1> --targets <user_id2>... --message <xxx>```，将预警数据通过飞书(feishu)渠道推送给列表文件中的用户；
   - --targets <user_id> 参数可重复
- 7、推送数据格式严格按照alert-template.md的内容要求。


### 任务监控
- 1、记录任务执行过程中，调用的所有接口，包括接口出入参；
- 2、记录任务执行过程中，发生的任何错误；
- 3、将记录的数据发送到群聊```oc_e5021f4489531f598034cdfc2e0394f6```中，并@测试机器人，使用命令如下：
   - ```openclaw message send --channel feishu --account stock --target oc_e5021f4489531f598034cdfc2e0394f6 --message <xxx>```
