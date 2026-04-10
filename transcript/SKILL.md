---
name: transcript
description: "Extract subtitles/transcripts from video URLs (YouTube, Bilibili) and organize by chapters into Obsidian vault. Use when user provides a video URL and says '提取字幕', '整理字幕', '视频笔记', 'transcript', '字幕提取', or wants to extract and organize video content. Also use when user gives a YouTube/Bilibili link and mentions chapters, subtitles, or transcription. Future: podcast support."
---

# Transcript

从视频 URL 提取字幕，按章节整理，存入 Obsidian vault。

## 支持平台

| 平台 | 提取方式 | 字幕来源 |
|------|---------|---------|
| YouTube | yt-dlp | 自动生成 / 手动上传 |
| Bilibili | yt-dlp | 自动生成 / CC字幕 |
| 播客 | *待扩展* | whisper 等 |

## 工作流

### 1. 提取字幕

```bash
python3 ~/.claude/skills/transcript/scripts/extract.py "<URL>" \
  --lang "en-orig,en,zh-Hans,zh" \
  --out-dir "<output_dir>"
```

脚本自动完成：
- 获取视频元数据（标题、作者、时长、章节）
- 下载字幕（按语言偏好回退）
- 去重清洗（自动字幕有大量重复行）
- 按章节分段组织
- 生成带 frontmatter 的 Markdown + 保留原始 SRT

### 2. 章节来源

优先级：
1. **视频元数据**：yt-dlp 自动从视频描述提取章节（大多数 YouTube 视频）
2. **用户提供**：用户给截图或文本列出章节 → 保存为 JSON，传 `--chapters-json`
3. **无章节**：整个视频作为单一段落处理

用户提供章节的 JSON 格式：
```json
[
  {"start_time": 0, "title": "Introduction"},
  {"start_time": 315, "title": "Setup"},
  {"start_time": 610, "title": "Demo"}
]
```

### 3. 存入 Obsidian

提取完成后，走 `article-gen` 的 repost 流程存入 vault：
- 分类到 `raw/{category}/` 目录
- 补充 frontmatter（category、tags、summary）
- type 设为 `transcript`（article-gen 未定义此 type 时当作 `notes` 处理）
- 标记 index.md 待处理

如果用户只要字幕不存 vault，直接用 `--out-dir` 指定输出目录。

### 4. 语言处理

- `--lang` 参数按逗号分隔，依次尝试
- YouTube 默认: `en-orig,en,zh-Hans,zh`
- Bilibili 默认: `zh,zh-Hans,en`
- 用户可指定其他语言

## 常见场景

| 用户说 | 做什么 |
|--------|--------|
| "提取这个视频的字幕" + URL | 提取 → 按章节整理 → 输出 |
| "整理字幕存ob" + URL | 提取 → 整理 → article-gen repost 到 vault |
| "这个视频讲了什么" + URL | 提取 → 整理 → 生成摘要 |
| URL + 章节截图 | 从截图解析章节 → 提取 → 按章节整理 |

## 注意事项

- yt-dlp 需要已安装（`brew install yt-dlp`）
- Bilibili 字幕可能需要登录态（cookies），提取失败时提示用户
- 自动字幕质量参差，提取后建议用户检查关键段落
- 长视频（>2h）字幕文件可能很大，脚本已做去重处理
