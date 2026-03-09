---
name: feishu
description: Use when accessing Feishu/Lark resources via MCP - wiki knowledge base, documents, chats, bitable. Also use when Lark MCP token errors occur (99991663, "invalid access token", "user access token is not configured").
---

# Lark MCP

Feishu/Lark MCP integration reference. Covers tool inventory (168 tools), wiki knowledge base structure, verified capabilities, publishing workflows, and troubleshooting.

## Config

**Location**: `~/.claude.json` > `mcpServers` > `lark-mcp`

**Required args**: `-a <app_id> -s <app_secret> --token-mode tenant_access_token`

`--token-mode` must be explicitly set. Default `auto` causes wiki/doc APIs to fail when no user session exists.

**Enable all tools**: add `-t "all"` to args (overrides defaults, enables all 168 tools).

**Enable specific presets**: add `-t "preset.im.default,preset.wiki.all,preset.docx.all,preset.bitable.all,preset.drive.all,preset.sheets.all"` to args.

## Token Types

| Token | How to Get | Scope |
|-------|-----------|-------|
| **tenant_access_token** | Auto-generated from app_id + app_secret | Bot-accessible resources |
| **user_access_token** | `npx -y @larksuiteoapi/lark-mcp login -a <id> -s <secret>` | User-scoped resources |

## Tool Inventory (168 tools)

### 分类总览

| 领域 | 数量 | 覆盖范围 | 关键工具前缀 |
|------|------|---------|-------------|
| **IM (消息)** | 5 | 群聊管理、发消息、历史消息、群成员 | `im_v1_*` |
| **Contact (通讯录)** | 1 | 用户 ID 查询（邮箱/手机→open_id） | `contact_v3_*` |
| **Wiki (知识库)** | 14 | 空间列表/详情、节点CRUD/移动/复制、成员管理、任务状态 | `wiki_v2_*` |
| **Bitable (多维表格)** | 46 | 应用/表/字段/记录/视图/角色/成员/仪表盘/工作流 | `bitable_v1_*` |
| **Docx (云文档)** | 19 | 文档创建/读取/编辑/块操作/群公告/导入导出/搜索 | `docx_v1_*`, `docx_builtin_*` |
| **Drive (云空间)** | 49 | 文件管理/权限/评论/版本/导入导出/上传/统计 | `drive_v1_*`, `drive_v2_*` |
| **Sheets (电子表格)** | 34 | 表格/筛选/浮动图片/查找替换/维度移动 | `sheets_v3_*` |

### IM (消息) - 5 tools

| MCP Tool | 功能 | 说明 |
|----------|------|------|
| `im_v1_chat_create` | 创建群聊 | 可设头像、群名、群主、邀请成员 |
| `im_v1_chat_list` | 列出群聊 | 获取 bot 或用户所在群列表 |
| `im_v1_chatMembers_get` | 获取群成员 | 分页返回群成员列表 |
| `im_v1_message_create` | 发送消息 | 支持 text/post/image/file/interactive 等类型 |
| `im_v1_message_list` | 获取聊天历史 | 分页获取单聊或群聊消息记录 |

### Contact (通讯录) - 1 tool

| MCP Tool | 功能 | 说明 |
|----------|------|------|
| `contact_v3_user_batchGetId` | 批量查用户 ID | 通过邮箱或手机号查 open_id/union_id/user_id |

### Wiki (知识库) - 14 tools

| MCP Tool | 功能 | 说明 |
|----------|------|------|
| `wiki_v2_space_list` | 列出知识库空间 | 获取有权限的所有 wiki 空间 |
| `wiki_v2_space_get` | 获取空间信息 | 查询空间名称、类型、可见性 |
| `wiki_v2_space_getNode` | 获取节点信息 | 通过 node_token 或 obj_token 获取节点详情 |
| `wiki_v2_spaceNode_list` | 列出子节点 | 分页获取某空间/节点下的子节点 |
| `wiki_v2_spaceNode_create` | 创建节点 | 在知识库中创建新节点 |
| `wiki_v2_spaceNode_copy` | 复制节点 | 复制 wiki 节点到指定位置 |
| `wiki_v2_spaceNode_move` | 移动节点 | 在 wiki 内移动节点 |
| `wiki_v2_spaceNode_moveDocsToWiki` | 导入文档到 wiki | 将云空间文档移入 wiki 知识库 |
| `wiki_v2_spaceNode_updateTitle` | 更新节点标题 | 修改 wiki 节点标题 |
| `wiki_v2_spaceMember_create` | 添加成员 | 添加知识库空间成员 |
| `wiki_v2_spaceMember_delete` | 删除成员 | 移除知识库空间成员 |
| `wiki_v2_spaceMember_list` | 列出成员 | 获取知识库空间成员列表 |
| `wiki_v2_spaceSetting_update` | 更新空间设置 | 修改知识库空间配置 |
| `wiki_v2_task_get` | 获取任务状态 | 查询异步任务结果 |

### Bitable (多维表格) - 46 tools

**应用管理**: `app_create`, `app_get`, `app_update`, `app_copy`
**表管理**: `appTable_create`, `appTable_list`, `appTable_patch`, `appTable_delete`, `appTable_batchCreate`, `appTable_batchDelete`
**字段管理**: `appTableField_create`, `appTableField_list`, `appTableField_update`, `appTableField_delete`
**记录操作**: `appTableRecord_create`, `appTableRecord_get`, `appTableRecord_list`, `appTableRecord_search`, `appTableRecord_update`, `appTableRecord_delete`, `appTableRecord_batchCreate`, `appTableRecord_batchGet`, `appTableRecord_batchUpdate`, `appTableRecord_batchDelete`
**视图管理**: `appTableView_create`, `appTableView_get`, `appTableView_list`, `appTableView_patch`, `appTableView_delete`
**表单**: `appTableForm_get`, `appTableForm_patch`, `appTableFormField_list`, `appTableFormField_patch`
**角色权限**: `appRole_create`, `appRole_list`, `appRole_update`, `appRole_delete`, `appRoleMember_create`, `appRoleMember_list`, `appRoleMember_delete`, `appRoleMember_batchCreate`, `appRoleMember_batchDelete`
**仪表盘**: `appDashboard_list`, `appDashboard_copy`
**工作流**: `appWorkflow_list`, `appWorkflow_update`

### Docx (云文档) - 19 tools

**文档操作**: `document_create`, `document_get`, `document_rawContent`, `document_convert`
**Block 操作**: `documentBlock_get`, `documentBlock_list`, `documentBlock_patch`, `documentBlock_batchUpdate`, `documentBlockChildren_create`, `documentBlockChildren_get`, `documentBlockChildren_batchDelete`, `documentBlockDescendant_create`
**群公告**: `chatAnnouncement_get`, `chatAnnouncementBlock_get`, `chatAnnouncementBlock_list`, `chatAnnouncementBlock_batchUpdate`, `chatAnnouncementBlockChildren_create`, `chatAnnouncementBlockChildren_get`, `chatAnnouncementBlockChildren_batchDelete`
**导入**: `docx_builtin_import`

### Drive (云空间) - 49 tools

**文件管理**: `file_list`, `file_copy`, `file_move`, `file_delete`, `file_createFolder`, `file_createShortcut`, `file_taskCheck`, `file_subscribe`, `file_getSubscribe`, `file_deleteSubscribe`
**上传**: `file_uploadPrepare`, `file_uploadFinish`, `media_uploadPrepare`, `media_uploadFinish`
**下载**: `media_batchGetTmpDownloadUrl`
**导入导出**: `importTask_create`, `importTask_get`, `exportTask_create`, `exportTask_get`
**权限**: `permissionMember_create`, `permissionMember_list`, `permissionMember_update`, `permissionMember_delete`, `permissionMember_auth`, `permissionMember_batchCreate`, `permissionMember_transferOwner`, `permissionPublic_get`, `permissionPublic_patch`, `permissionPublicPassword_create`, `permissionPublicPassword_update`, `permissionPublicPassword_delete` (+ drive_v2 variants)
**评论**: `fileComment_create`, `fileComment_get`, `fileComment_list`, `fileComment_patch`, `fileComment_batchQuery`, `fileCommentReply_list`, `fileCommentReply_update`, `fileCommentReply_delete`
**版本**: `fileVersion_create`, `fileVersion_get`, `fileVersion_list`, `fileVersion_delete`
**统计**: `fileStatistics_get`, `fileViewRecord_list`, `fileLike_list`
**元数据**: `meta_batchQuery`

### Sheets (电子表格) - 34 tools

**表格操作**: `spreadsheet_create`, `spreadsheet_get`, `spreadsheet_patch`
**Sheet 操作**: `spreadsheetSheet_get`, `spreadsheetSheet_query`, `spreadsheetSheet_find`, `spreadsheetSheet_replace`, `spreadsheetSheet_moveDimension`
**筛选**: `spreadsheetSheetFilter_create`, `spreadsheetSheetFilter_get`, `spreadsheetSheetFilter_update`, `spreadsheetSheetFilter_delete`
**筛选视图**: `spreadsheetSheetFilterView_create`, `spreadsheetSheetFilterView_get`, `spreadsheetSheetFilterView_query`, `spreadsheetSheetFilterView_patch`, `spreadsheetSheetFilterView_delete`
**筛选视图条件**: `spreadsheetSheetFilterViewCondition_create`, `spreadsheetSheetFilterViewCondition_get`, `spreadsheetSheetFilterViewCondition_query`, `spreadsheetSheetFilterViewCondition_update`, `spreadsheetSheetFilterViewCondition_delete`
**浮动图片**: `spreadsheetSheetFloatImage_create`, `spreadsheetSheetFloatImage_get`, `spreadsheetSheetFloatImage_query`, `spreadsheetSheetFloatImage_patch`, `spreadsheetSheetFloatImage_delete`

## API Token Requirements

| API | tenant_access_token | user_access_token | Notes |
|-----|:---:|:---:|-------|
| `im_v1_*` | Y | Y | Bot must be in the group |
| `wiki_v2_*` | Y | Y | Bot must be added to wiki space |
| `docx_v1_*` | Y | Y | Bot needs doc permission |
| `docx_builtin_search` | **N** | **Y only** | Must use user_access_token |
| `docx_builtin_import` | Y | Y | |
| `bitable_v1_*` | Y | Y | Bot needs bitable permission |
| `drive_v1_*` / `drive_v2_*` | Y | Y | Bot needs drive permission |
| `sheets_v3_*` | Y | Y | Bot needs sheets permission |
| `contact_v3_*` | Y | Y | |

**How to tell**: Check tool description. "only supports user_access_token" = UAT only. `useUAT` param present = both supported.

## Required Permissions

Paste in Feishu Open Platform > App > Permissions to bulk enable:
```
im:chat:create, im:chat, im:message, im:chat:member:readonly,
wiki:wiki, wiki:wiki:readonly,
docx:document, docx:document:readonly,
bitable:app, bitable:app:readonly,
drive:drive, drive:drive:readonly, drive:drive:permission,
sheets:spreadsheet, sheets:spreadsheet:readonly,
docs:document:import,
contact:user.id:readonly
```

## 已知知识库结构

### 产品研发知识库

- **space_id**: `7559794508562251778`
- **space_type**: team (团队空间)
- **visibility**: private

#### 顶级目录

| # | 目录名称 | node_token | obj_token | 有子节点 |
|---|---------|-----------|-----------|---------|
| 1 | 产品研发版本说明 | `YZyiwkcBhiAFpYkT3pncPn4qnLh` | `IYIAdQbFKo9iITxvaA3cTPW8nEg` | 有 |
| 2 | 产品研发 | `RG2swgfiEiBsP9kf14dcd7FHnvb` | `T5oYdjOS4oksESxjD81cjO6vnqc` | 有 |
| 3 | 通用组件 | `Pe8wwdLPXiaC0skrTdMcdJc8nLf` | `GlBvdVE2jodQ0sxKJhNcjvYOnTd` | 有 |
| 4 | 联创项目 | `HzTRwXzKiiRj82khaxic7v1EnFf` | `N3vqdJQqNodfFgxSApMcg4jwnm4` | 有 |
| 5 | 研发流程和规范 | `ECAMwlpJFia0WEkcPSZcxTE9n9e` | `Dyoud5dqgo2zuXxnvE2ccLhtnTf` | 有 |
| 6 | 知识产权 | `QR0ewPrjgitXazkoOD0c0IHAn1b` | `QaGadXzJOoS0W8xBQurc4SycnMN` | 有 |
| 7 | 合作伙伴资料 | `OEjTw5l0uiPcOOkh9kbcXL4onpc` | `ZgHtd2S9ZoPK8jx66Bic6ia3n4e` | 有 |
| 8 | 学习资料 | `BORHwWDqoiQ3hVkjIbacQ6Rwnmh` | `P2UcdfojPoDI6Vxanp3cKFxln24` | 有 |
| 9 | 研发进展以及团队建设 | `HpiswvyIjirLSYkIJHhc7LlunWI` | `PYZBdU1qWosZhixQejHcQLdVnRc` | 有 |
| 10 | 技能树：3大场景+33个子技能 | `RsAlwsZJGiBLJ1kk1bbc1JwSnhc` | `ReKodrCQIoQC6TxjtFXcTI8QnHK` | 无 |
| 11 | 具身行业资讯 | `B9a4w7ONvipCdpkmaErcFlKLn5e` | `T2OsdUfUQobskQxLyEOcoDF8nNe` | 有 |

#### 具身行业资讯节点树

| 节点 | node_token | obj_token | 用途 |
|------|-----------|-----------|------|
| 具身行业资讯 (root) | `B9a4w7ONvipCdpkmaErcFlKLn5e` | `T2OsdUfUQobskQxLyEOcoDF8nNe` | 根目录 |
| AI | `IOsNwtIPdiLTYukHdgqcMIE9nad` | `XBLkdx1unof16AxOeY4cqkrvnde` | AI 相关资讯 |
| 技术 | `T1mzw30Bkir5IKkzbx9cxDFHnDe` | `XFZXdpfLsopJVXxSGELcDXlLnte` | 技术相关资讯 |
| 商业 | `EdB8wcEbeigCFPkYqUXcNpZWnlc` | `B2zDdqhaQoTC4bxB8xGcjVLon8c` | 商业相关资讯 |
| 思考 | `Xps2wjrCiixmB3kUKZscWLQQnge` | `F4BqdLtfzofHgsxJNxzc95O9nGe` | 思考类资讯 |

### 标签→飞书节点映射

本地 Obsidian 的 9 类标签映射到飞书「具身行业资讯」的 4 个子节点：

| 本地标签 | 飞书节点 | node_token |
|---------|---------|------------|
| `AI/发展`, `AI/应用`, `AI/影响` | 具身行业资讯/AI | `IOsNwtIPdiLTYukHdgqcMIE9nad` |
| `技术/趋势`, `技术/开发` | 具身行业资讯/技术 | `T1mzw30Bkir5IKkzbx9cxDFHnDe` |
| `商业/创业`, `商业/产品` | 具身行业资讯/商业 | `EdB8wcEbeigCFPkYqUXcNpZWnlc` |
| `思考/创意`, `思考/社会` | 具身行业资讯/思考 | `Xps2wjrCiixmB3kUKZscWLQQnge` |

**映射规则**: 取标签的一级分类（`/` 前的部分），匹配对应飞书节点。

### 资讯推送（广播到所有可见用户）

推送资讯时，**默认发送给 bot 可用范围内的所有用户**（私信），而非群聊。

#### 获取所有可见用户

Bot 的可用范围包含「指定用户」和「指定部门」两部分，需要合并去重：

```python
import json, subprocess, time

def get_token():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST",
         "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"app_id": "<APP_ID>", "app_secret": "<APP_SECRET>"})],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)["tenant_access_token"]

def get_all_visible_users(token):
    """获取 bot 可用范围内的所有用户 open_id"""
    all_users = {}  # open_id -> name

    # 1. 获取通讯录授权范围（包含部门 ID 和直接指定的用户 ID）
    result = subprocess.run(
        ["curl", "-s",
         "https://open.feishu.cn/open-apis/contact/v3/scopes",
         "-H", f"Authorization: Bearer {token}"],
        capture_output=True, text=True
    )
    scopes = json.loads(result.stdout).get("data", {})
    dept_ids = scopes.get("department_ids", [])
    direct_user_ids = scopes.get("user_ids", [])

    # 2. 遍历每个部门，获取部门成员
    for dept_id in dept_ids:
        result = subprocess.run(
            ["curl", "-s",
             f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department"
             f"?department_id={dept_id}&user_id_type=open_id"
             f"&department_id_type=open_department_id&page_size=50",
             "-H", f"Authorization: Bearer {token}"],
            capture_output=True, text=True
        )
        items = json.loads(result.stdout).get("data", {}).get("items", [])
        for user in items:
            all_users[user["open_id"]] = user.get("name", "unknown")

    # 3. 补充直接指定的用户（可能不在任何部门中）
    for uid in direct_user_ids:
        if uid not in all_users:
            all_users[uid] = f"user_{uid[-8:]}"

    return all_users
```

#### 广播发送卡片消息

```python
def broadcast_card(token, users, card):
    """向所有用户发送卡片私信"""
    success, fail = 0, 0
    for uid, name in users.items():
        body = {
            "receive_id": uid,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False)
        }
        result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
             "-H", f"Authorization: Bearer {token}",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(body, ensure_ascii=False)],
            capture_output=True, text=True
        )
        resp = json.loads(result.stdout)
        if resp.get("code") == 0:
            success += 1
        else:
            fail += 1
            print(f"FAIL {name}: {resp.get('msg')}")
        time.sleep(0.1)  # 限流保护
    return success, fail
```

#### 资讯卡片模板

```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "<文章标题>"},
        "template": "blue"  # blue/green/orange/red/purple
    },
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "**作者**: <作者名>\n**分类**: <分类标签>\n\n---\n\n**核心要点**:\n• 要点1\n• 要点2\n• 要点3"
            }
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看原文"},
                    "url": "<原文链接>",
                    "type": "default"
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "知识库全文"},
                    "url": "https://huazhi-ai.feishu.cn/docx/<obj_token>",
                    "type": "primary"
                }
            ]
        }
    ]
}
```

#### 完整推送流程

1. **获取 token**: `get_token()`
2. **获取所有可见用户**: `get_all_visible_users(token)` → 返回 `{open_id: name}` 字典
3. **构建卡片**: 用文章的标题、作者、摘要、链接填充模板
4. **广播发送**: `broadcast_card(token, users, card)`
5. **报告结果**: 打印成功/失败数量

**注意**:
- MCP `im_v1_message_create` 的 `data`/`params` 参数在当前 lark-mcp 版本中存在 JSON 序列化问题，广播推送必须用 curl
- 限流: 飞书 API 限制约 50 QPS，`time.sleep(0.1)` 足够安全
- 权限要求: `contact:user.base:readonly`（获取部门成员）+ `im:message`（发消息）

### 已知群聊

| 群名 | chat_id | 说明 |
|------|---------|------|
| 具身资讯分享 | `oc_ca0e539c7a997487125adcac0f52a3c4` | Bot 已加入（备用，推送优先用广播） |

## Wiki 浏览工作流

现在全部通过 MCP 工具完成，无需 curl：

1. **列出空间**: `wiki_v2_space_list` → 获取 space_id
2. **列出顶级节点**: `wiki_v2_spaceNode_list` (path: space_id) → 获取 node_token + obj_token
3. **展开子节点**: `wiki_v2_spaceNode_list` (params: parent_node_token) → 浏览子树
4. **获取节点详情**: `wiki_v2_space_getNode` (params: token) → 获取元数据
5. **读取文档内容**: `docx_v1_document_rawContent` (path: document_id = obj_token) → 获取文本

**Key distinction**:
- `node_token`: wiki 节点标识 (用于 wiki APIs)
- `obj_token`: 实际文档标识 (用于 docx APIs)
- `space_id`: wiki 空间标识 (不是 node_token，不要传给 getNode)

**快捷访问**: 对于已知节点（见上方目录），直接使用存储的 node_token/obj_token，跳过步骤 1-3。

## Common MCP Operations

**Get wiki node info** (use node_token, NOT space_id):
```
mcp__lark-mcp__wiki_v2_space_getNode
  params: { token: "<node_token>" }
```

**List wiki spaces** (no curl needed):
```
mcp__lark-mcp__wiki_v2_space_list
  params: { page_size: 50 }
```

**List wiki child nodes**:
```
mcp__lark-mcp__wiki_v2_spaceNode_list
  path: { space_id: "7559794508562251778" }
  params: { parent_node_token: "<node_token>", page_size: 50 }
```

**Read document content** (use obj_token from wiki node):
```
mcp__lark-mcp__docx_v1_document_rawContent
  path: { document_id: "<obj_token>" }
```

**List chats**:
```
mcp__lark-mcp__im_v1_chat_list
  params: { page_size: 20 }
```

**Get chat members**:
```
mcp__lark-mcp__im_v1_chatMembers_get
  path: { chat_id: "oc_xxx" }
```

**Get chat history**:
```
mcp__lark-mcp__im_v1_message_list
  params: { container_id_type: "chat", container_id: "oc_xxx", page_size: 20 }
```

**Send message**:
```
mcp__lark-mcp__im_v1_message_create
  params: { receive_id_type: "chat_id" }
  data: { receive_id: "oc_xxx", msg_type: "text", content: "{\"text\":\"hello\"}" }
```

**Send message to user** (need open_id first):
```
# Step 1: Get open_id
mcp__lark-mcp__contact_v3_user_batchGetId
  data: { emails: ["user@company.com"] }
  params: { user_id_type: "open_id" }

# Step 2: Send message
mcp__lark-mcp__im_v1_message_create
  params: { receive_id_type: "open_id" }
  data: { receive_id: "<open_id>", msg_type: "text", content: "{\"text\":\"hello\"}" }
```

**Search bitable records**:
```
mcp__lark-mcp__bitable_v1_appTableRecord_search
  path: { app_token: "xxx", table_id: "xxx" }
  data: { field_names: ["field1"], filter: { conjunction: "and", conditions: [...] } }
```

**Create wiki node**:
```
mcp__lark-mcp__wiki_v2_spaceNode_create
  path: { space_id: "7559794508562251778" }
  data: { obj_type: "docx", parent_node_token: "<parent_node_token>", title: "新文档" }
```

**Move docs to wiki**:
```
mcp__lark-mcp__wiki_v2_spaceNode_moveDocsToWiki
  path: { space_id: "7559794508562251778" }
  data: { parent_wiki_token: "<parent_node_token>", obj_type: "docx", obj_token: "<doc_token>" }
```

## 发布文档到飞书知识库

### 方法选择指南

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 新发布 / 全量更新长文档 | **curl 文件上传导入** | 快速、格式稳定 |
| 更新已发布文档（改链接、改文字） | **Document Block API** | 原地修改，不产生重复文档 |
| 小改动（加标题、改段落） | **Document Block API** | 增量编辑，不需要重新导入 |
| 短文档 / 快速测试 | **MCP `docx_builtin_import`** | 最简单，但长文档格式可能出错 |
| 创建新 wiki 节点 | **MCP `wiki_v2_spaceNode_create`** | 直接创建，无需 curl |

### 方法 1: curl 文件上传导入（推荐）

通过文件上传 + 导入任务的方式，绕过 MCP 的 JSON 序列化限制。速度快，格式解析稳定。

**预处理**（Obsidian → 飞书兼容 Markdown）：
- 去掉 YAML frontmatter
- 去掉 `![[image.png]]` 行（飞书无法显示本地图片）
- `[[wikilink]]` → 纯文本（飞书不支持 wikilink）
- 去掉 `[toc]`（飞书有原生目录功能）

**步骤**：

1. **获取 token**：
   ```bash
   TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
     -H 'Content-Type: application/json' \
     -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")
   ```

2. **上传文件到云盘**：
   ```bash
   FILE_TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/files/upload_all' \
     -H "Authorization: Bearer $TOKEN" \
     -F "file_name=article.md" \
     -F "parent_type=explorer" \
     -F "parent_node=" \
     -F "size=$(wc -c < /tmp/article.md)" \
     -F "file=@/tmp/article.md" \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['file_token'])")
   ```

3. **创建导入任务**（注意 `point` 字段必填）：
   ```bash
   TICKET=$(curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/import_tasks' \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "file_extension":"md",
       "file_token":"'$FILE_TOKEN'",
       "type":"docx",
       "file_name":"文档标题",
       "point":{"mount_type":1,"mount_key":"nodcn8QDoQdhGBYxo9yRouGWEpb"}
     }' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['ticket'])")
   ```

4. **轮询获取文档 token**：
   ```bash
   DOC_TOKEN=$(curl -s "https://open.feishu.cn/open-apis/drive/v1/import_tasks/$TICKET" \
     -H "Authorization: Bearer $TOKEN" \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['result']['token'])")
   ```

5. **移入 wiki 节点**（可用 MCP 或 curl）：
   ```
   mcp__lark-mcp__wiki_v2_spaceNode_moveDocsToWiki
     path: { space_id: "7559794508562251778" }
     data: { parent_wiki_token: "<target parent node_token>", obj_type: "docx", obj_token: "$DOC_TOKEN" }
   ```

6. **回写 frontmatter**：更新本地文件的 `feishu_node_token` 为返回的 `wiki_token`

**注意**：
- `point.mount_key` 使用应用根目录 token `nodcn8QDoQdhGBYxo9yRouGWEpb`
- 导入任务通常 2 秒内完成，但建议轮询检查

### 方法 2: MCP `docx_builtin_import`（简单但慢，长文档格式可能出错）

将 Markdown 内容通过 MCP JSON 参数直接传入。适合短文档或快速测试。

**已知问题**：长文档的 heading 解析可能完全失败。

**流程**：

1. MCP `docx_builtin_import` 导入 → 获得 obj_token
2. MCP `wiki_v2_spaceNode_moveDocsToWiki` 移入 wiki → 获得 wiki_token
3. 回写本地 frontmatter

### 方法 3: Document Block API（增量编辑）

对已有飞书文档进行局部修改时使用。现在可通过 MCP 工具完成：

**获取文档所有 blocks**: `docx_v1_documentBlock_list`
**更新 block**: `docx_v1_documentBlock_patch`
**批量更新**: `docx_v1_documentBlock_batchUpdate`
**追加子 block**: `docx_v1_documentBlockChildren_create`
**删除 blocks**: `docx_v1_documentBlockChildren_batchDelete`

#### Block 类型速查

| block_type | 含义 | 内容 key |
|-----------|------|---------|
| 1 | Page（文档根节点） | `page` |
| 2 | Text（纯文本段落） | `text` |
| 3 | Heading1 | `heading1` |
| 4 | Heading2 | `heading2` |
| 5 | Heading3 | `heading3` |
| 12 | Bullet List（无序列表） | `bullet` |
| 13 | Ordered List（有序列表） | `ordered` |
| 14 | Code Block | `code` |
| 22 | Table | `table` |

## 从飞书知识库拉取内容

### 遍历节点（MCP）

```
mcp__lark-mcp__wiki_v2_spaceNode_list
  path: { space_id: "7559794508562251778" }
  params: { parent_node_token: "<NODE_TOKEN>", page_size: 50 }
```

### 读取文档内容

```
mcp__lark-mcp__docx_v1_document_rawContent
  path: { document_id: "<obj_token>" }
```

### 拉取到本地流程

1. 遍历「具身行业资讯」各子节点，获取所有文档列表
2. 对比本地 vault 中已有的 `feishu_node_token`，找出新文档
3. 用 `docx_v1_document_rawContent` 读取新文档内容
4. 转换为 Markdown，添加 frontmatter（包含 `feishu_node_token` 和 `feishu_sync_time`）
5. 根据来源节点确定本地目录（AI→知识库/, 技术→知识库/ 等）
6. 保存到本地 vault

## Direct API Workarounds

仅在 MCP 工具无法完成时使用 curl：

### Get tenant_access_token
```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])"
```

### 文件上传（MCP 不支持二进制上传）
```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/files/upload_all' \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_name=xxx" -F "parent_type=explorer" -F "parent_node=" \
  -F "size=$(wc -c < file)" -F "file=@file"
```

### 批量文本替换（已验证 Python 脚本）

```python
import json, subprocess, urllib.parse

DOC_ID = '<obj_token>'
OLD = 'old-text'
NEW = 'new-text'
OLD_ENCODED = urllib.parse.quote(OLD, safe='')
NEW_ENCODED = urllib.parse.quote(NEW, safe='')

def curl_json(args):
    result = subprocess.run(['curl', '-s'] + args, capture_output=True, text=True)
    return json.loads(result.stdout)

token = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({'app_id': '<APP_ID>', 'app_secret': '<APP_SECRET>'}),
])['tenant_access_token']

blocks = curl_json([
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_ID}/blocks?page_size=500',
    '-H', f'Authorization: Bearer {token}',
])['data']['items']

for b in blocks:
    if OLD not in json.dumps(b, ensure_ascii=False):
        continue
    block_id = b['block_id']
    content_key = {2: 'text', 12: 'bullet'}.get(b['block_type'])
    if not content_key:
        continue
    elements = b[content_key]['elements']
    new_elements = []
    for elem in elements:
        if 'text_run' not in elem:
            new_elements.append(elem)
            continue
        tr = elem['text_run']
        new_style = dict(tr['text_element_style'])
        if 'link' in new_style:
            new_style['link'] = {'url': new_style['link']['url'].replace(OLD_ENCODED, NEW_ENCODED)}
        new_elements.append({'text_run': {'content': tr['content'].replace(OLD, NEW), 'text_element_style': new_style}})
    resp = curl_json(['-X', 'PATCH',
        f'https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_ID}/blocks/{block_id}',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({'update_text_elements': {'elements': new_elements, 'style': b[content_key].get('style', {})}}),
    ])
    print(f"{'OK' if resp.get('code') == 0 else 'FAIL'} block {block_id}")
```

## Wiki Access Checklist

Wiki APIs return error 99991663 if:

1. **`--token-mode` not set** -> Fix: add `--token-mode tenant_access_token` to config args
2. **Bot not in wiki space** -> Fix: In Feishu wiki settings, add the bot as a member
3. **App permissions not granted** -> Fix: Enable `wiki:wiki:readonly` etc. in Feishu Open Platform > App > Permissions

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `99991663 Invalid access token` | Token not attached to request | Add `--token-mode tenant_access_token` to config |
| `User access token is not configured` | API requires UAT, no login session | Run `login` command or use alternative API |
| `No active login sessions` | UAT expired | Re-run `npx -y @larksuiteoapi/lark-mcp login -a <id> -s <secret>` |
| `131005 not found` | Wrong token type passed | Use correct token: node_token for getNode, obj_token for rawContent |
| Tool not found in ToolSearch | MCP tool not loaded | Use `ToolSearch` with `+lark <keyword>` to load |
| Permission denied | App lacks required scope | Add permissions in Feishu Open Platform > App > Permissions |

## CLI Commands

```bash
# Check session status
npx -y @larksuiteoapi/lark-mcp whoami

# Login (get user_access_token via OAuth)
npx -y @larksuiteoapi/lark-mcp login -a <app_id> -s <app_secret>

# Logout
npx -y @larksuiteoapi/lark-mcp logout
```
