---
name: feishu
description: Use when accessing Feishu/Lark resources - wiki knowledge base, documents, chats, bitable. Also use when Lark API errors occur. Use for ANY Feishu interaction including publishing articles, broadcasting messages, reading docs, managing bitable records, or troubleshooting API issues.
---

# Feishu Integration

飞书 API 集成。通过 `lark-cli` + `_shared/feishu_publish.py` + `feishu_broadcast.py` 覆盖知识库、文档、消息、多维表格、电子表格。

## Config

**lark-cli**: `npm install -g @larksuite/cli`，通过 `lark-cli config init` 配置应用凭据。

**当前应用**: 具身资讯bot `cli_a928d4672cb89bca`

Token 由 lark-cli 自动管理（`--as bot` 用 tenant token，`--as user` 用 user token）。

## 快速路由

根据任务选择正确的方法：

| 任务 | 方法 | 详情 |
|------|------|------|
| **发布新文档到知识库** | `_shared/feishu_publish.py` | 预处理 → 上传 → 导入 → 移入 wiki → 插入图片 |
| **广播推送卡片** | `python3 scripts/feishu_broadcast.py` | 获取可见用户 → 构建卡片 → 私信推送 |
| **更新已有文档（推荐）** | `lark-cli docs +update --mode overwrite` | 见下方「更新文档」 |
| **更新已有文档（局部）** | `lark-cli` Document Block API | 见下方「Block API 局部修改」 |
| **读取文档** | `lark-cli api GET /open-apis/docx/v1/documents/{doc}/raw_content --as bot` | |
| **浏览知识库** | `lark-cli api GET /open-apis/wiki/v2/spaces/{space}/nodes --as bot` | 见下方「浏览知识库」 |
| **操作多维表格** | `lark-cli api` bitable 端点 | 见 `references/api-reference.md` |
| **发消息** | `lark-cli api POST /open-apis/im/v1/messages --as bot` | |
| **排查错误** | `references/troubleshooting.md` | 错误码 → 原因 → 修复 |
| **查节点 token** | `references/wiki-structure.md` | 已知节点/部门/群聊 |

## 发布新文档

使用共享脚本 `_shared/feishu_publish.py`：

```python
import os
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

# 带本地图片的日报（x-feed、embodied-intel）
result = publish_to_feishu(
    md_path='article.md', doc_title='标题',
    wiki_parent_node='UzfowFW4sidwVdkZulecDOQ3nyd',
    card_template='blue', card_title='标题', card_summary='要点',
    recipients='all', media_dir='~/media/',
)

# 带外部 URL 图片的文章（chat-digest）
result = publish_article_to_feishu(
    md_path='article.md', doc_title='标题',
    wiki_parent_node='UzfowFW4sidwVdkZulecDOQ3nyd',
)
```

两个入口函数：
- `publish_to_feishu()`：完整版，含本地图片/视频插入 + 卡片推送 + frontmatter 回写
- `publish_article_to_feishu()`：精简版，含外部 URL 图片下载插入，无推送

**手动执行**时按以下步骤（脚本内部逻辑相同）：

1. 预处理 Markdown（去 frontmatter，**去掉外部图片 URL**，记录图片位置）
2. curl 上传 .md 文件 → file_token
3. curl 创建导入任务 → 轮询获取 doc_token
4. `lark-cli api POST /open-apis/wiki/v2/spaces/{space}/nodes/move_docs_to_wiki --as bot` 移入目标节点
5. 对每张外部图片：下载 → 创建空 image block → upload → replace_image
6. 回写本地 frontmatter（feishu_node_token, feishu_sync_time）

**关键规则**：
- **外部图片必须先去掉再导入**。飞书导入会为 `![](url)` 创建尺寸错误的占位 block（1460x220），`replace_image` 不会修正尺寸。正确做法：导入后用 create+upload+replace 插入（尺寸自动正确）
- `point.mount_key` 固定为 `nodcn8QDoQdhGBYxo9yRouGWEpb`
- SVG 必须先转 PNG：`rsvg-convert -w 1460 input.svg -o output.png`
- Mermaid 代码块飞书不渲染，导入前用 `mmdc -w 1460 -b white --scale 2` 转 PNG

## 广播推送

```bash
python3 ~/.claude/skills/feishu/scripts/feishu_broadcast.py \
  --title "文章标题" \
  --author "作者名" \
  --summary "要点1|要点2|要点3" \
  --source-url "https://原文链接" \
  --doc-url "https://huazhi-ai.feishu.cn/docx/xxx"
```

也可传 `--department` 按部门定向推送（如 `--department 后场-研发`）。

部门 ID 和已知群聊见 `references/wiki-structure.md`。

## 更新已有文档

### 整体覆盖（推荐）

**优先用 `lark-cli docs +update --mode overwrite`**，比 Block API 逐块改快得多（~15 次 API vs 50-100+ 次）：

```bash
lark-cli docs +update --doc <doc_token> --mode overwrite --as bot --markdown "$CONTENT"
```

**含 Mermaid 图的文档更新完整流程**：

1. 预处理 Markdown：Mermaid 代码块 → `IMG_PLACEHOLDER_N`，去 wikilinks
2. `mmdc -w 1460 -b white --scale 2` 转 PNG（每个 Mermaid 块）
3. `lark-cli docs +update --mode overwrite` 覆盖文档内容
4. 读取所有 blocks，找到包含 `IMG_PLACEHOLDER_N` 的 text blocks
5. 对每个占位符：delete text block → create image block → upload PNG → replace_image

URL 和 doc_token 不变，无需重新移入 wiki 节点。

### Block API 局部修改

仅修改少量内容时使用（如更新一个段落、插入一个 block）：

```bash
# 1. 获取所有 blocks
lark-cli api GET /open-apis/docx/v1/documents/{doc}/blocks --as bot --params '{"page_size":500}'

# 2. 更新 block
lark-cli api PATCH /open-apis/docx/v1/documents/{doc}/blocks/{block_id} --as bot \
  --data '{"update_text_elements": {...}}'

# 3. 删除 blocks
lark-cli api DELETE /open-apis/docx/v1/documents/{doc}/blocks/{parent}/children/batch_delete --as bot \
  --data '{"start_index": N, "end_index": M}'

# 4. 插入 blocks
lark-cli api POST /open-apis/docx/v1/documents/{doc}/blocks/{parent}/children --as bot \
  --data '{"children": [...], "index": N}'
```

Block 类型速查：

| block_type | 含义 | key |
|-----------|------|-----|
| 2 | Text | `text` |
| 3/4/5 | H1/H2/H3 | `heading1/2/3` |
| 12/13 | 无序/有序列表 | `bullet/ordered` |
| 14 | Code | `code` |
| 27 | Image | `image` |

**批量操作从后往前**，避免 index 偏移。child_index = flat index - 1（不含 Page block）。

## 浏览知识库

```bash
# 1. 列出空间
lark-cli api GET /open-apis/wiki/v2/spaces --as bot --params '{"page_size":50}'

# 2. 列出子节点
lark-cli api GET /open-apis/wiki/v2/spaces/7559794508562251778/nodes --as bot \
  --params '{"parent_node_token":"<token>","page_size":50}'

# 3. 读取文档内容（用 obj_token）
lark-cli api GET /open-apis/docx/v1/documents/<obj_token>/raw_content --as bot
```

**Token 区分**：
- `node_token` → wiki API（节点操作）
- `obj_token` → docx API（文档内容）
- `space_id` → 空间级操作（不要传给 getNode）

已知节点可直接用存储的 token，跳过列出步骤。见 `references/wiki-structure.md`。

## 发消息

```bash
# 发文本到群
lark-cli api POST /open-apis/im/v1/messages --as bot \
  --params '{"receive_id_type":"chat_id"}' \
  --data '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"hello\"}"}'

# 发私信（先查 open_id）
lark-cli api POST /open-apis/contact/v3/users/batch_get_id --as bot \
  --params '{"user_id_type":"open_id"}' \
  --data '{"emails":["user@co.com"]}'
```

## Category → 飞书节点映射

| 本地 category | 飞书节点 | node_token |
|--------------|---------|------------|
| `模型前沿/*` | 行业前沿/模型前沿 | `Za2NwAddOidZ1Ikm4CKcyHS7nSc` |
| `具身动态/*` | 行业前沿/具身动态 | `UzfowFW4sidwVdkZulecDOQ3nyd` |
| `编程范式/*` | 行业前沿/编程范式 | `Nvrzwk0MAi5bPYkBucMcn1uJnkh` |
| `AI思考/*` | 行业前沿/AI思考 | `Me5EwNgwciDpKRk0YSPcKaWHnAo` |
| `商业观察/*` | 行业前沿/商业观察 | `End8wv8oei8eQ6kr5pzcOpmVnyh` |
| `工程实战/*` | → 编程范式 | `Nvrzwk0MAi5bPYkBucMcn1uJnkh` |

取 category 一级分类（`/` 前）匹配。space_id: `7559794508562251778`。

## 参考文件

| 文件 | 内容 | 何时读 |
|------|------|-------|
| `references/api-reference.md` | API 端点清单、lark-cli 调用示例、token/权限要求 | 需要查找 API 参数时 |
| `references/wiki-structure.md` | 知识库节点树、部门 ID、群聊 ID | 需要 token/ID 查找时 |
| `references/troubleshooting.md` | 错误排查、图片上传详情、UAT 获取、Mermaid 发布 | 遇到错误或需要高级操作时 |
