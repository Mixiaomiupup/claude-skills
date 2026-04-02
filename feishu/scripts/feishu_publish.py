#!/usr/bin/env python3
"""Publish a Markdown file to Feishu wiki.

Handles: preprocess → upload → import → move to wiki → insert external images.

Usage:
    python3 feishu_publish.py --file article.md --title "标题" --parent-node "UzfowFW4sidwVdkZulecDOQ3nyd"
    python3 feishu_publish.py --file article.md --title "标题" --parent-node "UzfowFW4sidwVdkZulecDOQ3nyd" --space-id "7559794508562251778"
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time


SPACE_ID = "7559794508562251778"
MOUNT_KEY = "nodcn8QDoQdhGBYxo9yRouGWEpb"


def get_credentials():
    """Read app_id and app_secret from ~/.lark-cli/apps.json."""
    config_path = os.path.expanduser("~/.lark-cli/apps.json")
    with open(config_path) as f:
        config = json.load(f)
    default_app = config["apps"][config["default"]]
    return default_app["app_id"], default_app["app_secret"]


def curl_json(args: list) -> dict:
    result = subprocess.run(["curl", "-s"] + args, capture_output=True, text=True)
    return json.loads(result.stdout)


def get_token() -> str:
    app_id, app_secret = get_credentials()
    resp = curl_json([
        "-X", "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"app_id": app_id, "app_secret": app_secret}),
    ])
    return resp["tenant_access_token"]


def preprocess_markdown(content: str) -> tuple[str, list[dict]]:
    """Remove frontmatter, wikilinks, toc, and extract external images.

    Returns (cleaned_content, image_list).
    image_list: [{"url": "...", "alt": "...", "marker": "IMG_PLACEHOLDER_N"}]
    """
    # Remove YAML frontmatter
    content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    images = []
    lines = content.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Remove local obsidian images
        if re.match(r"!\[\[.*?\]\]", stripped):
            continue
        # Remove [toc]
        if stripped.lower() == "[toc]":
            continue
        # Convert wikilinks to plain text
        line = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", lambda m: m.group(2) or m.group(1), line)
        # Extract external images
        m = re.match(r"!\[([^\]]*)\]\((https?://[^)]+)\)", stripped)
        if m:
            marker = f"IMG_PLACEHOLDER_{len(images)}"
            images.append({"url": m.group(2), "alt": m.group(1), "marker": marker})
            cleaned.append(f"<!-- {marker} -->")
        else:
            cleaned.append(line)

    return "\n".join(cleaned), images


def upload_and_import(token: str, md_path: str, title: str) -> str:
    """Upload markdown file and import as docx. Returns doc_token."""
    file_size = os.path.getsize(md_path)

    # Upload
    upload_resp = curl_json([
        "-X", "POST",
        "https://open.feishu.cn/open-apis/drive/v1/files/upload_all",
        "-H", f"Authorization: Bearer {token}",
        "-F", "file_name=article.md",
        "-F", "parent_type=explorer",
        "-F", "parent_node=",
        "-F", f"size={file_size}",
        "-F", f"file=@{md_path}",
    ])
    file_token = upload_resp["data"]["file_token"]
    print(f"  Uploaded: {file_token}")

    # Import
    import_resp = curl_json([
        "-X", "POST",
        "https://open.feishu.cn/open-apis/drive/v1/import_tasks",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "file_extension": "md",
            "file_token": file_token,
            "type": "docx",
            "file_name": title,
            "point": {"mount_type": 1, "mount_key": MOUNT_KEY},
        }),
    ])
    ticket = import_resp["data"]["ticket"]

    # Poll
    for _ in range(15):
        time.sleep(2)
        task_resp = curl_json([
            f"https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}",
            "-H", f"Authorization: Bearer {token}",
        ])
        result = task_resp.get("data", {}).get("result", {})
        if result.get("token"):
            doc_token = result["token"]
            print(f"  Imported: {doc_token}")
            return doc_token

    print("  ERROR: Import timeout", file=sys.stderr)
    sys.exit(1)


def move_to_wiki(token: str, doc_token: str, parent_node: str, space_id: str) -> str:
    """Move doc into wiki. Returns node_token."""
    resp = curl_json([
        "-X", "POST",
        f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "parent_wiki_token": parent_node,
            "obj_type": "docx",
            "obj_token": doc_token,
        }),
    ])

    task_id = resp.get("data", {}).get("task_id")
    if not task_id:
        print(f"  ERROR: Move failed: {resp}", file=sys.stderr)
        sys.exit(1)

    # Poll task
    for _ in range(10):
        time.sleep(2)
        task_resp = curl_json([
            f"https://open.feishu.cn/open-apis/wiki/v2/tasks/{task_id}?task_type=move",
            "-H", f"Authorization: Bearer {token}",
        ])
        results = task_resp.get("data", {}).get("task", {}).get("move_result", [])
        if results and results[0].get("status") == 0:
            node_token = results[0]["node"]["node_token"]
            print(f"  Moved to wiki: {node_token}")
            return node_token

    print("  ERROR: Move timeout", file=sys.stderr)
    sys.exit(1)


def insert_external_images(token: str, doc_id: str, images: list[dict]):
    """Download external images and insert into document with correct dimensions."""
    if not images:
        return

    print(f"  Inserting {len(images)} images...")

    # Get all blocks
    blocks = curl_json([
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500",
        "-H", f"Authorization: Bearer {token}",
    ])["data"]["items"]

    page_children = [b for b in blocks if b.get("parent_id") == doc_id and b["block_id"] != doc_id]

    # Process from back to front
    for img_info in reversed(images):
        marker = img_info["marker"]
        url = img_info["url"]

        # Find marker position
        target_idx = None
        for i, b in enumerate(page_children):
            if marker in json.dumps(b, ensure_ascii=False):
                target_idx = i
                break

        if target_idx is None:
            print(f"    WARN: {marker} not found, skip")
            continue

        # Download image
        ext = url.rsplit(".", 1)[-1].split("?")[0][:4]
        local_path = f"/tmp/feishu_img_{marker}.{ext}"
        subprocess.run(["curl", "-s", "-o", local_path, url])
        fsize = os.path.getsize(local_path)

        # Delete marker block
        curl_json([
            "-X", "DELETE",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"start_index": target_idx, "end_index": target_idx + 1}),
        ])
        time.sleep(0.5)

        # Create empty image block
        create_resp = curl_json([
            "-X", "POST",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"children": [{"block_type": 27, "image": {}}], "index": target_idx}),
        ])
        new_block_id = create_resp["data"]["children"][0]["block_id"]
        time.sleep(0.5)

        # Upload image
        upload_resp = curl_json([
            "-X", "POST",
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"file_name=image.{ext}",
            "-F", "parent_type=docx_image",
            "-F", f"parent_node={new_block_id}",
            "-F", f"size={fsize}",
            "-F", f"file=@{local_path}",
        ])
        file_token = upload_resp["data"]["file_token"]
        time.sleep(0.5)

        # Bind image (dimensions auto-detected)
        curl_json([
            "-X", "PATCH",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{new_block_id}",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"replace_image": {"token": file_token}}),
        ])
        print(f"    ✓ {marker} ({fsize} bytes)")
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="Publish Markdown to Feishu wiki")
    parser.add_argument("--file", required=True, help="Path to markdown file")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("--parent-node", required=True, help="Parent wiki node_token")
    parser.add_argument("--space-id", default=SPACE_ID, help="Wiki space ID")
    args = parser.parse_args()

    # Read and preprocess
    with open(args.file) as f:
        content = f.read()

    cleaned, images = preprocess_markdown(content)

    # Write preprocessed file
    tmp_path = "/tmp/feishu_article.md"
    with open(tmp_path, "w") as f:
        f.write(cleaned)

    print(f"Preprocessed: {len(cleaned)} chars, {len(images)} images extracted")

    # Get token
    token = get_token()

    # Upload and import
    doc_token = upload_and_import(token, tmp_path, args.title)

    # Move to wiki
    node_token = move_to_wiki(token, doc_token, args.parent_node, args.space_id)

    # Insert external images
    insert_external_images(token, doc_token, images)

    # Output result as JSON
    result = {
        "doc_token": doc_token,
        "node_token": node_token,
        "url": f"https://huazhi-ai.feishu.cn/docx/{doc_token}",
        "images_inserted": len(images),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
