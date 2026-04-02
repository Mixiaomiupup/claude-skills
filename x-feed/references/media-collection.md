# Media Collection Reference

封面图生成、推文截图、视频下载的详细实现。在 Digest Mode Step 7.5 中使用。

---

## 1. 封面图生成

使用 `gemini-image` skill 生成日报封面，结合当日热点内容。

**风格**：手绘信息图风格（baoyu-inspired），5 个话题卡片，粉彩配色，wobble 线条。

```bash
# 生成封面（不含中文文字，避免 AI 文字错误）
python3 ~/.claude/skills/gemini-image/scripts/gemini_image.py generate "<prompt>" \
  -o ~/Downloads/x-daily/YYYY-MM-DD/cover-raw.png
```

**AI 中文文字已知问题**：Gemini 生成中文经常写错字。解决方案：prompt 中 "NO Chinese text"，用 Pillow 叠加正确文字（`STHeiti Medium.ttc` 简体字体，勿用 Hiragino Sans 繁体）。

---

## 2. 推文截图

使用 anyweb 截取推文**仅正文区域**（不含侧边栏、顶栏、回复区）。

### 选取规则

- **有视频的推文不截图**：如果该推文已下载了视频（Step 3 视频下载），则跳过截图，视频比截图更有价值
- 只截取没有视频的 Top 5 高互动推文

### 核心流程

1. `anyweb open "https://x.com/{user}/status/{id}"` 打开推文
2. **展开全文**：检查是否有"显示更多"/"Show more"按钮，若有则点击展开：
   ```javascript
   const showMore = document.querySelector('[data-testid="tweet-text-show-more-link"]');
   if (showMore) showMore.click();
   ```
   **不展开就截图会导致内容不完整**（半张图），这是常见错误。
3. 启用深色模式：
   `anyweb eval "document.cookie='night_mode=2;domain=.x.com;path=/'; location.reload()"`
4. `anyweb eval "<HIDE_JS>"` 隐藏非正文元素并返回正文边界
5. `anyweb screenshot` 全页截图
6. Pillow 裁切到正文边界

### HIDE_JS 要点

```javascript
// 隐藏：sidebarColumn, header[role="banner"], BottomBar, dialog
// 约束：primaryColumn maxWidth=620px, margin=0 auto
// 隐藏回复：articles[1:] display=none
// 返回：JSON.stringify(articles[0].getBoundingClientRect())
```

### Pillow 裁切：先检测 devicePixelRatio

```bash
# 1. 获取实际 viewport 和 dpr
anyweb eval 'JSON.stringify({dpr: window.devicePixelRatio, vw: window.innerWidth})'
# 典型结果: {"dpr":1,"vw":1536}
```

```python
# 2. 用 dpr 计算缩放因子，不要硬编码 viewport 宽度
#    错误写法: scale = img.width / 1280  ← 猜测的值，会导致裁切偏移
#    正确写法:
scale = dpr  # dpr=1 时坐标直接映射，dpr=2 时坐标 ×2
left = max(0, int(bounds['left'] * scale) - 5)
top = max(0, int(bounds['top'] * scale) - 5)
right = min(img.width, int(bounds['right'] * scale) + 5)
bottom = min(img.height, int(bounds['bottom'] * scale) + 15)
cropped = img.crop((left, top, right, bottom))
```

**已知坑**：anyweb 默认 viewport 为 1536x864（非 1280），且 dpr=1。如果用 `img.width / 1280` 算 scale 会得到 1.2，导致所有坐标右移 20%。

---

## 3. 视频下载

### 3.1 使用 yt-dlp 下载

```bash
yt-dlp --cookies-from-browser chrome -f "bestvideo+bestaudio/best" \
  -o "$HOME/Downloads/x-daily/YYYY-MM-DD/tweet-%(id)s.%(ext)s" \
  "https://x.com/{user}/status/{tweet_id}"
```

**Prerequisites**: `brew install yt-dlp ffmpeg`

### 3.2 具身智能视频优先策略

具身智能板块的视频（机器人 demo、工厂部署、运动控制展示）是最有传播力的内容，执行更积极的下载策略：

- **具身智能板块**：所有标记 🎬 的推文一律下载视频，不设互动量门槛
- **其他板块**：仅互动量 Top 5 且含视频的推文下载

### 3.3 嵌入 Obsidian

1. 复制图片到 `~/Documents/obsidian/mixiaomi/attachments/`：
   - `cover.png` → `智涌日报-YYYY-MM-DD-cover.png`
   - `tweet-{id}.png` 直接复制

2. 更新日报 Markdown：
   - frontmatter: `cover: "智涌日报-YYYY-MM-DD-cover.png"`
   - 标题下: `![[智涌日报-YYYY-MM-DD-cover.png]]`
   - 每条推文来源链接后: `![[tweet-{id}.png]]`

---

## 4. 媒体目录与清理

```
~/Downloads/x-daily/YYYY-MM-DD/
├── cover.png          # 最终封面（Pillow 叠加文字后）
├── cover-raw.png      # Gemini 原始输出（发布前删除）
├── tweet-{id}.png     # 推文截图（仅正文，裁切后）
├── tweet-full-{id}.png # 全页截图（发布前删除）
└── tweet-{id}.mp4     # 视频文件（tweet- 前缀匹配 feishu_publish.py glob）
```

**发布前必须清理**：删除 `cover-raw.png` 和 `tweet-full-*.png`，否则会被 `publish_to_feishu()` 的 `media_dir` 参数一并上传到飞书。
