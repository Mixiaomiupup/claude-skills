# Feishu API Reference (lark-cli)

所有调用通过 `lark-cli api <METHOD> <PATH> --as bot [--params JSON] [--data JSON]`。

## 通用参数

```bash
--as bot              # 用 tenant_access_token（默认）
--as user             # 用 user_access_token
--params '{"k":"v"}'  # Query 参数
--data '{"k":"v"}'    # Request body
--page-all            # 自动翻页
--format table|csv    # 格式化输出
```

## IM（消息）

```bash
# 创建群聊
lark-cli api POST /open-apis/im/v1/chats --as bot \
  --data '{"name":"群名","chat_type":"group"}'

# 列出群聊
lark-cli api GET /open-apis/im/v1/chats --as bot --params '{"page_size":50}'

# 获取群成员
lark-cli api GET /open-apis/im/v1/chats/{chat_id}/members --as bot

# 发消息
lark-cli api POST /open-apis/im/v1/messages --as bot \
  --params '{"receive_id_type":"chat_id"}' \
  --data '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"hello\"}"}'

# 获取聊天历史
lark-cli api GET /open-apis/im/v1/messages --as bot \
  --params '{"container_id_type":"chat","container_id":"oc_xxx","sort_type":"ByCreateTimeDesc","page_size":20}'

# 回复消息
lark-cli api POST /open-apis/im/v1/messages/{message_id}/reply --as bot \
  --data '{"msg_type":"text","content":"{\"text\":\"reply\"}"}'
```

## Contact（通讯录）

```bash
# 邮箱/手机 → open_id
lark-cli api POST /open-apis/contact/v3/users/batch_get_id --as bot \
  --params '{"user_id_type":"open_id"}' \
  --data '{"emails":["user@co.com"]}'

# 获取部门成员
lark-cli api GET /open-apis/contact/v3/users/find_by_department --as bot \
  --params '{"department_id":"xxx","user_id_type":"open_id","page_size":50}'
```

## Wiki（知识库）

```bash
# 列出空间
lark-cli api GET /open-apis/wiki/v2/spaces --as bot --params '{"page_size":50}'

# 空间详情
lark-cli api GET /open-apis/wiki/v2/spaces/{space_id} --as bot

# 节点详情
lark-cli api GET /open-apis/wiki/v2/spaces/get_node --as bot \
  --params '{"token":"<node_token>"}'

# 列出子节点
lark-cli api GET /open-apis/wiki/v2/spaces/{space_id}/nodes --as bot \
  --params '{"parent_node_token":"<token>","page_size":50}'

# 创建节点
lark-cli api POST /open-apis/wiki/v2/spaces/{space_id}/nodes --as bot \
  --data '{"obj_type":"docx","parent_node_token":"<token>","title":"标题"}'

# 移入 wiki
lark-cli api POST /open-apis/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki --as bot \
  --data '{"parent_wiki_token":"<token>","obj_type":"docx","obj_token":"<doc_token>"}'

# 异步任务状态
lark-cli api GET /open-apis/wiki/v2/tasks/{task_id} --as bot
```

## Docx（云文档）

```bash
# 创建文档
lark-cli api POST /open-apis/docx/v1/documents --as bot \
  --data '{"title":"标题","folder_token":"<folder>"}'

# 获取文档信息
lark-cli api GET /open-apis/docx/v1/documents/{document_id} --as bot

# 获取原始内容
lark-cli api GET /open-apis/docx/v1/documents/{document_id}/raw_content --as bot

# 列出 blocks
lark-cli api GET /open-apis/docx/v1/documents/{document_id}/blocks --as bot \
  --params '{"page_size":500}'

# 更新 block
lark-cli api PATCH /open-apis/docx/v1/documents/{doc}/blocks/{block_id} --as bot \
  --data '{"update_text_elements":{...}}'

# 插入子 blocks
lark-cli api POST /open-apis/docx/v1/documents/{doc}/blocks/{parent}/children --as bot \
  --data '{"children":[...],"index":N}'

# 批量删除子 blocks
lark-cli api DELETE /open-apis/docx/v1/documents/{doc}/blocks/{parent}/children/batch_delete --as bot \
  --data '{"start_index":N,"end_index":M}'
```

## Drive（云空间）

```bash
# 列出文件
lark-cli api GET /open-apis/drive/v1/files --as bot \
  --params '{"folder_token":"<token>","page_size":50}'

# 创建文件夹
lark-cli api POST /open-apis/drive/v1/files/create_folder --as bot \
  --data '{"name":"文件夹名","folder_token":"<parent>"}'

# 导入任务
lark-cli api POST /open-apis/drive/v1/import_tasks --as bot \
  --data '{"file_extension":"md","file_token":"<token>","type":"docx","file_name":"title"}'

# 查询导入状态
lark-cli api GET /open-apis/drive/v1/import_tasks/{ticket} --as bot
```

## Bitable（多维表格）

```bash
# 列出表格
lark-cli api GET /open-apis/bitable/v1/apps/{app_token}/tables --as bot

# 搜索记录
lark-cli api POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search --as bot \
  --data '{"field_names":["f1"],"filter":{"conjunction":"and","conditions":[...]}}'

# 创建记录
lark-cli api POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records --as bot \
  --data '{"fields":{"字段1":"值1"}}'

# 批量创建
lark-cli api POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create --as bot \
  --data '{"records":[{"fields":{...}},...]}'
```

## Sheets（电子表格）

```bash
# 创建表格
lark-cli api POST /open-apis/sheets/v3/spreadsheets --as bot \
  --data '{"title":"表格名"}'

# 获取表格信息
lark-cli api GET /open-apis/sheets/v3/spreadsheets/{spreadsheet_token} --as bot

# 查询 sheet
lark-cli api GET /open-apis/sheets/v3/spreadsheets/{token}/sheets/query --as bot
```

## 文件上传（需 curl）

lark-cli 不支持 multipart form-data，文件上传仍需 curl：

```bash
# 获取 tenant_access_token
TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# 上传文件
curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/files/upload_all' \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_name=xxx" -F "parent_type=explorer" -F "parent_node=" \
  -F "size=$(wc -c < file)" -F "file=@file"
```

## Token 要求

| API | --as bot | --as user | 备注 |
|-----|:---:|:---:|------|
| im | Y | Y | Bot 须在群内 |
| wiki | Y | Y | Bot 须在 wiki 空间 |
| docx_builtin_search | N | Y | 仅 user token |
| 其他 | Y | Y | |

## 权限清单

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
