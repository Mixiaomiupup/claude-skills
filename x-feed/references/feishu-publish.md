# Feishu Publish Reference

飞书文档发布和视频嵌入的详细实现。在 Digest Mode Step 8 中使用。

---

## 1. Video Embed in Feishu (3-step method)

File block (block_type 23) is the only API-supported way to embed playable video in Feishu docs.
The `view_type` is controlled by the auto-generated View block (block_type 33), which defaults to card view.
API does NOT support creating inline video players — only the Feishu UI can do that.

```python
# Step 1: Create empty file block
body = {"children": [{"block_type": 23, "file": {}}], "index": -1}
resp = curl_json(['-X', 'POST',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{parent_block_id}/children',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(body),
])
created_block_id = resp['data']['children'][0]['block_id']

# CRITICAL: API may wrap file block in a View block (type 33).
# Must get the actual file block (child of View block) for upload & PATCH.
import time; time.sleep(0.5)
block_resp = curl_json(['-X', 'GET',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{created_block_id}',
    '-H', f'Authorization: Bearer {token}',
])
block_data = block_resp.get('data', {}).get('block', {})
if block_data.get('block_type') == 33 and block_data.get('children'):
    file_block_id = block_data['children'][0]  # Real file block inside View wrapper
else:
    file_block_id = created_block_id

# Step 2: Upload video with parent_node = file_block_id (CRITICAL!)
resp = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/drive/v1/medias/upload_all',
    '-H', f'Authorization: Bearer {token}',
    '-F', f'file_name={video_filename}',
    '-F', 'parent_type=docx_file',
    '-F', f'parent_node={file_block_id}',  # Must be file_block_id, NOT doc_token
    '-F', f'size={file_size}',
    '-F', f'file=@{video_path}',
])
media_token = resp['data']['file_token']

# Step 3: PATCH replace_file
resp = curl_json(['-X', 'PATCH',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{file_block_id}',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({"replace_file": {"token": media_token}}),
])
```

**Critical**: `parent_node` in Step 2 MUST be `file_block_id`, NOT doc_token. Using doc_token causes `relation mismatch` (error 1770013).

### What doesn't work

| Approach | Result | Reason |
|----------|--------|--------|
| Create file block with token in one call | `invalid param` | API only accepts empty `file: {}` at creation |
| iframe block with x.com URL | `ERR_CONNECTION_CLOSED` | X.com blocked in China |
| PATCH on View block wrapper (type 33) | error 1770025 | Must PATCH the child file block, not the View wrapper |

---

## 2. Publish Script

使用共享脚本 `~/.claude/skills/_shared/feishu_publish.py`：

```python
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

# Step 8.1: 清理多余文件
import glob, os
media_dir = os.path.expanduser('~/Downloads/x-daily/YYYY-MM-DD')
for f in glob.glob(os.path.join(media_dir, 'cover-raw.png')) + glob.glob(os.path.join(media_dir, 'tweet-full-*.png')):
    os.remove(f)

# Step 8.2: 发布（含封面、截图、视频上传 + 卡片广播）
result = publish_to_feishu(
    md_path=os.path.expanduser('~/Documents/obsidian/mixiaomi/日报/智涌日报-YYYY-MM-DD.md'),
    doc_title='智涌日报 - YYYY-MM-DD',
    wiki_parent_node='Rs4fwW23SiU0mCk0aBZcupXNnvd',
    media_dir=media_dir,
    card_template='blue',
    card_title='智涌日报 - YYYY-MM-DD',
    card_summary='**本日 AI 热点速览**\n\n**具身智能**\n* 要点1\n\n**模型与研究**\n* 要点1\n\n**产品与工具**\n* 要点1',
    recipients='all',
)
```

**更新模式**: `publish_to_feishu()` 自动检测 frontmatter 中的 `feishu_node_token`。若已存在则清空旧文档并覆盖（URL 不变）；若不存在则新建。

**注意**：`media_dir` 不传或传 `None` 则只发布文本。**必须传此参数。**

---

## 3. 父节点映射

| 内容类型 | parent_wiki_token | 飞书节点 |
|---------|-------------------|---------|
| 智涌日报 | `Rs4fwW23SiU0mCk0aBZcupXNnvd` | 日报/智涌日报 |
| 模型前沿 | `Za2NwAddOidZ1Ikm4CKcyHS7nSc` | 行业前沿/模型前沿 |
| 具身动态 | `UzfowFW4sidwVdkZulecDOQ3nyd` | 行业前沿/具身动态 |
| 编程范式 | `Nvrzwk0MAi5bPYkBucMcn1uJnkh` | 行业前沿/编程范式 |
| AI思考 | `Me5EwNgwciDpKRk0YSPcKaWHnAo` | 行业前沿/AI思考 |
| 商业观察 | `End8wv8oei8eQ6kr5pzcOpmVnyh` | 行业前沿/商业观察 |

**权限要求**：`wiki:wiki` + `drive:drive` + `im:message` + `contact:user.base:readonly`
