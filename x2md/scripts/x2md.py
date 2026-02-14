#!/usr/bin/env python3
"""
x2md - 将 X/Twitter 推文或长文（Article）转换为 Markdown

用法:
    python3 x2md.py <tweet_url>
    python3 x2md.py https://x.com/dotey/status/2021711269426765853

输出: 在当前目录生成 .md 文件，同时复制到剪贴板（macOS）
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


def extract_tweet_id(url: str) -> str:
    """从推文 URL 中提取 tweet ID"""
    match = re.search(r"/status/(\d+)", url)
    if not match:
        print(f"错误: 无法从 URL 中提取推文 ID: {url}")
        sys.exit(1)
    return match.group(1)


def extract_username(url: str) -> str:
    """从推文 URL 中提取用户名"""
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status", url)
    if not match:
        return "unknown"
    return match.group(1)


def fetch_tweet(tweet_id: str) -> dict:
    """通过 fxtwitter API 获取推文数据"""
    api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
    req = Request(api_url, headers={"User-Agent": "x2md/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") != 200:
                print(f"API 返回错误: {data}")
                sys.exit(1)
            return data.get("tweet", {})
    except URLError as e:
        print(f"请求失败: {e}")
        sys.exit(1)


def apply_inline_styles(text: str, styles: list) -> str:
    """将行内样式（加粗、斜体）应用到文本"""
    if not styles:
        return text

    # 按 offset 降序排列，从后往前插入标记避免偏移
    sorted_styles = sorted(styles, key=lambda s: s["offset"], reverse=True)
    chars = list(text)

    for style in sorted_styles:
        offset = style["offset"]
        length = style["length"]
        end = offset + length
        style_type = style.get("style", "")

        if style_type == "Bold":
            marker = "**"
        elif style_type == "Italic":
            marker = "*"
        else:
            continue

        # 确保不越界
        if end <= len(chars):
            chars.insert(end, marker)
        if offset <= len(chars):
            chars.insert(offset, marker)

    return "".join(chars)


def article_to_markdown(article: dict, media_entities: list) -> str:
    """将 X Article 的 content blocks 转为 Markdown"""
    lines = []
    content = article.get("content", {})
    blocks = content.get("blocks", [])
    entity_map = content.get("entityMap", [])

    # 构建 media entity 查找表: media_id -> image_url
    media_lookup = {}
    for me in media_entities:
        media_id = str(me.get("media_id", ""))
        info = me.get("media_info", {})
        img_url = info.get("original_img_url", "")
        if media_id and img_url:
            media_lookup[media_id] = img_url

    # 构建 entity key -> media_id 映射
    entity_media = {}
    for entry in entity_map:
        key = entry.get("key")
        value = entry.get("value", {})
        if value.get("type") == "MEDIA":
            items = value.get("data", {}).get("mediaItems", [])
            for item in items:
                mid = str(item.get("mediaId", ""))
                if mid:
                    entity_media[key] = mid

    for block in blocks:
        block_type = block.get("type", "unstyled")
        text = block.get("text", "")
        inline_styles = block.get("inlineStyleRanges", [])
        entity_ranges = block.get("entityRanges", [])

        if block_type == "atomic":
            # 图片/媒体块
            for er in entity_ranges:
                key = er.get("key")
                media_id = entity_media.get(key, "")
                img_url = media_lookup.get(media_id, "")
                if img_url:
                    lines.append(f"![image]({img_url})")
                    lines.append("")
            continue

        # 应用行内样式
        styled_text = apply_inline_styles(text, inline_styles)

        if block_type == "header-one":
            lines.append(f"# {styled_text}")
        elif block_type == "header-two":
            lines.append(f"## {styled_text}")
        elif block_type == "header-three":
            lines.append(f"### {styled_text}")
        elif block_type == "blockquote":
            for line in styled_text.split("\n"):
                lines.append(f"> {line}")
        elif block_type == "unordered-list-item":
            lines.append(f"- {styled_text}")
        elif block_type == "ordered-list-item":
            lines.append(f"1. {styled_text}")
        else:
            # unstyled = 普通段落
            lines.append(styled_text)

        lines.append("")

    return "\n".join(lines)


def format_tweet_to_md(tweet: dict, is_quote: bool = False) -> str:
    """将单条推文数据转为 Markdown"""
    lines = []

    author = tweet.get("author", {})
    name = author.get("name", "Unknown")
    screen_name = author.get("screen_name", "unknown")
    created = tweet.get("created_at", "")
    text = tweet.get("text", "")
    url = tweet.get("url", "")

    # 时间格式化
    time_str = ""
    if created:
        try:
            dt = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            time_str = created

    prefix = "> " if is_quote else ""

    if is_quote:
        lines.append(f"> **{name}** (@{screen_name}) - {time_str}")
        lines.append(">")
        for line in text.split("\n"):
            lines.append(f"> {line}")
        lines.append("")
    else:
        lines.append(f"**{name}** (@{screen_name}) - {time_str}")
        lines.append("")
        lines.append(text)
        lines.append("")

    # 处理媒体
    media = tweet.get("media", {})
    if media:
        photos = media.get("photos", [])
        for photo in photos:
            img_url = photo.get("url", "")
            if img_url:
                lines.append(f"{prefix}![image]({img_url})")
                lines.append("")

        videos = media.get("videos", [])
        for video in videos:
            video_url = video.get("url", "")
            if video_url:
                lines.append(f"{prefix}[Video]({video_url})")
                lines.append("")

    # 处理引用推文
    quote = tweet.get("quote")
    if quote:
        lines.append("---")
        lines.append("")
        lines.append(format_tweet_to_md(quote, is_quote=True))

    # 推文链接
    if url and not is_quote:
        lines.append(f"[原文链接]({url})")
        lines.append("")

    return "\n".join(lines)


def fetch_thread(tweet_id: str, username: str) -> list[dict]:
    """
    尝试获取完整线程。
    通过逐条追溯 reply 来重建线程。
    """
    tweets = []
    visited = set()

    # 向上追溯
    chain_up = []
    temp_id = tweet_id
    while temp_id and temp_id not in visited:
        visited.add(temp_id)
        tweet = fetch_tweet(temp_id)
        if not tweet:
            break
        chain_up.append(tweet)
        replying_to = tweet.get("replying_to")
        replying_to_status = tweet.get("replying_to_status")
        if replying_to_status and replying_to == username:
            temp_id = replying_to_status
        else:
            break

    chain_up.reverse()
    tweets = chain_up

    return tweets


def build_frontmatter(tweets: list[dict], original_url: str) -> str:
    """从推文数据构建 YAML frontmatter"""
    if not tweets:
        return ""

    first_tweet = tweets[0]
    author_data = first_tweet.get("author", {})
    name = author_data.get("name", "Unknown")
    screen_name = author_data.get("screen_name", "unknown")

    # 确定标题
    article = first_tweet.get("article")
    if article and article.get("title"):
        title = article["title"]
    elif len(tweets) == 1:
        raw_text = first_tweet.get("text", "")
        title = raw_text.split("\n")[0][:50].strip()
        if len(raw_text.split("\n")[0]) > 50:
            title += "…"
    else:
        raw_text = first_tweet.get("text", "")
        title = raw_text.split("\n")[0][:50].strip()
        if len(raw_text.split("\n")[0]) > 50:
            title += "…"
        title += f"（{len(tweets)}条线程）"

    # 确定内容类型
    if article and article.get("content", {}).get("blocks"):
        content_type = "article"
    elif len(tweets) > 1:
        content_type = "thread"
    else:
        content_type = "tweet"

    # 日期
    date_str = ""
    created = first_tweet.get("created_at", "")
    if article and article.get("created_at"):
        try:
            dt = datetime.fromisoformat(
                article["created_at"].replace("Z", "+00:00")
            )
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    if not date_str and created:
        try:
            dt = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    saved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 语言
    lang = first_tweet.get("lang", "")

    # 互动数据
    likes = first_tweet.get("likes", 0)
    retweets = first_tweet.get("retweets", 0)
    views = first_tweet.get("views", 0)

    # 转义标题中的引号
    safe_title = title.replace('"', '\\"')

    lines = [
        "---",
        f'title: "{safe_title}"',
        f'author: "{name}"',
        f'author_handle: "@{screen_name}"',
        f'source: "{original_url}"',
        f"type: {content_type}",
        f"date: {date_str}",
        f"saved_at: {saved_at}",
        f"lang: {lang}",
        f"likes: {likes}",
        f"retweets: {retweets}",
        f"views: {views}",
        "tags:",
        "category:",
        "summary:",
        "status: raw",
        "---",
    ]

    return "\n".join(lines)


def build_markdown(tweets: list[dict], original_url: str) -> str:
    """将推文列表转为完整 Markdown 文档，自动识别 Article"""
    if not tweets:
        return ""

    first_tweet = tweets[0]
    author = first_tweet.get("author", {})
    name = author.get("name", "Unknown")
    screen_name = author.get("screen_name", "unknown")

    # 检查是否包含 Article
    article = first_tweet.get("article")
    if article and article.get("content", {}).get("blocks"):
        # X Article 长文模式
        title = article.get("title", "")
        created = article.get("created_at", "")
        media_entities = article.get("media_entities", [])

        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**{name}** (@{screen_name})")
        lines.append("")

        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                time_str = created
            lines.append(f"*{time_str}*")
            lines.append("")

        lines.append(f"> 来源: {original_url}")
        lines.append("")

        # 封面图
        cover = article.get("cover_media", {})
        cover_info = cover.get("media_info", {})
        cover_url = cover_info.get("original_img_url", "")
        if cover_url:
            lines.append(f"![cover]({cover_url})")
            lines.append("")

        lines.append("---")
        lines.append("")

        # 文章正文
        lines.append(article_to_markdown(article, media_entities))

        # 在内容前插入 frontmatter
        frontmatter = build_frontmatter(tweets, original_url)
        return frontmatter + "\n\n" + "\n".join(lines)

    # 普通推文/线程模式
    lines = []
    lines.append(f"# {name} (@{screen_name})")
    lines.append("")
    lines.append(f"> 来源: {original_url}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, tweet in enumerate(tweets):
        if len(tweets) > 1:
            lines.append(f"### [{i + 1}/{len(tweets)}]")
            lines.append("")
        lines.append(format_tweet_to_md(tweet))
        if i < len(tweets) - 1:
            lines.append("---")
            lines.append("")

    # 在内容前插入 frontmatter
    frontmatter = build_frontmatter(tweets, original_url)
    return frontmatter + "\n\n" + "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    """复制到剪贴板（macOS）"""
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
        return process.returncode == 0
    except FileNotFoundError:
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 x2md.py <tweet_url>")
        print("示例: python3 x2md.py https://x.com/dotey/status/2021711269426765853")
        sys.exit(1)

    url = sys.argv[1]
    tweet_id = extract_tweet_id(url)
    username = extract_username(url)

    print(f"正在获取推文 {tweet_id} ...")

    # 尝试获取线程
    tweets = fetch_thread(tweet_id, username)

    if not tweets:
        print("未能获取到推文内容")
        sys.exit(1)

    # 检测类型
    article = tweets[0].get("article")
    if article and article.get("content", {}).get("blocks"):
        title = article.get("title", "")
        block_count = len(article["content"]["blocks"])
        print(f"检测到 X Article: {title}")
        print(f"文章包含 {block_count} 个内容块")
    else:
        print(f"获取到 {len(tweets)} 条推文")

    # 转换为 Markdown
    markdown = build_markdown(tweets, url)

    # 生成文件名: "作者 - 标题.md"
    author = tweets[0].get("author", {})
    display_name = author.get("name", username)
    article = tweets[0].get("article")
    if article and article.get("title"):
        title = article["title"]
    elif len(tweets) == 1:
        # 单条推文: 取前30字作为标题
        raw_text = tweets[0].get("text", "")
        title = raw_text.split("\n")[0][:30].strip()
        if len(raw_text.split("\n")[0]) > 30:
            title += "…"
    else:
        # 线程: 用第一条推文前30字
        raw_text = tweets[0].get("text", "")
        title = raw_text.split("\n")[0][:30].strip()
        if len(raw_text.split("\n")[0]) > 30:
            title += "…"
        title += f"（{len(tweets)}条线程）"

    # 清理文件名中不合法的字符
    safe_title = re.sub(r'[<>:"/\\|?*]', "", title).strip()
    if not safe_title:
        safe_title = tweet_id
    filename = f"{display_name} - {safe_title}.md"

    # 如果当前目录下存在 X收藏/ 子目录，则保存到其中
    x_dir = os.path.join(os.getcwd(), "X收藏")
    if os.path.isdir(x_dir):
        filepath = os.path.join(x_dir, filename)
    else:
        filepath = filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"已保存到: {filepath}")

    # 复制到剪贴板
    if copy_to_clipboard(markdown):
        print("已复制到剪贴板")
    else:
        print("剪贴板复制失败，请手动复制文件内容")


if __name__ == "__main__":
    main()
