---
name: lark-mcp
description: Use when accessing Feishu/Lark resources via MCP - wiki knowledge base, documents, chats, bitable. Also use when Lark MCP token errors occur (99991663, "invalid access token", "user access token is not configured").
---

# Lark MCP

Feishu/Lark MCP integration reference. Covers tool inventory, verified capabilities, direct API workarounds, and troubleshooting.

## Config

**Location**: `~/.claude.json` > `mcpServers` > `lark-mcp`

**Required args**: `-a <app_id> -s <app_secret> --token-mode tenant_access_token`

`--token-mode` must be explicitly set. Default `auto` causes wiki/doc APIs to fail when no user session exists.

**Enable specific tools** (overrides defaults): add `-t "tool1,tool2,preset.im.default"` to args.

## Token Types

| Token | How to Get | Scope |
|-------|-----------|-------|
| **tenant_access_token** | Auto-generated from app_id + app_secret | Bot-accessible resources |
| **user_access_token** | `npx -y @larksuiteoapi/lark-mcp login -a <id> -s <secret>` | User-scoped resources |

## Official Default Tools (19 total)

Source: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/mcp_integration/mcp_installation

### Verified Available via MCP (17/19)

| # | MCP Tool Name | Function | Verified |
|---|---------------|----------|----------|
| 1 | `im_v1_chat_create` | Create group chat | Not tested (write op) |
| 2 | `im_v1_chat_list` | List groups bot is in | **Tested OK** |
| 3 | `im_v1_chatMembers_get` | Get group member list | **Tested OK** |
| 4 | `im_v1_message_create` | Send message | Not tested (write op) |
| 5 | `im_v1_message_list` | Get chat history | **Tested OK** |
| 6 | `wiki_v2_space_getNode` | Get wiki node info | **Tested OK** |
| 7 | `docx_v1_document_rawContent` | Get document plain text | **Tested OK** |
| 8 | `drive_v1_permissionMember_create` | Add collaborator permission | Not tested (write op) |
| 9 | `docx_builtin_import` | Import document (markdown -> docx) | Not tested (write op) |
| 10 | `bitable_v1_app_create` | Create bitable app | Not tested (write op) |
| 11 | `bitable_v1_appTable_create` | Create table in bitable | Not tested (write op) |
| 12 | `bitable_v1_appTable_list` | List tables in bitable | Available, needs app_token |
| 13 | `bitable_v1_appTableField_list` | List fields in table | Available, needs app_token |
| 14 | `bitable_v1_appTableRecord_search` | Search records in table | Available, needs app_token |
| 15 | `bitable_v1_appTableRecord_create` | Create record | Not tested (write op) |
| 16 | `bitable_v1_appTableRecord_update` | Update record | Not tested (write op) |
| 17 | `contact_v3_user_batchGetId` | Get user ID by phone/email | **Tested OK** |

### Not Found in ToolSearch (2/19)

| # | Tool Name | Function | Notes |
|---|-----------|----------|-------|
| 18 | `wiki_v1_node_search` | Search wiki nodes | User reports it should work; may be ToolSearch discovery issue |
| 19 | `docx_builtin_search` | Search cloud documents | Requires user_access_token only |

**Note**: `wiki_v1_node_search` may exist on the MCP server but not appear in Claude Code's ToolSearch. Try calling it directly if needed.

## API Token Requirements

| API | tenant_access_token | user_access_token | Notes |
|-----|:---:|:---:|-------|
| `im_v1_chat_list` | Y | Y | Bot must be in the group |
| `im_v1_message_create/list` | Y | Y | Bot must be in the group |
| `wiki_v1_node_search` | Y | Y | Bot must be added to wiki space |
| `wiki_v2_space_getNode` | Y | Y | Bot must be added to wiki space |
| `docx_v1_document_rawContent` | Y | Y | Bot needs doc permission |
| `docx_builtin_search` | **N** | **Y only** | Description explicitly states this |
| `docx_builtin_import` | Y | Y | |
| `bitable_v1_*` | Y | Y | Bot needs bitable permission |
| `contact_v3_user_batchGetId` | Y | Y | |

**How to tell**: Check tool description. "only supports user_access_token" = UAT only. `useUAT` param present = both supported.

## Required Permissions

Paste in Feishu Open Platform > App > Permissions to bulk enable:
```
im:chat:create, im:chat, im:message, wiki:wiki, wiki:wiki:readonly, docx:document, bitable:app, drive:drive, docs:document:import, contact:user.id:readonly
```

## Direct API Workarounds

When MCP tools are insufficient (e.g. listing wiki spaces, browsing child nodes), use direct Feishu API via curl.

### Get tenant_access_token
```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])"
```

### List all wiki spaces (no MCP tool for this)
```bash
curl -s "https://open.feishu.cn/open-apis/wiki/v2/spaces?page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

### List wiki root nodes
```bash
curl -s "https://open.feishu.cn/open-apis/wiki/v2/spaces/<SPACE_ID>/nodes?page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

### List wiki child nodes
```bash
curl -s "https://open.feishu.cn/open-apis/wiki/v2/spaces/<SPACE_ID>/nodes?parent_node_token=<NODE_TOKEN>&page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

### Browse full wiki tree (batch script)
```bash
TOKEN=$(...get token...) && \
SPACE_ID="<space_id>" && \
curl -s "https://open.feishu.cn/open-apis/wiki/v2/spaces/$SPACE_ID/nodes?parent_node_token=<NODE>&page_size=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
for item in json.load(sys.stdin).get('data',{}).get('items',[]):
    icon = '📁' if item.get('has_child') else '📄'
    print(f'{icon} {item[\"title\"]}  [node:{item[\"node_token\"]}] [doc:{item[\"obj_token\"]}] [{item[\"obj_type\"]}]')
"
```

## Common MCP Operations

**Get wiki node info** (use node_token, NOT space_id):
```
mcp__lark-mcp__wiki_v2_space_getNode
  params: { token: "<node_token>" }
```

**Read document content** (use obj_token from wiki node):
```
mcp__lark-mcp__docx_v1_document_rawContent
  path: { document_id: "<obj_token>" }
```

**Search wiki** (if available):
```
mcp__lark-mcp__wiki_v1_node_search
  data: { query: "keyword", space_id: "optional" }
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

**Search bitable records**:
```
mcp__lark-mcp__bitable_v1_appTableRecord_search
  path: { app_token: "xxx", table_id: "xxx" }
  data: { field_names: ["field1"], filter: { conjunction: "and", conditions: [...] } }
```

## Wiki Browsing Workflow

Recommended flow to browse a wiki knowledge base:

1. **List spaces** (direct API, no MCP tool): get space_id
2. **List root nodes** (direct API): get node_token + obj_token for each
3. **Expand children** (direct API with parent_node_token): browse tree
4. **Get node info** (MCP `wiki_v2_space_getNode`): get metadata
5. **Read content** (MCP `docx_v1_document_rawContent`): get document text

**Key distinction**:
- `node_token`: wiki node identifier (use with wiki APIs)
- `obj_token`: actual document identifier (use with docx APIs)
- `space_id`: wiki space identifier (NOT a node_token, don't pass to getNode)

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
| `131005 not found` | Wrong token type passed (e.g. space_id as node_token) | Use correct token: node_token for getNode, obj_token for rawContent |
| Tool not found in ToolSearch | MCP server exposes it but Claude Code doesn't discover it | Try direct API call as workaround |

## 已知知识库结构

### 产品研发知识库

- **space_id**: `7559794508562251778`

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

## 发布文档到飞书知识库

### 方法选择指南

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 新发布 / 全量更新长文档 | **curl 文件上传导入** | 快速、格式稳定 |
| 小改动（加标题、改段落） | **Document Block API** | 增量编辑，不需要重新导入 |
| 短文档 / 快速测试 | **MCP `docx_builtin_import`** | 最简单，但长文档格式可能出错 |

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

5. **移入 wiki 节点**：
   ```bash
   WIKI_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/wiki/v2/spaces/$SPACE_ID/nodes/move_docs_to_wiki" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "parent_wiki_token":"<target parent node_token>",
       "obj_type":"docx",
       "obj_token":"'$DOC_TOKEN'"
     }' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['wiki_token'])")
   ```

6. **回写 frontmatter**：更新本地文件的 `feishu_node_token` 为 `$WIKI_TOKEN`

**注意**：
- `point.mount_key` 使用应用根目录 token `nodcn8QDoQdhGBYxo9yRouGWEpb`
- 导入任务通常 2 秒内完成，但建议轮询检查
- 可以用 Python 脚本批量处理多篇文章

### 方法 2: MCP `docx_builtin_import`（简单但慢，长文档格式可能出错）

将 Markdown 内容通过 MCP JSON 参数直接传入。适合短文档或快速测试。

**已知问题**：长文档的 heading 解析可能完全失败（所有 block 变为纯文本 type 2），原因是整篇文章作为 JSON 内联字符串传入时序列化不稳定。

**流程**：

1. 用 MCP `docx_builtin_import` 导入 Markdown 内容：
   ```
   mcp__lark-mcp__docx_builtin_import
     data: { file_name: "标题.md", markdown: "<markdown content>" }
   ```
   获得新文档的 `token`（即 obj_token）

2. 用直接 API 将新文档移入 wiki 目标节点下：
   ```bash
   curl -X POST "https://open.feishu.cn/open-apis/wiki/v2/spaces/$SPACE_ID/nodes/move_docs_to_wiki" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "parent_wiki_token": "<target parent node_token>",
       "obj_type": "docx",
       "obj_token": "<token from step 1>"
     }'
   ```
   返回 `wiki_token`

3. 将 `wiki_token` 记录到本地 frontmatter 的 `feishu_node_token` 字段

**注意**: 不要先创建空 wiki 节点再导入内容，应先导入文档再移入 wiki。

### 方法 3: Document Block API（增量编辑）

对已有飞书文档进行小改动时使用，无需重新导入整篇文档。

**获取文档 block 结构**：
```bash
# 获取文档所有 blocks
curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_token>/blocks" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
blocks = json.load(sys.stdin)['data']['items']
for b in blocks:
    bt = b.get('block_type', 0)
    bid = b['block_id']
    # Type 1=Page, 2=Text, 3=Heading1, 4=Heading2, ...
    text = ''
    for key in ['text', 'heading1', 'heading2', 'heading3']:
        el = b.get(key, {}).get('elements', [])
        if el:
            text = el[0].get('text_run', {}).get('content', '')[:50]
            break
    print(f'  type={bt} id={bid} text={text}')
"
```

**在指定 block 后追加子 block**：
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_token>/blocks/<block_id>/children" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [{
      "block_type": 3,
      "heading1": {
        "elements": [{"text_run": {"content": "新标题"}}]
      }
    }]
  }'
```

**修改已有 block 内容**：
```bash
curl -s -X PATCH "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_token>/blocks/<block_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "update_text_elements": {
      "elements": [{"text_run": {"content": "更新后的文本"}}]
    }
  }'
```

**删除 blocks**：
```bash
curl -s -X DELETE "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_token>/blocks/<parent_block_id>/children/batch_delete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"start_index": 0, "end_index": 2}'
```

**Block 类型速查**：
| block_type | 含义 |
|-----------|------|
| 1 | Page（文档根节点） |
| 2 | Text（纯文本段落） |
| 3 | Heading1 |
| 4 | Heading2 |
| 5 | Heading3 |
| 12 | Ordered List |
| 13 | Unordered List |
| 14 | Code Block |
| 22 | Table |

## 从飞书知识库拉取内容

### 遍历节点

```bash
# 列出某节点下的子文档
TOKEN=$(...) && SPACE_ID="7559794508562251778"
curl -s "https://open.feishu.cn/open-apis/wiki/v2/spaces/$SPACE_ID/nodes?parent_node_token=<NODE_TOKEN>&page_size=50" \
  -H "Authorization: Bearer $TOKEN"
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

## CLI Commands

```bash
# Check session status
npx -y @larksuiteoapi/lark-mcp whoami

# Login (get user_access_token via OAuth)
npx -y @larksuiteoapi/lark-mcp login -a <app_id> -s <app_secret>

# Logout
npx -y @larksuiteoapi/lark-mcp logout
```
