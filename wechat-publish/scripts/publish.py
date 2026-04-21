#!/usr/bin/env python3
"""wx_publish — 一键发布 Markdown 到微信公众号草稿。

编排 auth → md2pub → upload → draft 四个步骤。

用法:
    python3 publish.py 日报.md                              # 完整发布（含图片+封面）
    python3 publish.py 日报.md --title "自定义标题"           # 指定标题
    python3 publish.py 日报.md --port 9222                   # 指定 CDP 端口
    python3 publish.py 日报.md --attachments ~/vault/attachments  # 指定图片目录
    python3 publish.py 日报.md --dry-run                     # 只转换不发布

依赖: pip install websockets（仅 auth 步骤需要）
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent
MD2PUB = Path.home() / ".claude/scripts/md2pub.py"
DEFAULT_ATTACHMENTS = Path.home() / "Documents/obsidian/mixiaomi/attachments"


def load_module(path: Path, name: str):
    """动态加载同目录下的 Python 模块。"""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extract_title_from_md(md_text: str) -> str:
    """从 markdown frontmatter 或第一个 h1 提取标题。"""
    # frontmatter title
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', md_text, re.MULTILINE)
    if m:
        return m.group(1)
    # first h1
    m = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
    if m:
        return m.group(1)
    return "未命名文章"


def extract_image_refs(md_text: str) -> list[str]:
    """提取 markdown 中所有 Obsidian 图片嵌入 ![[filename]]。"""
    return re.findall(r"!\[\[([^\]]+)\]\]", md_text)


def replace_images_in_md(md_text: str, cdn_map: dict) -> str:
    """将 ![[img]] 替换为 ![img](cdn_url)，封面图直接删除。"""
    for img_name, info in cdn_map.items():
        if "cover" in img_name:
            md_text = md_text.replace(f"![[{img_name}]]", "")
        else:
            md_text = md_text.replace(f"![[{img_name}]]", f"![{img_name}]({info['cdn_url']})")
    return md_text


def main():
    ap = argparse.ArgumentParser(prog="wx_publish", description="一键发布 Markdown 到微信公众号草稿")
    ap.add_argument("input", help="Markdown 文件路径")
    ap.add_argument("--title", help="文章标题（默认从 MD 提取）")
    ap.add_argument("--author", default="智涌MindSurge")
    ap.add_argument("--digest", default="", help="文章摘要")
    ap.add_argument("--theme", default="default", help="md2pub 主题")
    ap.add_argument("--port", type=int, default=9224, help="CDP 端口（默认 9224）")
    ap.add_argument("--attachments", type=Path, default=DEFAULT_ATTACHMENTS, help="图片目录")
    ap.add_argument("--dry-run", action="store_true", help="只转换 HTML，不上传不发布")
    ap.add_argument("--app-msg-id", default="", help="更新已有草稿")
    args = ap.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"ERROR: {md_path} 不存在", file=sys.stderr)
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    title = args.title or extract_title_from_md(md_text)
    print(f"📄 标题: {title}", file=sys.stderr)

    # ── Step 1: Auth ──
    if not args.dry_run:
        print("\n🔑 Step 1: 获取登录凭证...", file=sys.stderr)
        auth = load_module(SKILL_DIR / "auth.py", "auth")
        import asyncio

        creds = asyncio.run(auth.get_credentials(args.port))
        if not creds["token"]:
            print("ERROR: 未获取到 token，请确认已登录微信后台", file=sys.stderr)
            sys.exit(1)
        print(f"  token={creds['token']}, cookie={len(creds['cookie'])} chars", file=sys.stderr)

    # ── Step 2: Upload images ──
    image_refs = extract_image_refs(md_text)
    cdn_map = {}  # {filename: {"cdn_url": ..., "fileid": ...}}
    cover_info = {"cdn_url": "", "fileid": ""}

    if image_refs and not args.dry_run:
        print(f"\n🖼️  Step 2: 上传 {len(image_refs)} 张图片...", file=sys.stderr)
        upload = load_module(SKILL_DIR / "upload.py", "upload")
        for img_name in image_refs:
            img_path = args.attachments / img_name
            if not img_path.exists() and "cover" in img_name:
                # Fallback: try generic cover.png in the same directory
                fallback = args.attachments / "cover.png"
                if fallback.exists():
                    print(f"  FALLBACK {img_name} → cover.png", file=sys.stderr)
                    img_path = fallback
            if not img_path.exists():
                print(f"  SKIP {img_name}（未找到）", file=sys.stderr)
                continue
            info = upload.upload_image(str(img_path), creds["token"], creds["cookie"])
            cdn_map[img_name] = info
            if "cover" in img_name:
                cover_info = info
            print(f"  ✓ {img_name}", file=sys.stderr)
    elif image_refs:
        print(f"\n🖼️  Step 2: [dry-run] 跳过 {len(image_refs)} 张图片上传", file=sys.stderr)

    # ── Step 3: MD → HTML ──
    print("\n📝 Step 3: 转换 MD → HTML...", file=sys.stderr)
    md2pub = load_module(MD2PUB, "md2pub")

    # Replace image references with CDN URLs before conversion
    processed_md = replace_images_in_md(md_text, cdn_map) if cdn_map else md_text
    html_body = md2pub.convert(processed_md, args.theme)
    print(f"  HTML: {len(html_body)} chars", file=sys.stderr)

    if args.dry_run:
        out = Path("/tmp/wx_publish_preview.html")
        out.write_text(md2pub.convert_full_html(processed_md, args.theme), encoding="utf-8")
        print(f"\n✅ [dry-run] 预览: {out}", file=sys.stderr)
        return

    # ── Step 4: Create draft ──
    print("\n📮 Step 4: 创建草稿...", file=sys.stderr)
    draft = load_module(SKILL_DIR / "draft.py", "draft")
    result = draft.create_or_update_draft(
        token=creds["token"],
        cookie=creds["cookie"],
        title=title,
        html_content=html_body,
        author=args.author,
        digest=args.digest,
        cover_fileid=cover_info["fileid"],
        cover_cdn=cover_info["cdn_url"],
        app_msg_id=args.app_msg_id,
    )

    ret = result.get("base_resp", {}).get("ret", -1)
    aid = result.get("appMsgId", "")
    if ret == 0:
        print(f"\n✅ 草稿创建成功！appMsgId={aid}", file=sys.stderr)
        print(f"   封面: {'有' if cover_info['cdn_url'] else '无'}", file=sys.stderr)
        print(f"   配图: {len([k for k in cdn_map if 'cover' not in k])} 张", file=sys.stderr)
    else:
        print(f"\n❌ 失败 ret={ret}", file=sys.stderr)
        sys.exit(1)

    # Output result as JSON
    json.dump({"ret": ret, "appMsgId": aid, "title": title}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
