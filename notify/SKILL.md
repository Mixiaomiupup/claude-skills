---
name: notify
description: 推送项目进展到飞书（按部门/人员）。从云效拉取迭代工作项，构建卡片消息，按部门定向私信推送。当用户说'推送进展'、'通知后场'、'发给研发'、'notify'、'推送到飞书'、'迭代进展发一下'、'给XX部门发'，或任何涉及将项目状态同步到飞书的操作时使用。
---

# Notify — 项目进展飞书推送

将云效（Yunxiao）项目迭代进展推送到飞书指定部门成员。

## 工作流程

```
1. ToolSearch 加载工具
2. 解析目标（项目+部门，缺什么问什么）
3. 并行拉取：搜项目 + 问部门
4. 拉迭代 → 拉工作项
5. 构建卡片 → 预览确认
6. Python 脚本一次性完成：获取 token → 获取成员 → 去重 → 发送
7. 输出汇总
```

## Step 1: 加载工具

用 ToolSearch 一次性加载所需的云效 MCP 工具：

```
ToolSearch("select:mcp__yunxiao__search_projects,mcp__yunxiao__list_sprints,mcp__yunxiao__search_workitems")
```

## Step 2: 解析推送目标

从用户消息中提取：

| 参数 | 来源 | 默认值 |
|------|------|--------|
| **项目名** | 用户指定或上下文推断 | 必须明确 |
| **迭代** | 用户指定或取最新进行中迭代 | 状态为 DOING 的迭代 |
| **部门** | 用户指定部门名 | 必须明确 |
| **额外人员** | 用户指定的个人 | 无 |

**并行执行**：搜索项目和询问部门可以同时进行（用 AskUserQuestion 问部门的同时调 search_projects）。

如果信息不足，用 AskUserQuestion 询问缺失参数。

### 已知项目别名

云效项目名可能是英文，用户可能说中文。搜索时先用用户原文搜，搜不到则尝试别名：

| 用户说 | 云效项目名 | 项目 ID |
|--------|-----------|---------|
| 跃科 | Yueke_by_Duco | ca70cf018b805f93452bb76d75 |

如果别名表没有匹配，用多个关键词分别搜索（中文名、拼音、英文名）。

## Step 3: 拉取云效数据

```
organizationId: 696f3f56b28d0aba0f5e4371
```

1. **搜索项目**: `mcp__yunxiao__search_projects` (name 过滤)
2. **获取迭代**: `mcp__yunxiao__list_sprints` (status=["DOING"])
3. **获取工作项**: `mcp__yunxiao__search_workitems` (sprint 过滤, category="Req,Task,Bug", perPage=100)

从工作项中提取：编号、标题、类型（需求/任务/缺陷）、状态、负责人、优先级。

## Step 4: 构建飞书卡片并预览

### 状态 & 优先级 emoji 映射

| 状态 | Emoji | 优先级 | Emoji |
|------|-------|--------|-------|
| 开发中 / In Development | 🔵 | 紧急 | 🔴 |
| 设计中 / Designing | 🟢 | 高 | 🟠 |
| 待确认 / New | 🟡 | 中 | 🔵 |
| 待处理 / To Do | ⚪ | 低 | ⚪ |
| 已完成 / Done | ✅ | | |

### 卡片结构

```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": f"📋 {项目名} 迭代进展 - {迭代名}"},
        "template": "blue"
    },
    "elements": [
        # 迭代信息
        {"tag": "div", "text": {"tag": "lark_md", "content": "📅 **周期**: {开始} ~ {结束}　｜　**状态**: {状态}\n\n**迭代目标**: {描述}"}},
        {"tag": "hr"},
        # 工作项表格（lark_md 表格语法）
        {"tag": "div", "text": {"tag": "lark_md", "content": "| 编号 | 类型 | 标题 | 负责人 | 状态 | 优先级 |\n| --- | --- | --- | --- | --- | --- |\n| ...rows... |"}},
        {"tag": "hr"},
        # 进度统计
        {"tag": "div", "text": {"tag": "lark_md", "content": "📊 **完成进度**: {已完成}/{总数}　｜　⏰ **剩余天数**: {天数}天\n\n_由云效项目管理自动同步 · {日期}_"}}
    ]
}
```

### 确认机制

发送前**必须**向用户展示：
1. 卡片内容预览（Markdown 表格）
2. 发送目标（部门名）
3. 等待用户确认后再发送

这是对外可见的操作，不要跳过确认步骤。

## Step 5: 发送（Python 脚本）

用户确认后，用**一个完整的 Python 脚本**完成全部发送流程。

**重要**：不要用 Bash 脚本（macOS 默认 shell 不支持 `declare -A` 等特性），统一用 Python。

### 已知部门速查

| 部门 | department_id |
|------|--------------|
| 后场-研发 | `od-44778258d5c056a8bc746c1c9b92032e` |
| 后场-研发（实习生+顾问） | `od-4d23fdda045eb2310bc154aa672ca2e0` |
| 前场-业务 | `od-d298abfccd172a73eda5f7194bd1812f` |
| 具身语料服务 | `od-32952337c6dd7b4fed51d8220aeb0080` |
| 职能支撑 | `od-d45883aa0889ddf7c7af6c9c3d3a7bc3` |

**常用组合**：
- "后场所有人" = 后场-研发 + 后场-研发（实习生+顾问），自动去重
- "全员" = 所有部门，自动去重

如果用户说的部门名不在表中，用 API `/contact/v3/departments` 动态查找。

### 完整 Python 脚本模板

```python
python3 << 'PYEOF'
import json, time, os, urllib.request
from datetime import date

# ===== 配置区（根据实际数据填充）=====
DEPTS = [
    ("od-xxx", "部门名1"),
    ("od-yyy", "部门名2"),
]
CARD = { ... }  # Step 4 构建的卡片 dict
# ===== 配置区结束 =====

def api_call(method, url, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data, ensure_ascii=False).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. 获取 token
with open(os.path.expanduser("~/.claude.json")) as f:
    config = json.load(f)
args = config["mcpServers"]["lark-mcp"]["args"]
app_id = args[args.index("-a") + 1]
app_secret = args[args.index("-s") + 1]

token = api_call("POST",
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    {"app_id": app_id, "app_secret": app_secret}
)["tenant_access_token"]

card_str = json.dumps(CARD, ensure_ascii=False)

# 2. 遍历部门，获取成员，去重，发送
sent_ids = set()
results = []

for dept_id, dept_name in DEPTS:
    url = f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department?department_id={dept_id}&user_id_type=open_id&department_id_type=open_department_id&page_size=50"
    items = api_call("GET", url, token=token).get("data", {}).get("items", [])

    dept_sent = []
    dept_skipped = []

    for member in items:
        open_id = member.get("open_id", "")
        name = member.get("name", "unknown")

        if open_id in sent_ids:
            dept_skipped.append(name)
            print(f"  ⏭ 跳过(已发送): {name}")
            continue

        body = {"receive_id": open_id, "msg_type": "interactive", "content": card_str}
        try:
            result = api_call("POST",
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                data=body, token=token)
            if result.get("code") == 0:
                print(f"  ✅ {name}")
                sent_ids.add(open_id)
                dept_sent.append(name)
            else:
                print(f"  ❌ {name} (code: {result.get('code')}, msg: {result.get('msg', '')})")
        except Exception as e:
            print(f"  ❌ {name} (error: {e})")

        time.sleep(0.1)

    results.append((dept_name, dept_sent, dept_skipped))
    print(f"[{dept_name}] 发送 {len(dept_sent)} 人: {'、'.join(dept_sent)}")
    if dept_skipped:
        print(f"  去重跳过: {'、'.join(dept_skipped)}")
    print("---")

# 3. 汇总
print("\n========== 发送汇总 ==========")
total = sum(len(r[1]) for r in results)
for dept_name, sent, skipped in results:
    skip_info = f"（去重 {len(skipped)} 人）" if skipped else ""
    print(f"| {dept_name} | {len(sent)} | {'、'.join(sent)} | {skip_info}")
print(f"\n共 {total} 人，✅ {total} 成功")
PYEOF
```

## Step 6: 输出汇总

脚本执行后，整理输出为 Markdown 表格：

```
| 部门 | 人数 | 成员 |
|------|------|------|
| 后场-研发 | 7 | 谢娟、章林骏、... |
| 后场-研发（实习生+顾问） | 6 | 陈一帆、... |（去重 3 人）

共 N 人，✅ M 成功，❌ K 失败
```

## 常见用法

```
/notify                          → 询问项目和部门
推送跃科进展给后场               → 自动识别项目别名+部门组合
迭代进展发给后场-研发             → 需确认项目
通知后场所有人                    → 后场-研发 + 后场-研发（实习生+顾问），自动去重
```
