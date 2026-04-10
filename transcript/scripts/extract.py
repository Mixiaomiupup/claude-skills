#!/usr/bin/env python3
"""Extract subtitles from video URLs, clean and organize by chapters.

Supports YouTube and Bilibili via yt-dlp.
Outputs: raw SRT + chapter-organized Markdown.

Usage:
    python3 extract.py <URL> [--lang LANG] [--chapters-json FILE]

    --lang         Subtitle language preference (default: en-orig,en,zh-Hans)
    --chapters-json  External chapters JSON file (for videos without embedded chapters)
                     Format: [{"start_time": 0, "title": "Intro"}, ...]
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VAULT = Path.home() / "Documents/obsidian/mixiaomi"


def detect_platform(url: str) -> str:
    if "bilibili.com" in url or "b23.tv" in url:
        return "bilibili"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "unknown"


def get_video_metadata(url: str) -> dict:
    """Get video title, chapters, duration, uploader via yt-dlp."""
    cmd = ["yt-dlp", "--dump-json", "--no-download", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"Error getting metadata: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def download_subtitles(url: str, lang_prefs: list[str], out_dir: Path) -> Path | None:
    """Download subtitles with language preference fallback."""
    # Try auto-generated subs first, then manual subs
    for lang in lang_prefs:
        for sub_flag in ["--write-auto-sub", "--write-sub"]:
            cmd = [
                "yt-dlp",
                sub_flag,
                "--sub-lang",
                lang,
                "--sub-format",
                "srt",
                "--skip-download",
                "-o",
                str(out_dir / "sub"),
                url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            # Find the downloaded .srt file
            srt_files = list(out_dir.glob("sub*.srt"))
            if srt_files:
                return srt_files[0]
    return None


def parse_srt(srt_path: Path) -> list[tuple[float, str]]:
    """Parse SRT file into list of (start_seconds, text)."""
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\n+", content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        time_match = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
            lines[1],
        )
        if not time_match:
            continue
        h, m, s = (
            int(time_match.group(1)),
            int(time_match.group(2)),
            int(time_match.group(3)),
        )
        start_sec = h * 3600 + m * 60 + s
        text = " ".join(lines[2:])
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            entries.append((start_sec, text))
    return entries


def deduplicate(entries: list[tuple[float, str]]) -> list[tuple[float, str]]:
    """Remove duplicate lines from auto-generated subtitles."""
    seen: set[str] = set()
    result = []
    for sec, text in entries:
        if text not in seen:
            seen.add(text)
            result.append((sec, text))
    return result


def assign_to_chapters(
    entries: list[tuple[float, str]], chapters: list[dict]
) -> dict[int, list[str]]:
    """Assign subtitle entries to chapters by timestamp."""
    chapter_texts: dict[int, list[str]] = {i: [] for i in range(len(chapters))}
    for sec, text in entries:
        ch_idx = 0
        for i, ch in enumerate(chapters):
            if sec >= ch["start_time"]:
                ch_idx = i
        chapter_texts[ch_idx].append(text)
    return chapter_texts


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS or MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_paragraphs(texts: list[str], max_len: int = 500) -> list[str]:
    """Join text into paragraphs, splitting at sentence boundaries."""
    full_text = " ".join(texts)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    if not full_text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", full_text)
    paragraphs = []
    para: list[str] = []
    para_len = 0
    for s in sentences:
        para.append(s)
        para_len += len(s)
        if para_len > max_len:
            paragraphs.append(" ".join(para))
            para = []
            para_len = 0
    if para:
        paragraphs.append(" ".join(para))
    return paragraphs


def generate_markdown(
    metadata: dict,
    chapters: list[dict],
    chapter_texts: dict[int, list[str]],
    url: str,
    platform: str,
) -> str:
    """Generate chapter-organized Markdown with frontmatter."""
    title = metadata.get("title", "Untitled")
    uploader = metadata.get("uploader", metadata.get("channel", "Unknown"))
    duration = metadata.get("duration", 0)
    upload_date = metadata.get("upload_date", "")
    if upload_date:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    description = metadata.get("description", "")

    lines = [
        "---",
        f'title: "{title}"',
        f'author: "{uploader}"',
        f'source: "{url}"',
        f"platform: {platform}",
        f"date: {upload_date}",
        f"duration: {format_time(duration)}",
        f"type: transcript",
        "status: raw",
        "tags: []",
        'category: ""',
        "---",
        "",
        f"# {title}",
        "",
        f"> **{uploader}** | {format_time(duration)} | [{platform}]({url})",
        "",
    ]

    # Table of contents
    lines.append("## Chapters")
    lines.append("")
    for i, ch in enumerate(chapters):
        ts = format_time(ch["start_time"])
        lines.append(f"- [{ts}] {ch['title']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Chapter content
    for i, ch in enumerate(chapters):
        ts = format_time(ch["start_time"])
        lines.append(f"## {ts} {ch['title']}")
        lines.append("")
        paragraphs = build_paragraphs(chapter_texts.get(i, []))
        if paragraphs:
            for p in paragraphs:
                lines.append(p)
                lines.append("")
        else:
            lines.append("*[No subtitle content]*")
            lines.append("")

    # My notes section
    lines.append("---")
    lines.append("")
    lines.append("## My Notes")
    lines.append("")

    return "\n".join(lines)


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Sanitize string for use as filename."""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_len]


def main():
    parser = argparse.ArgumentParser(description="Extract and organize video subtitles")
    parser.add_argument("url", help="Video URL (YouTube or Bilibili)")
    parser.add_argument(
        "--lang",
        default="en-orig,en,zh-Hans,zh",
        help="Comma-separated subtitle language preferences",
    )
    parser.add_argument(
        "--chapters-json",
        help="External chapters JSON file for videos without embedded chapters",
    )
    parser.add_argument(
        "--out-dir",
        help="Output directory (default: auto-detect from vault)",
    )
    args = parser.parse_args()

    platform = detect_platform(args.url)
    if platform == "unknown":
        print(f"Warning: Unknown platform for URL: {args.url}", file=sys.stderr)
        platform = "other"

    lang_prefs = [l.strip() for l in args.lang.split(",")]

    # Step 1: Get metadata
    print(f"Fetching metadata from {platform}...", file=sys.stderr)
    metadata = get_video_metadata(args.url)
    title = metadata.get("title", "Untitled")
    print(f"Title: {title}", file=sys.stderr)

    # Step 2: Get chapters
    chapters = metadata.get("chapters") or []
    if args.chapters_json:
        chapters = json.loads(Path(args.chapters_json).read_text())
        print(f"Loaded {len(chapters)} chapters from file", file=sys.stderr)
    elif chapters:
        print(f"Found {len(chapters)} chapters in metadata", file=sys.stderr)
    else:
        # No chapters — treat entire video as one chapter
        duration = metadata.get("duration", 0)
        chapters = [{"start_time": 0, "title": title, "end_time": duration}]
        print("No chapters found, treating as single segment", file=sys.stderr)

    # Step 3: Download subtitles
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        print(f"Downloading subtitles ({', '.join(lang_prefs)})...", file=sys.stderr)
        srt_path = download_subtitles(args.url, lang_prefs, tmppath)
        if not srt_path:
            print(
                "ERROR: No subtitles found for any requested language.", file=sys.stderr
            )
            sys.exit(1)
        print(f"Got subtitles: {srt_path.name}", file=sys.stderr)

        # Step 4: Parse and clean
        entries = parse_srt(srt_path)
        print(f"Parsed {len(entries)} subtitle entries", file=sys.stderr)
        deduped = deduplicate(entries)
        print(f"After dedup: {len(deduped)} unique lines", file=sys.stderr)

        # Step 5: Assign to chapters
        chapter_texts = assign_to_chapters(deduped, chapters)

        # Step 6: Determine output
        uploader = metadata.get("uploader", metadata.get("channel", "Unknown"))
        safe_title = sanitize_filename(title)
        filename = f"{sanitize_filename(uploader)} - {safe_title}.md"

        out_dir = Path(args.out_dir) if args.out_dir else None
        # Will be set by caller or default to vault raw/

        # Step 7: Generate markdown
        md_content = generate_markdown(
            metadata, chapters, chapter_texts, args.url, platform
        )

        # Step 8: Save raw SRT
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            srt_dest = out_dir / f"{safe_title}.srt"
            srt_dest.write_text(srt_path.read_text(), encoding="utf-8")
            md_dest = out_dir / filename
            md_dest.write_text(md_content, encoding="utf-8")
            print(f"\nSaved:", file=sys.stderr)
            print(f"  SRT: {srt_dest}", file=sys.stderr)
            print(f"  MD:  {md_dest}", file=sys.stderr)
        else:
            # Print to stdout for piping, save SRT info
            print(md_content)
            # Also print paths for the caller
            print(
                f"\n<!-- srt_lines: {len(entries)}, unique: {len(deduped)}, chapters: {len(chapters)} -->"
            )

    # Output summary as JSON for caller to parse
    summary = {
        "title": title,
        "uploader": uploader,
        "platform": platform,
        "duration": metadata.get("duration", 0),
        "chapters": len(chapters),
        "subtitle_lines": len(entries),
        "unique_lines": len(deduped),
        "filename": filename,
    }
    print(json.dumps(summary), file=sys.stderr)


if __name__ == "__main__":
    main()
