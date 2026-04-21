---
name: wechat-publish
description: 发布文章到微信公众号（智涌MindSurge）。通过系统Edge CDP自动化完成图片上传、草稿创建、内容更新和发布。当用户说"发到公众号"、"发微信"、"公众号发布"、"推送公众号"、"微信发表"，或任何涉及将内容发布到微信公众号的操作时使用。也适用于修改已发表文章的场景。
---

# 微信公众号发布

## 1. 架构概述

```
scripts/publish.py 日报.md          ← 一键发布入口
    ├── scripts/auth.py             ← CDP 取 cookie + token
    ├── scripts/upload.py           ← 上传图片到微信 CDN
    ├── ~/.claude/scripts/md2pub.py ← MD → 微信 HTML（零依赖）
    └── scripts/draft.py            ← 创建/更新草稿 API
```

**一键发布**（推荐）:
```bash
python3 ~/.claude/skills/wechat-publish/scripts/publish.py 日报.md
```

**单独调用各步骤**:
```bash
# 1. 取凭证
python3 scripts/auth.py --port 9224 > /tmp/wx_creds.json

# 2. 上传图片
python3 scripts/upload.py --creds /tmp/wx_creds.json cover.png tweet.png > /tmp/cdn_map.json

# 3. 转换 MD → HTML
python3 ~/.claude/scripts/md2pub.py input.md --body-only -o /tmp/body.html

# 4. 创建草稿
python3 scripts/draft.py --creds /tmp/wx_creds.json --title "标题" --content /tmp/body.html
```

**为什么用系统 Edge（本 skill 例外）？** 微信后台检测自动化浏览器，Playwright 即使用 `channel="chrome"` 也会被识别，页面渲染空白。其他 skill 的 `anyweb --cdp` 已改用独立 Chrome，但 wechat-publish 仍需 CDP 直连系统 Edge 浏览器 -- 微信的反自动化检测专门针对非 Edge 浏览器，Edge 与用户正常使用的浏览器完全一致不会被检测。Edge 需以 `--remote-debugging-port=9222` 启动。这是所有 skill 中唯一保留 Edge CDP 的。

## 2. 连接浏览器

### 2.1 使用 anyweb --cdp（推荐）

```bash
# 打开微信后台（复用系统 Edge 登录态）
anyweb --cdp open "https://mp.weixin.qq.com/"
```

**前提**：Edge 需以 `--remote-debugging-port=9222` 启动。

### 2.2 anyweb --cdp 常用操作

```bash
# 导航
anyweb --cdp open "URL"

# 执行 JS（等价于 CDP Runtime.evaluate）
anyweb --cdp eval "document.title"

# 截图
anyweb --cdp screenshot

# 页面状态
anyweb --cdp state --ax
```

### 2.3 需要原始 CDP 的操作（回退）

以下操作超出 anyweb CLI 能力，仍需通过 CDP 直接连接（Edge 已以 `--remote-debugging-port=9222` 启动）：
- `DOM.setFileInputFiles`（视频上传文件注入）
- `Network.getCookies`（获取 httpOnly cookie）

回退时启动方式：
```bash
# Edge 需以调试端口启动（通常已配置）
open -a "Microsoft Edge" --args --remote-debugging-port=9222
```

CDP 通信模板（仅在需要原始 CDP 时使用）：

```python
import asyncio, json, websockets, urllib.request

async def run():
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    ws_url = [t['webSocketDebuggerUrl'] for t in tabs if 'KEYWORD' in t.get('title','')][0]

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{
            'expression': 'document.title'
        }}))
        r = json.loads(await ws.recv())
        print(r.get('result',{}).get('result',{}).get('value',''))

asyncio.run(run())
```

注意：多次在同一页面执行 JS 时，用 IIFE `(() => { ... })()` 包裹避免变量名冲突。

## 3. 用户登录与获取凭证

1. 通过 CDP 导航到 `https://mp.weixin.qq.com/`
2. **让用户手动登录**（扫码）
3. 登录后从 URL 提取 `token`，从 CDP 提取 cookies：

```python
# 获取 Token（从任意后台页面 URL）
# URL 格式: https://mp.weixin.qq.com/cgi-bin/home?...&token=XXXXXXXXX

# 获取 Cookies
await ws.send(json.dumps({'id':1,'method':'Network.getCookies'}))
r = json.loads(await ws.recv())
cookies = r.get('result',{}).get('cookies',[])
cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies if 'mp.weixin' in c.get('domain',''))
```

将 cookie_str 和 token 保存到 `/tmp/wx_cookies.txt` 和变量中，后续 API 调用使用。

## 4. 上传图片

所有图片（封面、推文截图）必须先上传到微信 CDN，外部图片链接不显示。

```bash
curl -s -X POST "https://mp.weixin.qq.com/cgi-bin/filetransfer?action=upload_material&f=json&writetype=doublewrite&groupid=1&token=${TOKEN}&lang=zh_CN&t=ajax-editor-upload-loc-img" \
  -H "Cookie: ${COOKIE}" \
  -F "file=@${IMAGE_PATH};type=image/png"
```

返回 `cdn_url`（`https://mmbiz.qpic.cn/...`），保存映射关系到 `/tmp/wx_image_urls.json`。

## 4b. 上传视频

视频不能通过图片上传 API 上传，必须通过编辑器页面操作。**图片上传接口不支持视频文件。**

### 4b.1 流程概述

```
编辑器工具栏"视频" → 素材库对话框 → "本地上传"(打开新页面)
    → 新页面注入文件 → 选封面 → 保存 → 回编辑器选择视频 → 插入
```

### 4b.2 打开视频上传页

在文章编辑器中点击工具栏的"视频"按钮，弹出"选择视频"对话框，点击"本地上传"会打开一个**新标签页**（`videomsg_edit`）。

**注意**：headless 环境下 `window.open` 可能被拦截。用拦截器捕获 URL 后手动导航：

```javascript
// 1. 拦截 window.open
window.__capturedUrl = null;
window._origOpen = window.open;
window.open = function(url) { window.__capturedUrl = url; return null; };

// 2. 点击"本地上传"
document.querySelector('.tpl_item.jsInsertIcon.video').click();
// 等待对话框出现后点击"本地上传"按钮

// 3. 读取捕获的 URL，手动在新 tab 打开
// window.__capturedUrl → 包含 videomsg_edit 的 URL
```

### 4b.3 在视频上传页注入文件

新标签页 URL 包含 `videomsg_edit`。页面中有一个隐藏的 `<input type="file" accept="video/*" name="vid">`。

```python
# 1. 找到视频上传页的 tab
video_tab = [t for t in tabs if 'videomsg_edit' in t.get('url','')][0]

# 2. 通过 Runtime 找到 file input 的 objectId
await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{
    'expression': 'document.querySelector("input[accept=\\"video/*\\"]")'
}}))
obj_id = response['result']['result']['objectId']

# 3. 通过 DOM.setFileInputFiles 注入视频文件
await ws.send(json.dumps({'id':2,'method':'DOM.setFileInputFiles','params':{
    'files': ['/path/to/video.mp4'],
    'objectId': obj_id
}}))
```

**关键**：必须用 `objectId`（而非 `nodeId`/`backendNodeId`），因为 DOM.enable 后的消息顺序会导致 nodeId 方式不可靠。

### 4b.4 选封面 + 填标题 + 保存

上传完成后（轮询 `.weui-desktop-upload__file__progress` 的 `style.width` 到 `100%`）：

1. **选封面**：**必须等待封面缩略图加载**（至少 15 秒），然后点击推荐封面缩略图（`.cover__options__item`，跳过第一个空白项）。如果缩略图未加载就点击会导致保存失败。**用重试循环**：最多 5 次，每次间隔 5 秒。
2. **完成裁剪**：在封面编辑器中直接点击"完成"按钮
3. **填标题**：设置 `input[name=title]` 的值（使用 `HTMLInputElement.prototype.value.set` + dispatch input 事件）
4. **勾选同意**：点击"我已阅读并同意"checkbox
5. **保存**：点击"保存"按钮，页面跳转到视频素材列表表示成功

**视频审核/转码**：上传保存后视频进入"转码中"→"审核中"状态。**审核通过前无法插入文章**。轮询素材库列表，只使用状态为"已通过"的视频。未通过的跳过，不要阻塞发布流程。

### 4b.5 在文章中插入已上传的视频

回到文章编辑器，重新打开视频对话框：

```javascript
// 1. 点击视频按钮打开对话框
document.querySelector('.tpl_item.jsInsertIcon.video').click();

// 2. 视频出现在素材库列表中（.more-video__item）
// 3. 选中视频：点击隐藏的 checkbox（需要先强制显示）
var item = document.querySelector('.more-video__item');
var checkLabel = item.querySelector('.weui-desktop-form__check-label');
checkLabel.style.cssText = 'display:block !important; visibility:visible !important;';
checkLabel.click();
// 验证：footer 显示 "已选择 1/10条视频"

// 4. 点击确定插入
```

### 4b.6 视频位置：Marker 技术（推荐）

视频默认插入到光标位置。用 **marker 占位符**精确控制视频应出现的位置：

**Step 1**：在 HTML 中为每个视频插入唯一占位符（在创建草稿前）：

```python
def video_marker(name):
    return f'<p style="text-align:center;margin:12px 0;padding:16px;background-color:#f0f0f0;border-radius:8px;font-size:14px;color:#666;">🎬 [{name}] 视频位置</p>'
```

把 marker 放在对应新闻条目的来源链接之后。**注意**：不要用 `id` 属性，API 创建草稿时会被 strip。

**Step 2**：草稿创建后，按顺序处理每个视频：
1. 在 ProseMirror 中找到 marker 文本：`textContent.includes('[BD] 视频位置')`
2. 将光标设置到 marker 元素：`window.getSelection().collapse(markerNode, 0)`
3. 打开视频对话框，选中对应视频，插入 → 视频出现在光标位置（即 marker 旁边）
4. 删除 marker 元素

**Step 3**：验证所有视频已正确放置。

**注意**：
- 编辑器是 ProseMirror（不是 UEditor），内容在 `.ProseMirror` 元素中，不在 iframe 里
- 每次只插入一个视频，按 marker 顺序逐个处理
- 如果视频还在审核中，跳过对应 marker（留白或删除 marker）

### 4b.7 视频上传约束

| 约束 | 说明 |
|------|------|
| 文件大小 | ≤ 200MB |
| 时长 | ≤ 1 小时 |
| 格式 | mp4 等主流格式 |
| 封面必选 | 不选封面无法保存 |
| 转码时间 | 上传后素材库可能短暂显示"暂无视频"，刷新即可 |

## 5. Markdown → 微信 HTML

### 5.1 使用 md2pub 脚本（推荐）

**脚本位置**: `~/.claude/scripts/md2pub.py`（零外部依赖，纯 Python 标准库）

```bash
# 生成 body HTML（用于微信 API content0 字段）
python3 ~/.claude/scripts/md2pub.py input.md --body-only -o /tmp/body.html

# 浏览器预览
python3 ~/.claude/scripts/md2pub.py input.md --preview

# 切换主题
python3 ~/.claude/scripts/md2pub.py input.md --theme green --body-only
```

**脚本内部流程**:

| 步骤 | 函数 | 做什么 |
|------|------|--------|
| 预处理 | `preprocess()` | 去 frontmatter/Obsidian 语法；blockquote 中 `[text](url)` → `text: url`，管道分隔拆多行 |
| 解析 | `parse_blocks()` | 逐行解析 markdown → block 结构体列表 |
| 渲染 | `render_blocks()` + `render_inline()` | block → 带内联 CSS 的 HTML，按主题配色 |
| 组装 | `convert()` | 包裹容器，输出最终 HTML |

**也可在 Python 中直接调用**:

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("md2pub", str(Path.home() / ".claude/scripts/md2pub.py"))
md2pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md2pub)

html_body = md2pub.convert(markdown_text, theme_name="default")
```

### 5.2 来源链接处理

x-feed 日报的来源格式 `> [来源](URL) | [官方公告](URL)` 经 md2pub `preprocess()` 自动转换：

| 输入（markdown） | 输出（HTML 纯文本） |
|------------------|---------------------|
| `> [CGTN 报道](URL) \| [新华社](URL)` | 两行：`CGTN 报道: URL` / `新华社: URL` |
| `> 来源: https://x.com/...` | 原样保留 `来源: https://x.com/...` |
| `> [GlobeNewswire](URL)` | `GlobeNewswire: URL` |

**不需要修改 x-feed 模板**——md2pub 兼容所有现有格式。微信端外链不可点，但 URL 作为纯文本可见。

### 5.3 关键约束

| 约束 | 说明 |
|------|------|
| **禁止 `margin:-16px`** | 负 margin 导致内容溢出手机屏幕。始终用 `margin:0` |
| **外链不可点击** | 微信过滤 `<a>` 外链。md2pub 预处理阶段自动将 blockquote 中的链接展开为纯文本 URL |
| **图片必须用 CDN URL** | 只有 `mmbiz.qpic.cn` 域名的图片才显示 |
| **图片加 max-width:100%** | 防止图片溢出手机屏幕 |
| **不要用 text-align:justify** | 移动端会导致字间距异常放大 |
| **有视频不截图** | 推文已有视频下载的，跳过该推文截图 |
| **推文截图裁剪** | JS 隐藏侧边栏 → 截图 → PIL 裁剪正文区域（约 750px 宽） |
| **视频用 marker 定位** | HTML 中放占位符，插入视频前设置光标到 marker 处（见 4b.6） |
| **单次引用 ≤ 300 字** | 微信公众号单个 `<blockquote>` 不得超过 300 字。描述文本放正文，仅来源链接和 💡 点评用引用格式。md2pub.py 会对超标引用打印警告 |
| **不加数据来源 footer** | 文章末尾不放"数据来源: Grok Search..."等 meta 信息 |

### 5.4 深色模式

md2pub 的样式设计为**深浅模式兼容**:
- blockquote 无背景色，只用左边框
- H2 标题无背景色，用底部彩色边框
- 不依赖 `data-darkmode-*` 属性
- 推文截图建议用深色模式截取

## 6. 创建/更新草稿

```python
import urllib.request, urllib.parse, json

url = f"https://mp.weixin.qq.com/cgi-bin/operate_appmsg?t=ajax-response&sub=create&type=77&token={token}&lang=zh_CN"
# 更新用 sub=update，并加 AppMsgId 参数

data = urllib.parse.urlencode({
    'token': token,
    'lang': 'zh_CN',
    'f': 'json',
    'ajax': '1',
    'AppMsgId': '',          # 更新时填已有草稿 ID
    'count': '1',
    'title0': '文章标题',
    'content0': html_content,
    'digest0': '文章摘要（120字内）',
    'author0': '智涌MindSurge',
    'writerid0': '0',
    'fileid0': 'COVER_FILE_ID',
    'cdn_url0': 'COVER_CDN_URL',
    'cdn_235_1_url0': 'COVER_CDN_URL',
    'cdn_1_1_url0': 'COVER_CDN_URL',
    'need_open_comment0': '1',
}).encode('utf-8')

req = urllib.request.Request(url, data=data, method='POST')
req.add_header('Cookie', cookie_str)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
# result['base_resp']['ret'] == 0 表示成功
# result['appMsgId'] 为草稿 ID
```

**注意**：ProseMirror 编辑器会把直接设置的 innerHTML 当纯文本处理，必须通过 API 写入内容。

## 7. 发布

发布必须通过页面操作 + 扫码验证，纯 API（`sub=publish`）返回 ret=2 不可用。

### 7.1 流程

1. CDP 导航到草稿编辑页面：
   ```
   https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&type=77&AppMsgId={id}&token={token}&lang=zh_CN
   ```

2. 通过 CDP 点击"发表"按钮：
   ```javascript
   const btns = document.querySelectorAll('button');
   for (let b of btns) {
       if (b.textContent.trim() === '发表' && b.offsetHeight > 0) { b.click(); break; }
   }
   ```

3. 等待确认对话框，点击对话框内的"发表"主按钮（`.primary` class）

4. 可能出现第二个确认框（"继续发表"）— **常规 `.click()` 和 CDP 鼠标事件对此按钮无效**，必须通过 React 内部 onClick：

```javascript
const primaryBtn = /* 找到 .primary 按钮 */;
const propsKey = Object.keys(primaryBtn).find(k => k.startsWith('__reactProps'));
if (propsKey && primaryBtn[propsKey].onClick) {
    primaryBtn[propsKey].onClick({
        preventDefault: () => {},
        stopPropagation: () => {},
        nativeEvent: new MouseEvent('click'),
        target: primaryBtn, currentTarget: primaryBtn
    });
}
```

5. **用户扫码验证** — 提示用户扫码，等待完成

### 7.2 查找对话框按钮的模式

```javascript
// 优先用 React onClick，fallback 到 .click()
const dialogs = document.querySelectorAll('.weui-desktop-dialog__wrp');
for (let d of dialogs) {
    if (d.offsetHeight > 0) {
        const btns = d.querySelectorAll('button');
        for (let b of btns) {
            if (b.className.includes('primary') && b.offsetHeight > 0) {
                const rk = Object.keys(b).find(k => k.startsWith('__reactProps'));
                if (rk && b[rk].onClick) {
                    b[rk].onClick({preventDefault:()=>{},stopPropagation:()=>{},
                        nativeEvent:new MouseEvent('click'),target:b,currentTarget:b});
                } else {
                    b.click();
                }
                break;
            }
        }
    }
}
```

## 8. 修改已发表文章

### 8.1 限制

- 每篇最多修改 **3 次**
- 支持修改：标题、正文文字、图片、视频、封面及摘要
- **不能修改 CSS 样式**（需要改样式 → 删除后重新发布）
- 修改页面用 **UEditor**（不是 ProseMirror），且是**逐元素操作**：点击某段落/图片弹出"替换"/"删除"选项
- 直接改 DOM 无效（微信内部状态追踪）

### 8.2 入口

发表记录页面 → hover 文章行 → 右侧出现3个按钮：统计(图表icon) / **改**(文字) / 更多(...)

```
URL: /cgi-bin/appmsgpublish?sub=list&...
hover 后 "改" 按钮位于行右侧中间位置（3个按钮中第2个）
点击后跳转: /cgi-bin/masssendmodify?action=edit_new&appmsgid=XXX&...
```

### 8.3 适用场景

- 修改错别字、更新数据 → 适合用修改
- 大面积内容替换（加截图、加视频、改排版）→ **不适合**，应删除后重新发布

## 9. 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 手机端文字被遮挡/溢出 | 外层 section `margin:-16px` | 改为 `margin:0` |
| 编辑器粘贴后变纯文本 | ProseMirror 过滤 HTML | 用 API `operate_appmsg` 写入 |
| 图片不显示 | 使用了外部图片 URL | 先上传到微信 CDN |
| 链接点不了 | 微信过滤外链 | 展示为纯文本 URL |
| API 发布返回 ret=2 | 需要扫码验证 | 通过 CDP 页面操作发布 |
| Playwright 页面空白 | 微信检测自动化浏览器 | 用 `anyweb --cdp` 直连系统 Edge |
| JS 变量名冲突 | CDP 多次执行同一页面 | 用 IIFE 包裹 |
| 视频全堆在文章开头/末尾 | 未用 marker 定位，视频插入到默认光标位置 | 用 marker 占位符技术（见 4b.6） |
| 视频封面选不了 | 缩略图未加载就点击 | 等 15 秒 + 重试循环（见 4b.4） |
| "继续发表"按钮点不动 | React 组件拦截了原生事件 | 用 `__reactProps` 调 onClick（见 7.1） |
| 视频"暂无" | 刚上传还在转码/审核 | 等待审核通过，跳过未通过的 |
