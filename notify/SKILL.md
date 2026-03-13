---
name: notify
description: 推送项目进展到飞书（按部门/人员）。从云效拉取迭代工作项，构建卡片消息，按部门定向私信推送。当用户说'推送进展'、'通知后场'、'发给研发'、'notify'、'推送到飞书'、'迭代进展发一下'、'给XX部门发'，或任何涉及将项目状态同步到飞书的操作时使用。
---

# Notify — 项目进展飞书推送

将云效（Yunxiao）项目迭代进展推送到飞书指定部门成员。

## 工作流程

```
解析目标 → 拉取云效数据 → 构建卡片 → 获取部门成员 → 逐人私信（去重）
```

## Step 1: 解析推送目标

从用户消息中提取：

| 参数 | 来源 | 默认值 |
|------|------|--------|
| **项目名** | 用户指定或上下文推断 | 必须明确 |
| **迭代** | 用户指定或取最新进行中迭代 | 状态为 DOING 的迭代 |
| **部门** | 用户指定部门名 | 必须明确 |
| **额外人员** | 用户指定的个人 | 无 |

如果信息不足，用 AskUserQuestion 询问缺失参数。

## Step 2: 拉取云效数据

使用云效 MCP 工具（需先 ToolSearch 加载）：

```
organizationId: 696f3f56b28d0aba0f5e4371
```

1. **搜索项目**: `mcp__yunxiao__search_projects` (name 过滤)
2. **获取迭代**: `mcp__yunxiao__list_sprints` (取 status=DOING 的迭代)
3. **获取工作项**: `mcp__yunxiao__search_workitems` (sprint 过滤, category="Req,Task,Bug")

从工作项中提取：标题、类型（需求/任务/缺陷）、状态、负责人、优先级、计划时间。

## Step 3: 构建飞书卡片

用 `interactive` 类型消息（卡片），模板结构：

```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "📋 {项目名} 迭代进展 - {迭代名}"},
        "template": "blue"
    },
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📅 **周期**: {开始} ~ {结束}　｜　**状态**: {状态}\n\n**迭代目标**: {描述}"
            }
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "{工作项表格 - lark_md格式}"
            }
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📊 **完成进度**: {已完成}/{总数}　｜　⏰ **剩余天数**: {天数}天\n\n_由云效项目管理自动同步 · {日期}_"
            }
        }
    ]
}
```

**工作项表格**用 lark_md 表格语法，包含状态 emoji 映射：

| 状态 | Emoji |
|------|-------|
| 开发中 / In Development | 🔵 |
| 设计中 / Designing | 🟢 |
| 待确认 / New | 🟡 |
| 待处理 / To Do | ⚪ |
| 已完成 / Done | ✅ |

优先级 emoji：紧急 🔴、高 🟠、中 🔵、低 ⚪

## Step 4: 获取部门成员并发送

MCP 没有"列出部门成员"工具，必须用 curl 完成整个发送流程。

### 已知部门速查

| 部门 | department_id |
|------|--------------|
| 后场-研发 | `od-44778258d5c056a8bc746c1c9b92032e` |
| 后场-研发（实习生+顾问） | `od-4d23fdda045eb2310bc154aa672ca2e0` |
| 前场-业务 | `od-d298abfccd172a73eda5f7194bd1812f` |
| 具身语料服务 | `od-32952337c6dd7b4fed51d8220aeb0080` |
| 职能支撑 | `od-d45883aa0889ddf7c7af6c9c3d3a7bc3` |

如果用户说的部门名不在表中，用 curl 调 `/contact/v3/scopes` + `/contact/v3/departments/{id}` 动态查找。

### 发送脚本模板

用一个 Bash 脚本完成 token获取 → 部门成员获取 → 去重 → 逐人发送：

```bash
# 1. 获取 token（从 ~/.claude.json 读取 app credentials）
APP_ID=$(python3 -c "import json; c=json.load(open('$HOME/.claude.json')); args=c['mcpServers']['lark-mcp']['args']; print(args[args.index('-a')+1])")
APP_SECRET=$(python3 -c "import json; c=json.load(open('$HOME/.claude.json')); args=c['mcpServers']['lark-mcp']['args']; print(args[args.index('-s')+1])")
TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# 2. 获取部门成员
MEMBERS=$(curl -s "https://open.feishu.cn/open-apis/contact/v3/users/find_by_department?department_id=$DEPT_ID&user_id_type=open_id&department_id_type=open_department_id&page_size=50" \
  -H "Authorization: Bearer $TOKEN")

# 3. 逐人发送（用 python 构建 JSON body，curl 发送）
# receive_id_type=open_id, msg_type=interactive, content=card JSON
# sleep 0.1 限流
```

### 多部门去重

发送多个部门时，用 set/array 记录已发送的 open_id，跨部门跳过重复。先发第一个部门全部成员，后续部门只发新增成员。

## Step 5: 报告结果

发送完毕后，输出汇总表：

```
| 部门 | 人数 | 成员 |
|------|------|------|
| 后场-研发 | 7 | 谢娟、章林骏、... |
| 后场-研发（实习生+顾问） | 6（去重后） | 陈一帆、... |

共 N 人，✅ M 成功，❌ K 失败
```

## 确认机制

发送前**必须**向用户展示：
1. 卡片内容预览（工作项表格）
2. 发送目标（部门名 + 人数）
3. 等待用户确认后再发送

这是对外可见的操作，不要跳过确认步骤。

## 常见用法

```
/notify                          → 询问项目和部门
推送 Yueke_by_Duco 进展给后场    → 自动识别项目+部门
迭代进展发给后场-研发             → 需确认项目
通知后场所有人                    → 后场-研发 + 后场-研发（实习生+顾问），自动去重
```
