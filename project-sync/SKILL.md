---
name: project-sync
description: 同步云效（Yunxiao）项目迭代进展到飞书多维表格（Bitable）。当用户说"同步进展"、"同步云效到飞书"、"更新项目管理表"、"拉取迭代进展"、"同步到飞书表格"、"项目进展同步"，或任何涉及从云效拉取工作项并写入飞书多维表格的操作时使用。注意与 notify skill 的区别：notify 是推送卡片消息到飞书聊天，project-sync 是写入飞书多维表格做持久化项目管理。
---

# Project Sync — 云效 → 飞书多维表格同步

将云效项目迭代中的工作项同步到飞书知识库中的多维表格，实现项目进展的持久化跟踪。

## 工作流程

```
1. ToolSearch 加载工具
2. 解析目标（项目 + 飞书文档位置）
3. 拉取云效数据（迭代 + 工作项）
4. 定位飞书多维表格（获取 bitable 结构）
5. 用户映射（云效用户名 → 飞书 open_id）
6. 构建记录 → 预览确认
7. 批量写入飞书多维表格
8. 输出汇总
```

## Step 1: 加载工具

用 ToolSearch 一次性加载所需工具：

```
ToolSearch("select:mcp__yunxiao__search_projects,mcp__yunxiao__list_sprints,mcp__yunxiao__search_workitems")
ToolSearch("select:mcp__lark-mcp__wiki_v2_spaceNode_list,mcp__lark-mcp__docx_v1_document_rawContent,mcp__lark-mcp__bitable_v1_appTable_list,mcp__lark-mcp__bitable_v1_appTableField_list,mcp__lark-mcp__bitable_v1_appTableRecord_search,mcp__lark-mcp__bitable_v1_appTableRecord_batchCreate,mcp__lark-mcp__bitable_v1_appTableRecord_batchUpdate")
```

## Step 2: 解析同步目标

从用户消息中提取：

| 参数 | 来源 | 默认值 |
|------|------|--------|
| **项目名** | 用户指定或上下文推断 | 必须明确 |
| **迭代** | 用户指定或取最新进行中迭代 | 状态为 DOING 的迭代 |
| **时间范围** | 用户指定（如"上周"）| 当前迭代全部工作项 |
| **飞书文档位置** | 用户指定或自动查找 | 按项目别名在 wiki 中搜索 |
| **同步模式** | 追加 / 全量覆盖 | 追加（新增不存在的记录） |

如果信息不足，用 AskUserQuestion 询问缺失参数。

### 已知项目别名

| 用户说 | 云效项目名 | 项目 ID | 飞书 wiki 位置 |
|--------|-----------|---------|----------------|
| 跃科 | Yueke_by_Duco | ca70cf018b805f93452bb76d75 | 联创项目 > 扁线电机柔性插装项目 > 项目排期 > 待办事项 |

搜索时先用用户原文搜，搜不到则尝试别名（中文名、拼音、英文名）。

### 云效组织 ID

```
organizationId: 696f3f56b28d0aba0f5e4371
```

## Step 3: 拉取云效数据

### 3.1 搜索项目（如未命中别名表）

```
mcp__yunxiao__search_projects
  organizationId: "696f3f56b28d0aba0f5e4371"
  name: "<项目名关键词>"
```

### 3.2 获取迭代

```
mcp__yunxiao__list_sprints
  organizationId: "696f3f56b28d0aba0f5e4371"
  id: "<项目ID>"
  status: ["DOING"]
```

如果用户指定了迭代名，用 name 匹配；否则取最新 DOING 状态的迭代。

### 3.3 获取工作项

```
mcp__yunxiao__search_workitems
  organizationId: "696f3f56b28d0aba0f5e4371"
  category: "Req,Task,Bug"
  spaceId: "<项目ID>"
  sprint: "<迭代ID>"
  perPage: 100
```

如果用户指定了时间范围（如"上周"），可用 `updatedAfter` / `updatedBefore` 过滤。

从工作项中提取：编号(serialNumber)、标题(subject)、类型(categoryId)、状态(status)、负责人(assignedTo)、优先级、计划开始/完成时间、标签(labels)。

## Step 4: 定位飞书多维表格

### 4.1 查找目标 bitable

如果项目在别名表中有飞书 wiki 位置，直接按路径查找。否则：

1. 列出产品研发知识库顶级节点：
   ```
   mcp__lark-mcp__wiki_v2_spaceNode_list
     path: { space_id: "7559794508562251778" }
     params: { page_size: 50 }
   ```

2. 逐层展开，查找包含项目名的节点

3. 在项目节点下查找 `obj_type: "bitable"` 的子节点

### 4.2 获取 bitable 结构

```
mcp__lark-mcp__bitable_v1_appTable_list
  path: { app_token: "<bitable的obj_token>" }

mcp__lark-mcp__bitable_v1_appTableField_list
  path: { app_token: "<app_token>", table_id: "<table_id>" }
```

### 4.3 读取现有记录（去重用）

```
mcp__lark-mcp__bitable_v1_appTableRecord_search
  path: { app_token: "<app_token>", table_id: "<table_id>" }
  data: { automatic_fields: true }
  params: { page_size: 500 }
```

对比云效工作项编号与现有记录标题中的编号，判断哪些是新增、哪些需要更新。

## Step 5: 用户映射

将云效用户名映射到飞书 open_id。映射来源有两个：

### 5.1 从现有 bitable 记录提取已知映射

遍历现有记录中的"执行人"字段，建立 `{中文名: open_id}` 映射表。

### 5.2 从飞书部门 API 补充未知用户

对于现有记录中没有的用户，通过部门成员 API 查找：

```python
import json, os, urllib.request

with open(os.path.expanduser('~/.claude.json')) as f:
    config = json.load(f)
args = config['mcpServers']['lark-mcp']['args']
app_id = args[args.index('-a') + 1]
app_secret = args[args.index('-s') + 1]

# 获取 token
req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    data=json.dumps({'app_id': app_id, 'app_secret': app_secret}).encode(),
    headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())['tenant_access_token']

# 查询部门成员
for dept_id in DEPT_IDS:
    req = urllib.request.Request(
        f'https://open.feishu.cn/open-apis/contact/v3/users/find_by_department'
        f'?department_id={dept_id}&user_id_type=open_id'
        f'&department_id_type=open_department_id&page_size=50',
        headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read()).get('data', {}).get('items', [])
        for u in items:
            print(f"{u.get('name', '')} -> {u.get('open_id', '')}")
```

### 已知部门

| 部门 | department_id |
|------|--------------|
| 后场-研发 | `od-44778258d5c056a8bc746c1c9b92032e` |
| 后场-研发（实习生+顾问） | `od-4d23fdda045eb2310bc154aa672ca2e0` |

### 云效用户名 → 飞书用户名映射

云效中用户名可能是英文（如 "Yifan Chen"），飞书中是中文（如 "陈一帆"）。已知映射：

| 云效用户名 | 飞书用户名 | open_id |
|-----------|-----------|---------|
| zhanglinjun / ZhangLinJun | 章林骏 | ou_b52e4a0810c94e0518aac5f479d1212e |
| xiejuan | 谢娟 | ou_87a0017dd3d4690f3e6f363383c14c01 |
| chenweiai | 陈未艾 | ou_98df8326dfeb0a93ce27f24df3b7c3c7 |
| Yifan Chen | 陈一帆 | ou_7e277ff6d5baafe29475c1e9f81e2dca |
| shenyijie | 沈懿杰 | ou_2a6d1033cdd03a9d1c3877c1e74f12af |
| 方经义 | 方经义 | ou_358678b770a2ded96cc1a4768e44b6b5 |
| 徐弋洋 | 徐弋洋 | ou_ac05d594de135410c7eddf649a728995 |
| 查志强 | 查志强 | ou_3bde9414b22bc7794cbe166754995212 |
| 米冠飞 | 米冠飞 | ou_1492796b64e0b6929b16ef173e89b29a |
| 邓子晗 | 邓子晗 | ou_985c74abf3882afeb657364a2dbeb863 |
| 徐丁宁 | 徐丁宁 | ou_f173b31c98abda2234bcd5f96eef4fce |
| 郭艾咏 | 郭艾咏 | ou_f8c45bf3ed36232782049bf7dc6086dc |
| 王奕晨 | 王奕晨 | ou_6fb6f14f6eeb4cf5f039864375531109 |

遇到不在映射表中的用户时，先查部门 API，仍找不到则该记录的执行人字段留空。

## Step 6: 字段映射与记录构建

### 优先级映射

| 云效优先级 | 飞书选项 |
|-----------|---------|
| 紧急 | 🔴P0-高优 |
| 高 | 🔴P0-高优 |
| 中 | 🟡P1-一般 |
| 低 | 🟢P2-低优 |

### 状态映射（写入"每日进展"字段）

| 云效状态 | 文本 |
|---------|------|
| 待处理 / To Do | 状态：待处理 |
| 待确认 / New | 状态：待确认 |
| 设计中 / Designing | 状态：设计中 |
| 开发中 / In Development | 状态：开发中 |
| 已完成 / Done | 状态：已完成 |

### 标准字段映射

这是基于跃科项目 bitable 的字段结构。不同项目的 bitable 字段可能不同，需根据 Step 4.2 获取的实际字段动态适配。

| Bitable 字段 | 类型 | 云效数据来源 | 格式说明 |
|-------------|------|------------|---------|
| 待办事项 | Text | `[{serialNumber}] {subject}` | 主键文本，含编号便于去重 |
| 优先级 | SingleSelect | priority → 映射表 | 选项值必须精确匹配 |
| 创建时间 | DateTime | 计划开始时间（毫秒时间戳） | 无计划时间则不填 |
| 截止日期 | DateTime | 计划完成时间（毫秒时间戳） | 无计划时间则不填 |
| 执行人 | User | assignedTo → open_id 映射 | `[{"id": "ou_xxx"}]` |
| 是否已完成 | Checkbox | status 是否为完成态 | true/false |
| 每日进展 | Text | 状态映射文本 | 简要状态说明 |
| 验收标准 | Text | description（如有） | 可选 |

### 动态字段适配

如果目标 bitable 的字段名与上述不同，按以下策略匹配：
- 包含"事项"/"标题"/"任务"的字段 → 写入标题
- 包含"优先"的字段 → 写入优先级
- 包含"截止"/"deadline"的字段 → 写入截止日期
- 包含"执行"/"负责"/"assignee"的字段 → 写入执行人
- 包含"完成"/"done"的字段 → 写入完成状态
- 包含"进展"/"进度"/"progress"的字段 → 写入状态

### 构建记录示例

```python
records = []
for item in workitems:
    fields = {
        "待办事项": f"[{item['serialNumber']}] {item['subject']}",
        "优先级": priority_map.get(item_priority, "🟡P1-一般"),
        "是否已完成": item['status']['nameEn'] == 'Done',
        "每日进展": f"状态：{item['status']['displayName']}",
    }
    # 可选字段
    if plan_start:
        fields["创建时间"] = plan_start_timestamp
    if plan_end:
        fields["截止日期"] = plan_end_timestamp
    if open_id := user_map.get(item['assignedTo']['name']):
        fields["执行人"] = [{"id": open_id}]
    records.append({"fields": fields})
```

## Step 7: 预览确认与写入

### 7.1 预览

发送前**必须**向用户展示：

1. 待同步的工作项汇总表（Markdown 表格）
2. 目标飞书文档位置
3. 同步模式（新增 N 条 / 更新 M 条）
4. 未能映射的用户（如有）

这是对飞书数据的修改操作，不要跳过确认步骤。

### 7.2 写入

用户确认后，批量写入：

**新增记录：**
```
mcp__lark-mcp__bitable_v1_appTableRecord_batchCreate
  path: { app_token: "<app_token>", table_id: "<table_id>" }
  params: { user_id_type: "open_id" }
  data: { records: [...] }
```

**更新已有记录：**
```
mcp__lark-mcp__bitable_v1_appTableRecord_batchUpdate
  path: { app_token: "<app_token>", table_id: "<table_id>" }
  params: { user_id_type: "open_id" }
  data: { records: [{ record_id: "recXXX", fields: {...} }, ...] }
```

## Step 8: 输出汇总

```markdown
同步完成：
- 项目：跃科 (Yueke_by_Duco)
- 迭代：version 0.0.1 (3/6 - 4/7)
- 新增：7 条记录
- 更新：0 条记录
- 跳过：0 条（已存在且无变化）
- 未映射用户：无

文档位置：产品研发知识库 > 联创项目 > ... > 待办事项
```

## 已知 Bitable 速查

| 项目 | app_token | table_id | 表名 |
|------|-----------|----------|------|
| 跃科项目排期 | BYOJbxBxVauHeIs6FnvcVOgnntg | tbl47B6j6iuZ6GiG | Todo跟进 |

## 常见用法

```
同步云效跃科项目到飞书       → 自动识别项目+查找飞书表格+全量同步
同步上周跃科进展到飞书       → 按时间过滤+同步到已知表格
把云效迭代工作项更新到飞书表  → 同上
项目进展同步                → 询问项目名
```

## 与其他 skill 的关系

| Skill | 用途 | 区别 |
|-------|------|------|
| **project-sync**（本 skill） | 写入飞书多维表格，持久化跟踪 | 结构化数据，可查询可统计 |
| **notify** | 推送卡片消息到飞书聊天 | 一次性通知，按部门定向推送 |
| **feishu** | 飞书 MCP 通用参考 | 工具手册，非工作流 |

典型组合：先用 project-sync 同步表格，再用 notify 通知相关人员。
