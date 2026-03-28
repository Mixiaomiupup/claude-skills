---
name: wechat-publish
description: 发布文章到微信公众号（智涌MindSurge）。通过系统Chrome CDP自动化完成图片上传、草稿创建、内容更新和发布。当用户说"发到公众号"、"发微信"、"公众号发布"、"推送公众号"、"微信发表"，或任何涉及将内容发布到微信公众号的操作时使用。也适用于修改已发表文章的场景。
---

# 微信公众号发布

## 1. 架构概述

```
系统Chrome(CDP:9222) → 用户登录 → 获取Cookie/Token
    → 上传图片(API) → 创建/更新草稿(API) → 发表(CDP页面操作+扫码)
```

**为什么用系统 Chrome 而不是 Playwright/anyweb？** 微信后台检测自动化浏览器，Playwright 即使用 `channel="chrome"` 也会被识别，页面渲染空白。必须用用户自己的系统 Chrome 开启远程调试。

## 2. 启动浏览器与连接

### 2.1 启动系统 Chrome

```bash
open -a "Google Chrome" --args --remote-debugging-port=9222
```

如果 Chrome 已经打开，需要先完全退出再用上述命令启动，否则 `--remote-debugging-port` 不生效。

### 2.2 验证 CDP 连接

```bash
curl -s http://localhost:9222/json | python3 -c "
import sys,json
tabs=json.load(sys.stdin)
for t in tabs:
    print(f'{t[\"title\"][:50]} | {t[\"url\"][:80]}')
"
```

### 2.3 CDP 通信模板

所有页面操作通过 WebSocket + `websockets` 库：

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

```javascript
// 点击工具栏视频按钮
document.querySelector('.tpl_item.jsInsertIcon.video').click();

// 在弹出的对话框中点击"本地上传"
// 注意：这会打开新标签页，不是在当前页面内操作
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

1. **选封面**：点击推荐封面缩略图（`.cover__options__item`，跳过第一个空白项），会弹出封面编辑器
2. **完成裁剪**：在封面编辑器中直接点击"完成"按钮
3. **填标题**：设置 `input[name=title]` 的值（使用 `HTMLInputElement.prototype.value.set` + dispatch input 事件）
4. **勾选同意**：点击"我已阅读并同意"checkbox
5. **保存**：点击"保存"按钮，页面跳转到视频素材列表表示成功

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

### 4b.6 调整视频位置

视频默认插入到光标位置（通常是文章开头）。需要通过 ProseMirror DOM 移动：

```javascript
var pm = document.querySelector(".ProseMirror");
var videoSection = pm.querySelector("section[nodeleaf]"); // 视频元素
var targetImg = pm.querySelector("img[src*='目标图片URL片段']");
var imgSection = targetImg.parentElement; // 找到包含目标图片的 section
imgSection.parentNode.insertBefore(videoSection, imgSection.nextSibling);
```

**注意**：编辑器是 ProseMirror（不是 UEditor），内容在 `.ProseMirror` 元素中，不在 iframe 里。`UE.instants` 为空。

### 4b.7 视频上传约束

| 约束 | 说明 |
|------|------|
| 文件大小 | ≤ 200MB |
| 时长 | ≤ 1 小时 |
| 格式 | mp4 等主流格式 |
| 封面必选 | 不选封面无法保存 |
| 转码时间 | 上传后素材库可能短暂显示"暂无视频"，刷新即可 |

## 5. Markdown → 微信 HTML

### 5.1 HTML 结构模板

```html
<section style="background-color:#ffffff;padding:12px 8px;margin:0;border-radius:0;">

<h2 style="font-size:20px;font-weight:bold;color:#1a1a1a;margin:28px 0 14px;padding-bottom:8px;border-bottom:3px solid #07c160;">标题</h2>

<p style="font-size:16px;line-height:1.8;margin:16px 0 6px;color:#1a1a1a;"><strong>• 条目标题</strong></p>

<section style="border-left:3px solid #e8a87c;padding:10px 14px;margin:6px 0 10px;background-color:#fdf5ef;border-radius:0 6px 6px 0;font-size:14px;color:#555;line-height:1.8;">
引用/摘要内容
</section>

<p style="margin:6px 0 10px;padding:8px 10px;border:1px dashed #ccc;border-radius:6px;font-size:12px;color:#999;word-break:break-all;">
https://x.com/example/status/123456
</p>

<p style="text-align:center;margin:12px 0;">
<img src="CDN_URL" style="max-width:100%;height:auto;border-radius:8px;" />
</p>

</section>
```

### 5.2 关键约束

| 约束 | 说明 |
|------|------|
| **禁止 `margin:-16px`** | 负 margin 导致内容溢出手机屏幕，是手机端显示异常的根本原因。始终用 `margin:0` |
| **外链不可点击** | 微信过滤正文中的 `<a>` 外链。改为虚线框内展示纯文本 URL |
| **图片必须用 CDN URL** | 只有 `mmbiz.qpic.cn` 域名的图片才显示 |
| **图片加 max-width:100%** | 防止图片溢出手机屏幕 |
| **不要用 text-align:justify** | 移动端会导致字间距异常放大 |

### 5.3 深色模式（可选）

两种方案：
- **推荐**：推文截图直接用深色模式截取，省去适配工作
- **手动适配**：在元素上添加 `data-darkmode-bgcolor-{id}` 和 `data-darkmode-color-{id}` 属性

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

4. 可能出现第二个确认框（"继续发表"），同样点击确认

5. **用户扫码验证** — 提示用户扫码，等待完成

### 7.2 查找对话框按钮的模式

```javascript
const dialogs = document.querySelectorAll('.weui-desktop-dialog__wrp');
for (let d of dialogs) {
    if (d.offsetHeight > 0) {
        const btns = d.querySelectorAll('button');
        for (let b of btns) {
            if (b.className.includes('primary') && b.offsetHeight > 0) {
                b.click(); break;
            }
        }
    }
}
```

## 8. 修改已发表文章

- 每篇最多修改 **3 次**
- 入口：发表记录页面 → hover 文章行右侧 → "改"按钮（需 CDP `Input.dispatchMouseEvent` 模拟 hover）
- **只能修改文字内容，不能修改 CSS 样式**
- 微信通过内部状态追踪修改，直接改 DOM 无效（提示"检测到内容没有修改"）
- 需要改样式 → 删除已发表文章后重新发布新草稿

## 9. 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 手机端文字被遮挡/溢出 | 外层 section `margin:-16px` | 改为 `margin:0` |
| 编辑器粘贴后变纯文本 | ProseMirror 过滤 HTML | 用 API `operate_appmsg` 写入 |
| 图片不显示 | 使用了外部图片 URL | 先上传到微信 CDN |
| 链接点不了 | 微信过滤外链 | 展示为纯文本 URL |
| API 发布返回 ret=2 | 需要扫码验证 | 通过 CDP 页面操作发布 |
| Playwright 页面空白 | 微信检测自动化浏览器 | 用系统 Chrome + CDP |
| JS 变量名冲突 | CDP 多次执行同一页面 | 用 IIFE 包裹 |
