---
name: chat-digest
description: "华智全员群文章分享日报。扫描群聊中分享的 URL，抓取文章内容，保存到飞书行业前沿知识库，生成汇总卡片推送全员。当用户说'群聊日报'、'今天群里分享了什么'、'文章汇总'、'chat digest'时使用。"
---

# 群聊文章分享日报

扫描华智全员群中当天分享的文章链接，抓取内容并保存到飞书行业前沿知识库，生成结构化汇总推送全员。

**工具依赖**：`lark-cli`（群消息读取 + 消息发送）、`anyweb`（微信/腾讯新闻 HTML 提取）、`markdownify`（HTML→Markdown）、`tavily_extract`（非微信文章抓取）、`_shared/feishu_publish.py`（知识库发布，`publish_article_to_feishu()`）、`feishu_broadcast.py`（全员推送）

---

## 工作流

```
Step 1: 读取群消息 → Step 2: 提取 URL + 跨次去重 → Step 3: 抓取文章 → Step 4: 筛选 + 保存到知识库 → Step 5: 生成汇总 → Step 6: 推送 → Step 7: 清理
```

### Step 1: 读取当日群消息

先加载 tavily 工具和去重记录：
```
ToolSearch: "+tavily extract" -> tavily_extract
```

```bash
mkdir -p /tmp/chat-digest

lark-cli im +chat-messages-list \
  --chat-id oc_c7e33df4ad9f8d387ab7348395d99b0a \
  --as bot --page-size 50 --sort asc \
  --start "YYYY-MM-DDT00:00:00+08:00" \
  --end "YYYY-MM-DDT23:59:59+08:00"
```

如消息超 50 条，用 `--page-token` 翻页。

**消息格式**：每条消息包含 `content`（文本）、`sender.name`（发送人）、`create_time`（时间）、`msg_type`（text/post/...）。

### Step 2: 提取 URL 并过滤

从消息 `content` 中提取所有 `https?://` URL。

**过滤规则**：
- **保留**：`mp.weixin.qq.com`、`github.com`、`arxiv.org`、`xiaohongshu.com`、`xhslink.com`、`zhihu.com`、`news.qq.com`、`*.github.io`、其他非飞书外部链接
- **排除**：`feishu.cn`（内部文档，不需要入库）、纯图片/表情消息、bot 发的消息（`sender_type != "user"`）

记录每条 URL 的：
- `url`：原始链接
- `sender`：谁分享的
- `time`：分享时间
- `context`：消息中 URL 之外的文字（分享评语）

**去重（两层）**：

1. **同次去重**：同一 URL 被多人分享只处理一次（保留最早分享者）
2. **跨次去重**：检查 `~/.claude/data/chat-digest/processed.json`，已处理过的 URL 标记为"[已入库]"跳过抓取

```bash
# 加载去重记录
PROCESSED_FILE=~/.claude/data/chat-digest/processed.json
mkdir -p ~/.claude/data/chat-digest
[ -f "$PROCESSED_FILE" ] || echo '{}' > "$PROCESSED_FILE"
```

`processed.json` 格式：
```json
{
  "https://mp.weixin.qq.com/s/xxx": {
    "title": "文章标题",
    "doc_token": "AbcDeFgH...",
    "category": "具身动态",
    "shared_by": "李玮",
    "date": "2026-04-03",
    "skipped": false,
    "skip_reason": null
  },
  "https://mp.weixin.qq.com/s/yyy": {
    "title": "某新闻标题",
    "doc_token": null,
    "category": null,
    "shared_by": "谢娟",
    "date": "2026-04-02",
    "skipped": true,
    "skip_reason": "新闻资讯"
  }
}
```

对每条提取到的 URL，先查 `processed.json`：
- 已存在且 `skipped: false` → 跳过，日报中标注"[已入库]"
- 已存在且 `skipped: true` → 跳过，日报中标注"[已跳过：{skip_reason}]"
- 不存在 → 继续抓取流程

### Step 3: 抓取文章内容

按 URL 来源选择不同的抓取方式。

#### 微信公众号（mp.weixin.qq.com）— 必须用 anyweb + markdownify

`tavily_extract` 和 `anyweb read` 都会丢失格式（标题、加粗、列表）和视频，不能用于公众号。

> **注意**：`anyweb --cdp state --ax` 可以获取微信文章的结构化纯文本（heading、paragraph），但**不包含图片 URL 和 HTML 格式**，无法替代 eval+markdownify 流程。AX tree 适合 Grok 等交互页面的文本读取，不适合需要保留图片和格式的文章抓取。

```bash
# 1. 打开页面（用 --cdp 自动启动独立 Chrome，交互式 DOM 操作）
anyweb --cdp open "https://mp.weixin.qq.com/s/..."
sleep 3

# 2. 先提取视频 URL（必须在清理 DOM 之前！）
anyweb --cdp eval "
const videos = document.querySelectorAll('#js_content video');
const result = [];
videos.forEach(v => { if (v.src) result.push({src: v.src, poster: v.poster}); });
JSON.stringify(result);
"

# 3. 清理视频播放器 DOM + 提取 HTML
anyweb --cdp eval "
(function() {
    const root = document.querySelector('#js_content');
    if (!root) return '';
    root.querySelectorAll(
        '.js_tx_video_container, .video_card_container, ' +
        '.js_video_poster_container, .js_video_channel_container, ' +
        '.video-text, .video_fill_width, .video_card, ' +
        '.js_tx_video_channel_container, ' +
        'mpvoice, .rich_media_meta_list, ' +
        '.like_comment_wrp, .reward_area, .rich_media_tool'
    ).forEach(e => e.remove());
    root.querySelectorAll('video').forEach(v => {
        let p = v.closest('.video_area') || v.closest('section') || v.parentElement;
        if (p && p !== root) p.remove(); else v.remove();
    });
    return root.innerHTML;
})();
"
# → 保存到 /tmp/chat-digest/html-N.html

# 4. HTML → Markdown
python3 -c "
from markdownify import MarkdownConverter
class WC(MarkdownConverter):
    def convert_img(self, el, text, **kw):
        src = el.get('data-src') or el.get('src', '')
        if not src or 'data:image' in src or len(src) < 10: return ''
        src = src.split('#')[0].replace('&amp;', '&')
        return f'\n\n![{el.get(\"alt\",\"\")}]({src})\n\n'
    def convert_strong(self, el, text, **kw):
        return f'**{text.strip()}**' if text.strip() else ''
    def convert_b(self, el, text, **kw):
        return f'**{text.strip()}**' if text.strip() else ''
    def convert_em(self, el, text, **kw):
        return f'*{text.strip()}*' if text.strip() else ''
    def convert_section(self, el, text, **kw):
        # 微信用 section+inline style 做加粗，避免嵌套产生多余 ** 对
        style = el.get('style', '')
        if 'font-weight' in style and ('bold' in style or '700' in style):
            return f'**{text.strip()}**\n\n' if text.strip() else ''
        return text
with open('/tmp/chat-digest/html-N.html') as f: html = f.read()
md = WC(heading_style='atx', bullets='-').convert(html)
# 清理嵌套加粗（****text**** → **text**）
import re
md = re.sub(r'\*{2,}([^*]+?)\*{2,}', r'**\1**', md)
print(md)
"

# 5. 关闭页面
anyweb --cdp close
```

**为什么必须先清理 DOM 再提取 HTML**：微信嵌入视频的 DOM 包含播放器完整 UI（播放/暂停、进度条、倍速选择、全屏切换、关注状态、转载卡片等），markdownify 会把所有可见文字转为正文，产生「继续观看」「退出全屏」「分享点赞在看」「已同步到看一看」「视频详情」等大量垃圾行。

#### 腾讯新闻（news.qq.com）— 用 anyweb，选择器不同

同样需要清理视频 DOM，但内容选择器改为 `.content-article`：

```javascript
// 清理 JS 中的 '#js_content' 替换为 '.content-article'
const root = document.querySelector('.content-article');
```

其余流程（清理 DOM → 提取 HTML → markdownify）与微信相同。

#### 其他 URL — 用 tavily_extract

```python
tavily_extract(urls=["https://..."], include_images=True, format="markdown")
```

#### 小红书特殊处理

小红书图文笔记的正文在图片中，`tavily_extract` 和 `anyweb --cdp read` 只能拿到标签和评论。按优先级：

1. **搜索转载全文**（优先）：`tavily_search` 搜索笔记标题，公众号/新闻站通常有全文转载
2. **群内同源文章覆盖**：如果同一内容已有公众号版本，标注"同源内容"并跳过
3. **图片 OCR**（兜底）：`anyweb --cdp open` → 提取轮播图 img src → curl 下载 → Read 工具读图识别文字 → 拼接正文

小红书文字笔记可直接用 `anyweb read` 获取。短链接（`xhslink.com`）比长链接更可靠。

#### 来源类型判断

| URL 模式 | source_type | site_name 推断 |
|----------|-------------|---------------|
| `mp.weixin.qq.com` | 公众号 | 从页面 meta 或正文提取 |
| `github.com` | GitHub | 仓库名或组织名 |
| `*.github.io` | 项目主页 | 域名前缀 |
| `arxiv.org` | 论文 | arXiv |
| `xiaohongshu.com` / `xhslink.com` | 小红书 | 小红书 |
| `zhihu.com` | 知乎 | 知乎 |
| `news.qq.com` | 新闻 | 腾讯新闻 |
| 其他 | 网页 | 域名 |

**抓取失败处理**：记录 URL 但标记为"[抓取失败]"，不影响其他文章。

#### 清理文章末尾垃圾

微信公众号和新闻网站文章末尾通常有垃圾内容，必须截断删除。

**策略**：从末尾向前扫描，找到第一个垃圾行后截断。注意同样的文字可能出现在正文中间（如"16类交流群"、"1倍速"），只截断末尾的。

**经过实战验证的截断 pattern**（匹配到任意一个就从该行截断）：

```python
tail_junk_patterns = [
    r'^\*?\*?商务推广',
    r'^免责声明',
    r'^往期回顾',
    r'^社群情况',
    r'^Robotion Talk',
    r'^\*?\*?欢迎关注【',       # 末尾的"欢迎关注【XX】"
    r'^将持续分享',
    r'^欢迎.*点赞.*收藏.*在看',
    r'^可添加微信交流',
    r'^扫码关注公众号',
    r'^投稿、兼职、加群',
    r'^~.*技术交流群',
    r'^选择想要加入的交流群',
    r'^humanfive微信读者群',
    r'^END智猩猩',
    r'^智猩猩矩阵号',
    r'^欢迎点击.*阅读原文',
    r'^广告\s*$',
    r'借钱难有',
    r'^SK-II',
]
```

**残留视频 UI 文字兜底清理**（逐行过滤删除，只删独占一行的）：

```python
video_ui_patterns = [
    r'^已关注\s*$', r'^关注\s*$', r'^重播\s+分享\s+赞',
    r'^关闭\s*$', r'^\*?\*?观看更多', r'^更多\s*$',
    r'^\*?退出全屏', r'^\*?切换到竖屏', r'^human five已关注',
    r'^分享视频', r'^，时长\d', r'^\d+/\d+$',
    r'^\d{2}:\d{2}/\d{2}:\d{2}', r'^切换到横屏', r'^继续播放\s*$',
    r'^进度条', r'^\[播放\]\(javascript', r'^\d{2}:\d{2}\s*$',
    r'^\[倍速\]', r'^倍速播放', r'^\[\d+\.?\d*倍\]',
    r'^\[超清\]', r'^\[流畅\]', r'^\*全屏\*',
    r'^继续观看\s*$', r'^转载\s*$', r'^分享点赞在看',
    r'^已同步到看', r'^写下你的评论', r'^视频详情\s*$',
]
```

### Step 3.5: 英文文章翻译

**非中文文章（X/Twitter、GitHub、arXiv、英文博客等）入飞书知识库前必须翻译成中文。** 中文公众号文章跳过此步。

翻译后的文档结构：

```markdown
# 中文标题

## 作者简介
（作者背景、身份、代表作品，2-3 段。用 tavily_search 搜索）

---

## 译文
（完整中文翻译，保留原文结构、标题层级、列表格式）
（图片 ![alt](url) 穿插在译文对应位置，不要堆在末尾）

---

## 原文
（完整英文原文，图片同样穿插在原位）
```

**翻译规则**：
- 技术术语保留英文（如 World Model、VLA、Sim2Real）
- 专有名词首次出现附英文（如「世界模型（World Model）」）
- 代码块、命令、URL 不翻译
- 保留原文的标题层级和列表结构
- 翻译风格：准确、流畅、自然，不要翻译腔

### Step 4: 筛选 + 保存到知识库

#### 内容筛选

抓取完成后，先判断文章是否值得入库。知识库是沉淀知识用的，不是新闻存档。

**入库**（有知识价值）：技术解读、研究论文、深度分析、方法论、行业洞察、教程
**不入库**（新闻资讯）：签约/合作公告、融资新闻、政府活动、产品发布短讯、纯转载无深度的快讯

不入库的文章：
- 记录到 `processed.json`（`skipped: true, skip_reason: "新闻资讯"` 等）
- 日报汇总中仍然列出（标注为参考链接），但不生成知识库链接

#### 保存规则

**核心规则：已有文档只更新，绝不重复创建。**

维护 URL → doc_token 的映射关系（在会话中跟踪 + `processed.json` 持久化）。判断逻辑：
- `processed.json` 中已存在 → 跳过（Step 2 已过滤）
- 本次会话中已发布过的 URL → 有 doc_token → 走更新流程
- 全新 URL → 走首次发布流程

#### 首次发布

用共享脚本 `_shared/feishu_publish.py` 的 `publish_article_to_feishu()` 函数。传入的 markdown **必须保留 `![alt](url)` 格式的图片引用**，函数内部会自动提取图片、生成占位符、导入后下载插入。

```python
import os, sys
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

result = publish_article_to_feishu(
    md_path='/tmp/chat-digest/article-N.md',
    doc_title='文章标题',
    wiki_parent_node='<category_node_token>',
)
# result: {"doc_token": "...", "node_token": "...", "doc_url": "...", "images_inserted": N}
```

记录返回的 `doc_token` 和 `node_token`，后续更新必须用这些 token。

**发布后立即更新 `processed.json`**：每篇文章成功发布或跳过后，立即写入记录，避免中途失败导致重复处理。

```python
import json
pf = os.path.expanduser("~/.claude/data/chat-digest/processed.json")
with open(pf) as f: db = json.load(f)
db[url] = {
    "title": title,
    "doc_token": doc_token,       # 入库的填 token，跳过的填 null
    "category": category,
    "shared_by": shared_by,
    "date": date_str,
    "skipped": False,             # 或 True
    "skip_reason": None           # 或 "新闻资讯" / "同源重复"
}
with open(pf, "w") as f: json.dump(db, f, ensure_ascii=False, indent=2)
```

#### 更新已有文档

用 `lark-cli docs +update` 原地覆盖，**不要用 `feishu_publish.py`**（会创建新文档）。

更新流程分两步：先覆盖文本，再插入图片。

**Step 4a: 预处理 — 提取图片为占位符**

```python
images, cleaned_lines = [], []
for line in md.split('\n'):
    m = re.match(r"!\[([^\]]*)\]\((https?://[^)]+)\)", line.strip())
    if m:
        marker = f"IMG_PLACEHOLDER_{len(images)}"
        images.append({"url": m.group(2), "alt": m.group(1), "marker": marker})
        cleaned_lines.append(f"\n{marker}\n")
    else:
        cleaned_lines.append(line)
cleaned = '\n'.join(cleaned_lines)
```

**Step 4b: 覆盖文本内容**

```bash
lark-cli docs +update \
  --doc <doc_token> \
  --mode overwrite \
  --markdown "<cleaned_markdown_with_placeholders>" \
  --as bot
```

**Step 4c: 插入图片**（从后往前处理，避免 index 偏移）

```python
# 1. 获取所有 blocks
blocks = GET /docx/v1/documents/{doc}/blocks?page_size=500
children = [b for b in blocks if b["parent_id"] == doc_id and b["block_id"] != doc_id]

# 2. 对每张图片（从后往前）：
for img in reversed(images):
    # a. 找到占位符所在 block 的 index
    #    注意：飞书会把 IMG_PLACEHOLDER_0 拆成多个 text_run，必须 join 后匹配
    idx = find_block_index_by_text(children, img["marker"])

    # b. 下载图片
    curl -s -o /tmp/img.ext url

    # c. 删除占位符 block
    DELETE /docx/v1/documents/{doc}/blocks/{doc}/children/batch_delete
        {"start_index": idx, "end_index": idx + 1}

    # d. 创建空 image block
    POST /docx/v1/documents/{doc}/blocks/{doc}/children
        {"children": [{"block_type": 27, "image": {}}], "index": idx}
    → new_block_id

    # e. 上传图片
    POST /drive/v1/medias/upload_all
        file_name, parent_type=docx_image, parent_node=new_block_id, size, file
    → file_token

    # f. 绑定图片
    PATCH /docx/v1/documents/{doc}/blocks/{new_block_id}
        {"replace_image": {"token": file_token}}
```

**占位符匹配注意**：飞书导入后会把 `IMG_PLACEHOLDER_0` 拆分成 `IMG_` + `PLACEHOLDER_` + `0` 等多个 text_run。搜索时必须先拼接 block 的所有 text_run content：

```python
def get_block_text(block):
    elements = block.get("text", {}).get("elements", [])
    return "".join(e.get("text_run", {}).get("content", "") for e in elements)
```

**微信图片 URL 格式**：`mmbiz.qpic.cn` 的图片用 `wx_fmt=png|jpeg|gif` query 参数标识格式，不是文件扩展名：

```python
if "wx_fmt=jpeg" in url or "wx_fmt=jpg" in url: ext = "jpg"
elif "wx_fmt=png" in url: ext = "png"
elif "wx_fmt=gif" in url: ext = "gif"
else: ext = "png"  # fallback
```

#### 分类→节点映射

根据文章内容自动判断分类：

| 内容关键词 | 节点 | node_token |
|-----------|------|-----------|
| 机器人、具身、humanoid、dexterous | 具身动态 | `UzfowFW4sidwVdkZulecDOQ3nyd` |
| 大模型、LLM、GPT、Claude、推理 | 模型前沿 | `Za2NwAddOidZ1Ikm4CKcyHS7nSc` |
| 编程、Agent、MCP、Cursor、IDE | 编程范式 | `Nvrzwk0MAi5bPYkBucMcn1uJnkh` |
| AI 观点、未来、伦理、工作流 | AI思考 | `Me5EwNgwciDpKRk0YSPcKaWHnAo` |
| 创业、融资、产品、商业 | 商业观察 | `End8wv8oei8eQ6kr5pzcOpmVnyh` |
| 无法判断 | 模型前沿（默认） | `Za2NwAddOidZ1Ikm4CKcyHS7nSc` |

每篇文章保存前先生成临时 Markdown 文件 `/tmp/chat-digest/article-N.md`，格式：

```markdown
---
title: "文章标题"
source: "原始 URL"
source_type: "公众号"
site_name: "量子位"
shared_by: "李玮"
shared_at: "2026-04-03 00:35"
date: 2026-04-03
---

（文章正文 Markdown，包含 ![alt](url) 图片引用）
```

### Step 5: 生成汇总卡片

生成汇总消息，格式：

```
📋 华智全员群文章日报 YYYY-MM-DD

今日共分享 N 篇文章，已全部收录到行业前沿知识库。

━━━━━━━━━━━━━━━━━━

1. 📄 文章标题
   来源：公众号「量子位」
   分享人：李玮 | 09:13
   链接：https://...
   知识库：https://huazhi-ai.feishu.cn/docx/xxx

2. 📄 文章标题
   来源：GitHub
   分享人：邓子晗 | 15:30
   链接：https://...
   知识库：https://huazhi-ai.feishu.cn/docx/xxx

...

━━━━━━━━━━━━━━━━━━
分享人统计：李玮(3篇) 查志强(2篇) 邓子晗(1篇)
```

### Step 6: 推送

将汇总消息发送到华智全员群：

```bash
lark-cli im +messages-send \
  --chat-id oc_c7e33df4ad9f8d387ab7348395d99b0a \
  --type text \
  --text "汇总内容"
```

如果用户要求全员私信推送，额外调用 `feishu_broadcast.py`。

### Step 7: 清理临时文件

推送完成后，清理 `/tmp/chat-digest/` 中的临时文件：

```bash
rm -rf /tmp/chat-digest/html-*.html /tmp/chat-digest/md-*-raw.txt /tmp/chat-digest/article-*.md /tmp/chat-digest/img.*
```

**不清理** `~/.claude/data/chat-digest/processed.json`（持久化去重记录）。

---

## 配置常量

```yaml
chat_id: "oc_c7e33df4ad9f8d387ab7348395d99b0a"  # 华智全员群
space_id: "7559794508562251778"
category_nodes:
  具身动态: "UzfowFW4sidwVdkZulecDOQ3nyd"
  模型前沿: "Za2NwAddOidZ1Ikm4CKcyHS7nSc"
  编程范式: "Nvrzwk0MAi5bPYkBucMcn1uJnkh"
  AI思考: "Me5EwNgwciDpKRk0YSPcKaWHnAo"
  商业观察: "End8wv8oei8eQ6kr5pzcOpmVnyh"
```

## 注意事项

- **去重**：两层去重 — 同次运行内 URL 去重 + 跨次运行通过 `~/.claude/data/chat-digest/processed.json` 去重
- **内容筛选**：新闻资讯（签约、融资、政府活动）不入知识库，只在日报中列为参考链接
- **飞书链接跳过**：`feishu.cn` 域名的链接是内部文档，不需要抓取入库
- **短链接**：`xhslink.com` 等短链接直接传给 tavily，它会自动跟随重定向
- **临时目录**：每次运行前 `mkdir -p /tmp/chat-digest`，Step 7 自动清理
- **去重记录持久化**：`processed.json` 在 `~/.claude/data/chat-digest/` 下，不随临时目录清理
- **翻页**：群消息可能超过 50 条/天，需用 page_token 获取全部
- **时区**：时间参数用 `+08:00` 中国时区
- **首次发布传原始 markdown**：给 `publish_article_to_feishu()` 的文件保留 `![](url)` 图片引用，不要预处理成占位符
- **更新传占位符 markdown**：给 `lark-cli docs +update` 的内容用 `IMG_PLACEHOLDER_N` 替换图片，更新后手动插入图片
