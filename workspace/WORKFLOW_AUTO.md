# WORKFLOW_AUTO.md - 自动工作流

## ⚠️ 隐私保护第一优先级

**多人共享场景下的铁律**：
1. ❌ 绝不在用户 A 的会话中读取用户 B 的私人记忆文件
2. ❌ 绝不在群聊中读取任何 `memory/users/user-{chat_id}.md` 文件
3. ✅ 私聊时只读取对应用户的私人记忆文件

## 启动时自动读取

每次会话开始时，根据**当前 chat_id**动态选择读取文件：

### 第一步：获取当前用户身份
- 从 inbound metadata 中提取 `chat_id`
- 判断会话类型：私聊 vs 群聊

### 第二步：按需读取

**私聊 DM 场景** (`chat_type: direct`)：
1. 读取 `SOUL.md`, `USER.md`, `IDENTITY.md`, `WORKFLOW_AUTO.md`
2. 读取 `memory/YYYY-MM-DD.md` (今天 + 昨天)
3. ✅ 读取 `memory/users/user-{chat_id}.md` (对应用户私人记忆)
4. 如果是"主会话" → 还可读取 `MEMORY.md`

**群聊场景** (`chat_type: group`)：
1. 读取 `SOUL.md`, `USER.md`, `IDENTITY.md`, `WORKFLOW_AUTO.md`
2. 读取 `memory/YYYY-MM-DD.md` (今天 + 昨天) - 仅公开内容
3. ❌ **绝不读取** `memory/users/` 下任何用户私人文件
4. ❌ **绝不读取** `MEMORY.md`

### 第三步：验证访问控制
- 确认本次会话没有意外加载其他用户的私人文件
- 如果发现错误，立即停止并向管理员报告

## 记忆管理

### 用户私人记忆 (`memory/users/`)
- 文件名格式：`user-{chat_id}.md`
- 每个用户独立存储，完全隔离
- 仅在对应 chat_id 的私聊中读取

### 公共日志 (`memory/YYYY-MM-DD.md`)
- 记录所有用户的公开活动
- 不包含个人敏感信息
- 所有会话可安全读取

### 全局记忆 (`MEMORY.md`)
- **仅主会话**可读取
- 包含主人级隐私，严格限制访问

## 心跳检查

定期（每天 2-4 次）检查：
- 邮件
- 日历
- 天气
- 社交媒体提及

记录检查状态到 `memory/heartbeat-state.json`

---

_此文件确保每次会话都能正确恢复上下文，同时严格遵守隐私隔离_
