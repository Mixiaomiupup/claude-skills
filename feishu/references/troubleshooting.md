# 飞书 Troubleshooting & 高级操作

## 错误排查

| Error | 原因 | 修复 |
|-------|------|------|
| `99991663 Invalid access token` | --token-mode 未设置 | 加 `--token-mode tenant_access_token` |
| `User access token is not configured` | API 需要 UAT | 运行 OAuth 或用替代 API |
| `131005 not found` | token 类型传错 | node_token → wiki API, obj_token → docx API |
| `131006 permission denied` | Bot 不在 wiki 空间 | wiki 设置中添加 bot 为成员 |
| `1770013 relation mismatch` | upload 的 parent_node 用了 doc_id | parent_node 必须是 image block_id |
| `1770001 invalid param` | 创建 image block 时传了 token | 创建空 block（`image: {}`），再 replace_image |
| 图片黑块/加载中 | upload 关联错误 | 用 create+upload+replace 三步流程 |
| 图片比例变形 | 在导入占位 block 上做 replace_image | 删除占位 block，重新 create+upload+replace |
| `20029 redirect_uri 不合法` | OAuth URL 未配置 | 安全设置添加 `http://localhost:9876/callback` |

## 图片上传详细流程

`tenant_access_token` 已验证可完成全流程（2026-03）。

### 三步插入图片

```bash
TOKEN="<token>"
DOC="<doc_obj_token>"

# 1. 创建空图片 block（index = 目标 child_index）
BLOCK_ID=$(curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/$DOC/blocks/$DOC/children" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"children": [{"block_type": 27, "image": {}}], "index": <N>}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['children'][0]['block_id'])")

# 2. 上传图片（parent_node = image block_id，不是 doc_id！）
FILE_TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/drive/v1/medias/upload_all' \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_name=image.png" \
  -F "parent_type=docx_image" \
  -F "parent_node=$BLOCK_ID" \
  -F "size=$(wc -c < image.png | tr -d ' ')" \
  -F "file=@image.png" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['file_token'])")

# 3. 绑定图片
curl -s -X PATCH "https://open.feishu.cn/open-apis/docx/v1/documents/$DOC/blocks/$BLOCK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"replace_image\":{\"token\":\"$FILE_TOKEN\"}}"
```

### 注意事项

- **parent_node 必须是 image block_id**，不是文档 ID
- **child_index = flat index - 1**（不含 Page block 自身）
- **批量操作从后往前**，避免 index 偏移
- **SVG 先转 PNG**：`rsvg-convert -w 1460 input.svg -o output.png`（不要用 qlmanage）
- 图片 <20MB，超过用分片上传
- 每步 sleep 0.5s，飞书有一致性延迟

## 外部图片处理

飞书导入 `![](url)` 会创建尺寸错误的占位 block（1460x220），`replace_image` 不修正尺寸。

**正确做法**：预处理时去掉外部图片 → 导入 → 对每张图片执行 create+upload+replace（尺寸自动正确）。

`scripts/feishu_publish.py` 已内置此流程。

## Mermaid 发布到飞书

飞书不渲染 Mermaid 代码块。流程：

1. 提取 mermaid 块，`mmdc -i file.mmd -o file.png -w 1460 -b white --scale 2` 转 PNG
2. 导入文档后，找 block_type=14 的代码块（匹配 graph/flowchart 等关键词）
3. 从后往前：删除代码块 → 创建空图片块 → 上传 PNG → replace_image

## 获取 user_access_token

UAT 通过 OAuth 授权码流程获取（2h 有效，refresh_token 30 天）。

### 方法 1：自动 OAuth 服务器

```bash
python3 ~/.claude/skills/feishu/scripts/oauth_server.py &
APP_ID="cli_a928d4672cb89bca"
REDIRECT="http%3A%2F%2Flocalhost%3A9876%2Fcallback"
echo "https://open.feishu.cn/open-apis/authen/v1/authorize?app_id=${APP_ID}&redirect_uri=${REDIRECT}&response_type=code&state=auth"
# 授权后 token 保存到 /tmp/feishu_uat.json
```

### 方法 2：手动

```bash
# 1. 获取 app_access_token
APP_TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"<ID>","app_secret":"<SECRET>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['app_access_token'])")

# 2. code 换 token
curl -s -X POST 'https://open.feishu.cn/open-apis/authen/v1/oidc/access_token' \
  -H "Authorization: Bearer $APP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"grant_type":"authorization_code","code":"<CODE>"}'

# 3. 刷新
curl -s -X POST 'https://open.feishu.cn/open-apis/authen/v1/oidc/refresh_access_token' \
  -H "Authorization: Bearer $APP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"grant_type":"refresh_token","refresh_token":"<TOKEN>"}'
```

Token 缓存：`/tmp/feishu_uat.json`（access_token, refresh_token, expires_in）。

## 批量文本替换

```python
import json, subprocess, urllib.parse

def batch_replace_text(token, doc_id, old, new):
    """替换文档中所有 old → new（含链接中的 URL 编码）"""
    old_enc = urllib.parse.quote(old, safe='')
    new_enc = urllib.parse.quote(new, safe='')

    blocks = curl_json([
        f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500',
        '-H', f'Authorization: Bearer {token}',
    ])['data']['items']

    for b in blocks:
        if old not in json.dumps(b, ensure_ascii=False):
            continue
        block_id = b['block_id']
        key = {2: 'text', 12: 'bullet'}.get(b['block_type'])
        if not key:
            continue
        elements = b[key]['elements']
        new_elements = []
        for e in elements:
            if 'text_run' not in e:
                new_elements.append(e)
                continue
            tr = e['text_run']
            style = dict(tr['text_element_style'])
            if 'link' in style:
                style['link'] = {'url': style['link']['url'].replace(old_enc, new_enc)}
            new_elements.append({'text_run': {'content': tr['content'].replace(old, new), 'text_element_style': style}})
        curl_json(['-X', 'PATCH',
            f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}',
            '-H', f'Authorization: Bearer {token}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({'update_text_elements': {'elements': new_elements, 'style': b[key].get('style', {})}}),
        ])
```

## CLI

```bash
lark-cli auth status      # 检查当前认证状态
lark-cli auth login       # OAuth 登录
lark-cli config init      # 配置应用凭据
```
