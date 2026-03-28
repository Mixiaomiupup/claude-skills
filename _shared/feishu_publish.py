"""Shared Feishu publish & broadcast script for daily digest skills.

Usage in skill (via Bash heredoc):

    exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

    publish_to_feishu(
        md_path='~/日报/X日报-2026-03-17.md',
        doc_title='X/Twitter 日报 - 2026-03-17',
        wiki_parent_node='IOsNwtIPdiLTYukHdgqcMIE9nad',
        card_template='blue',
        card_title='X/Twitter 日报 - 2026-03-17',
        card_summary='**重大新闻**\\n* 要点1\\n* 要点2',
        recipients='all',  # or ['米冠飞', '陈卿', ...]
    )
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path


def _curl_json(args):
    """Execute curl and parse JSON response."""
    r = subprocess.run(["curl", "-s"] + args, capture_output=True, text=True)
    return json.loads(r.stdout)


def _get_feishu_credentials():
    """Read app_id and app_secret from ~/.claude.json lark-mcp config."""
    with open(os.path.expanduser("~/.claude.json")) as f:
        config = json.load(f)
    lark_args = config["mcpServers"]["lark-mcp"]["args"]
    app_id = lark_args[lark_args.index("-a") + 1]
    app_secret = lark_args[lark_args.index("-s") + 1]
    return app_id, app_secret


def _get_tenant_token(app_id, app_secret):
    """Get Feishu tenant_access_token."""
    resp = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"app_id": app_id, "app_secret": app_secret}),
        ]
    )
    return resp["tenant_access_token"]


def _preprocess_markdown(md_path):
    """Remove YAML frontmatter, Obsidian wikilinks, and image embeds."""
    with open(os.path.expanduser(md_path), "r", encoding="utf-8") as f:
        content = f.read()

    # Remove YAML frontmatter
    content = re.sub(r"^---\n.*?\n---\n", "", content, count=1, flags=re.DOTALL)
    # Remove ![[image]] embeds
    content = re.sub(r"!\[\[.*?\]\]", "", content)
    # Convert [[wikilink]] to plain text
    content = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", lambda m: m.group(2) or m.group(1), content)
    # Merge indented blockquotes under bullets into the bullet text.
    # Pattern: "  > text" (indented blockquote) → "  text" (bullet continuation).
    # This keeps title + description in one Feishu bullet block instead of splitting.
    # Only targets indented "> " (under bullets), not standalone "> " (top-level quotes).
    content = re.sub(r"^(  +)> ", r"\1", content, flags=re.MULTILINE)

    return content


def _upload_md_file(token, content, filename):
    """Upload markdown content as a file to Feishu drive."""
    tmp_path = f"/tmp/{filename}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)

    fsize = os.path.getsize(tmp_path)
    resp = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/drive/v1/files/upload_all",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"file_name={filename}",
            "-F", "parent_type=explorer",
            "-F", "parent_node=",
            "-F", f"size={fsize}",
            "-F", f"file=@{tmp_path}",
        ]
    )
    os.unlink(tmp_path)
    return resp["data"]["file_token"]


def _import_as_docx(token, file_token, doc_title):
    """Import uploaded file as Feishu docx and return doc_token."""
    resp = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/drive/v1/import_tasks",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "file_extension": "md",
                "file_token": file_token,
                "type": "docx",
                "file_name": doc_title,
                "point": {"mount_type": 1, "mount_key": "nodcn8QDoQdhGBYxo9yRouGWEpb"},
            }),
        ]
    )
    ticket = resp["data"]["ticket"]

    # Poll for completion
    doc_token = None
    for _ in range(10):
        time.sleep(2)
        result = _curl_json(
            [
                f"https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}",
                "-H", f"Authorization: Bearer {token}",
            ]
        )
        doc_token = result.get("data", {}).get("result", {}).get("token")
        if doc_token:
            break

    if not doc_token:
        raise RuntimeError(f"Import task {ticket} did not complete in time")
    return doc_token


def _read_existing_node_token(md_path):
    """Read feishu_node_token from markdown frontmatter, if present."""
    try:
        with open(os.path.expanduser(md_path), "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"feishu_node_token:\s*(\S+)", content)
        return m.group(1) if m else None
    except Exception:
        return None


def _list_all_blocks(token, doc_token):
    """List all blocks in a Feishu document (handles pagination)."""
    blocks = []
    page_token_param = ""
    while True:
        url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
            f"?page_size=500{page_token_param}"
        )
        resp = _curl_json([url, "-H", f"Authorization: Bearer {token}"])
        data = resp.get("data", {})
        blocks.extend(data.get("items", []))
        pt = data.get("page_token")
        if pt:
            page_token_param = f"&page_token={pt}"
        else:
            break
    return blocks


def _clear_doc(token, doc_token):
    """Delete all child blocks from a document's page block."""
    blocks = _list_all_blocks(token, doc_token)
    if len(blocks) < 2:
        return
    page_block = blocks[0]
    children = page_block.get("children", [])
    if not children:
        return
    _curl_json(
        [
            "-X", "DELETE",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
            f"/blocks/{page_block['block_id']}/children/batch_delete",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"start_index": 0, "end_index": len(children)}),
        ]
    )
    time.sleep(1)


def _copy_blocks_between_docs(token, src_doc, dst_doc):
    """Copy all content blocks from source doc to destination doc."""
    src_blocks = _list_all_blocks(token, src_doc)
    if len(src_blocks) < 2:
        return

    dst_blocks = _list_all_blocks(token, dst_doc)
    dst_page_id = dst_blocks[0]["block_id"]

    src_page = src_blocks[0]
    child_ids = src_page.get("children", [])
    block_map = {b["block_id"]: b for b in src_blocks}

    SKIP_FIELDS = {"block_id", "block_type", "parent_id", "children"}

    for cid in child_ids:
        block = block_map.get(cid)
        if not block or block["block_type"] == 1:
            continue

        payload = {"block_type": block["block_type"]}
        for key, value in block.items():
            if key not in SKIP_FIELDS:
                payload[key] = value

        resp = _curl_json(
            [
                "-X", "POST",
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{dst_doc}"
                f"/blocks/{dst_page_id}/children",
                "-H", f"Authorization: Bearer {token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"children": [payload], "index": -1}),
            ]
        )
        # Log errors but continue
        if resp.get("code", 0) != 0:
            bt = block["block_type"]
            print(f"[feishu] Warning: block type {bt} copy failed: {resp.get('msg')}")
        time.sleep(0.05)


def _get_doc_token_from_node(token, node_token):
    """Get the underlying doc_token from a wiki node_token."""
    resp = _curl_json(
        [
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node"
            f"?token={node_token}",
            "-H", f"Authorization: Bearer {token}",
        ]
    )
    return resp["data"]["node"]["obj_token"]


def _update_existing_doc(token, content, doc_title, node_token):
    """Update an existing Feishu doc by clearing and re-importing content.

    Returns the old doc_token (URL stays the same).
    """
    # 1. Get old doc_token
    old_doc_token = _get_doc_token_from_node(token, node_token)
    print(f"[feishu] Update mode: old doc {old_doc_token}")

    # 2. Import new content as temp doc
    filename = f"temp_update_{int(time.time())}.md"
    file_token = _upload_md_file(token, content, filename)
    tmp_doc_token = _import_as_docx(token, file_token, doc_title)
    print(f"[feishu] Imported temp doc: {tmp_doc_token}")

    # 3. Clear old doc
    _clear_doc(token, old_doc_token)
    print(f"[feishu] Cleared old doc")

    # 4. Copy blocks from temp to old doc
    _copy_blocks_between_docs(token, tmp_doc_token, old_doc_token)
    print(f"[feishu] Copied blocks to old doc")

    # 5. Best-effort cleanup of temp doc
    try:
        _curl_json(
            [
                "-X", "DELETE",
                f"https://open.feishu.cn/open-apis/drive/v1/files/{tmp_doc_token}"
                f"?type=docx",
                "-H", f"Authorization: Bearer {token}",
            ]
        )
    except Exception:
        pass

    return old_doc_token


def _upload_image(token, image_path):
    """Upload an image to Feishu and return the image_key."""
    fsize = os.path.getsize(image_path)
    resp = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/im/v1/images",
            "-H", f"Authorization: Bearer {token}",
            "-F", "image_type=message",
            "-F", f"image=@{image_path}",
        ]
    )
    if resp.get("code") != 0:
        print(f"[feishu] Warning: image upload failed: {resp.get('msg')}")
        return None
    return resp["data"]["image_key"]


def _upload_drive_image(token, image_path, parent_node):
    """Upload an image to Feishu Drive and return file_token for docx embedding."""
    fsize = os.path.getsize(image_path)
    filename = os.path.basename(image_path)
    resp = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"file_name={filename}",
            "-F", "parent_type=docx_image",
            "-F", f"parent_node={parent_node}",
            "-F", f"size={fsize}",
            "-F", f"file=@{image_path}",
        ]
    )
    if resp.get("code") != 0:
        print(f"[feishu] Warning: drive image upload failed: {resp.get('msg')}")
        return None
    return resp["data"]["file_token"]


def _insert_image_block(token, doc_token, parent_block_id, image_path, index=-1):
    """Insert an image into a Feishu document using the 3-step method.

    Feishu image blocks (block_type 27) must be created empty first, then the
    image is uploaded with parent_node=image_block_id, then PATCHed in.

    Args:
        token: Feishu tenant access token.
        doc_token: Target document token.
        parent_block_id: Parent block (usually page block) to insert under.
        image_path: Local path to the image file.
        index: Position index (-1 for end).

    Returns:
        True if successful, False otherwise.
    """
    # Step 1: Create empty image block
    resp = _curl_json(
        [
            "-X", "POST",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
            f"/blocks/{parent_block_id}/children",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "children": [{"block_type": 27, "image": {}}],
                "index": index,
            }),
        ]
    )
    if resp.get("code") != 0:
        print(f"[feishu] Warning: create empty image block failed: {resp.get('msg')}")
        return False
    image_block_id = resp["data"]["children"][0]["block_id"]

    # Step 2: Upload image with parent_node = image_block_id (NOT doc_token!)
    fsize = os.path.getsize(image_path)
    filename = os.path.basename(image_path)
    resp2 = _curl_json(
        [
            "-X", "POST",
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"file_name={filename}",
            "-F", "parent_type=docx_image",
            "-F", f"parent_node={image_block_id}",
            "-F", f"size={fsize}",
            "-F", f"file=@{image_path}",
        ]
    )
    if resp2.get("code") != 0:
        print(f"[feishu] Warning: image upload failed: {resp2.get('msg')}")
        return False
    file_token = resp2["data"]["file_token"]

    # Step 3: PATCH replace_image
    resp3 = _curl_json(
        [
            "-X", "PATCH",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
            f"/blocks/{image_block_id}",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"replace_image": {"token": file_token}}),
        ]
    )
    if resp3.get("code") != 0:
        print(f"[feishu] Warning: replace_image failed: {resp3.get('msg')}")
        return False
    return True


def insert_images_to_doc(token, doc_token, media_dir, tweet_block_map=None):
    """Insert images into a Feishu document using the 3-step method.

    Args:
        token: Feishu tenant access token.
        doc_token: Target document token.
        media_dir: Directory containing screenshot files (tweet-{id}.png).
        tweet_block_map: Optional dict mapping tweet_id to block_id for positioning.
            If None, images are appended to the end of the document.

    Returns:
        Number of images successfully inserted.
    """
    media_path = Path(media_dir)
    if not media_path.exists():
        return 0

    blocks = _list_all_blocks(token, doc_token)
    page_block_id = blocks[0]["block_id"]
    inserted = 0

    # Build a map of block text content -> block_id for positioning
    # Search ALL text-bearing keys including bullet/ordered lists
    block_text_map = {}
    text_keys = ("text", "heading1", "heading2", "heading3", "heading4",
                 "heading5", "heading6", "heading7", "heading8", "heading9",
                 "quote", "bullet", "ordered", "callout")
    for block in blocks:
        text_content = ""
        for key in text_keys:
            elem = block.get(key, {})
            for el in elem.get("elements", []):
                tc = el.get("text_run", {}).get("content", "")
                text_content += tc
                link = el.get("text_run", {}).get("text_element_style", {}).get("link", {})
                if link.get("url"):
                    import urllib.parse
                    text_content += urllib.parse.unquote(link["url"])
        if text_content:
            block_text_map[block["block_id"]] = text_content

    # Insert cover image first (at top of document)
    cover_path = media_path / "cover.png"
    if cover_path.exists():
        if _insert_image_block(token, doc_token, page_block_id, str(cover_path), index=1):
            inserted += 1
            print(f"[feishu] Inserted cover image")
        else:
            print(f"[feishu] Warning: cover insert failed")
        time.sleep(0.3)

    # Insert tweet screenshots
    for img_file in sorted(media_path.glob("tweet-*.png")):
        tweet_id = img_file.stem.replace("tweet-", "")

        # Find the block containing this tweet's URL
        target_index = -1
        for bid, text in block_text_map.items():
            if tweet_id in text:
                current_blocks = _list_all_blocks(token, doc_token)
                current_children = current_blocks[0].get("children", [])
                try:
                    idx = current_children.index(bid)
                    target_index = idx + 1
                except ValueError:
                    pass
                break

        if _insert_image_block(token, doc_token, page_block_id, str(img_file), index=target_index):
            inserted += 1
            print(f"[feishu] Inserted screenshot: {img_file.name}")
        else:
            print(f"[feishu] Warning: screenshot insert failed for {img_file.name}")
        time.sleep(0.3)

    return inserted


def insert_videos_to_doc(token, doc_token, media_dir):
    """Insert videos into a Feishu document using the 3-step file block method.

    Args:
        token: Feishu tenant access token.
        doc_token: Target document token.
        media_dir: Directory containing video files (tweet-{id}.mp4).

    Returns:
        Number of videos successfully inserted.
    """
    media_path = Path(media_dir)
    if not media_path.exists():
        return 0

    blocks = _list_all_blocks(token, doc_token)
    page_block_id = blocks[0]["block_id"]

    # Build text map including URLs for tweet ID matching
    block_text_map = {}
    text_keys = ("text", "heading1", "heading2", "heading3", "heading4",
                 "heading5", "heading6", "heading7", "heading8", "heading9",
                 "quote", "bullet", "ordered", "callout")
    for block in blocks:
        text_content = ""
        for key in text_keys:
            elem = block.get(key, {})
            for el in elem.get("elements", []):
                tc = el.get("text_run", {}).get("content", "")
                text_content += tc
                link = el.get("text_run", {}).get("text_element_style", {}).get("link", {})
                if link.get("url"):
                    import urllib.parse
                    text_content += urllib.parse.unquote(link["url"])
        if text_content:
            block_text_map[block["block_id"]] = text_content

    inserted = 0
    for video_file in sorted(media_path.glob("tweet-*.mp4")):
        tweet_id = video_file.stem.replace("tweet-", "")
        fsize = os.path.getsize(str(video_file))
        filename = video_file.name

        # Find the block containing this tweet's URL for positioning
        target_index = -1
        for bid, text in block_text_map.items():
            if tweet_id in text:
                current_blocks = _list_all_blocks(token, doc_token)
                current_children = current_blocks[0].get("children", [])
                try:
                    idx = current_children.index(bid)
                    target_index = idx + 1
                    print(f"[feishu] Video {tweet_id}: inserting at index {target_index}")
                except ValueError:
                    pass
                break

        # Step 1: Create empty file block
        resp = _curl_json(
            [
                "-X", "POST",
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
                f"/blocks/{page_block_id}/children",
                "-H", f"Authorization: Bearer {token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"children": [{"block_type": 23, "file": {}}], "index": target_index}),
            ]
        )
        if resp.get("code") != 0:
            print(f"[feishu] Warning: file block creation failed: {resp.get('msg')}")
            continue
        created_block_id = resp["data"]["children"][0]["block_id"]

        # The created block may be wrapped in a View block (type 33).
        # We need the actual file block (type 23) which is its child.
        time.sleep(0.5)
        block_resp = _curl_json(
            [
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
                f"/blocks/{created_block_id}",
                "-H", f"Authorization: Bearer {token}",
            ]
        )
        block_data = block_resp.get("data", {}).get("block", {})
        if block_data.get("block_type") == 33 and block_data.get("children"):
            file_block_id = block_data["children"][0]
        else:
            file_block_id = created_block_id

        # Step 2: Upload video with parent_node = file_block_id
        resp = _curl_json(
            [
                "-X", "POST",
                "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
                "-H", f"Authorization: Bearer {token}",
                "-F", f"file_name={filename}",
                "-F", "parent_type=docx_file",
                "-F", f"parent_node={file_block_id}",
                "-F", f"size={fsize}",
                "-F", f"file=@{str(video_file)}",
            ]
        )
        if resp.get("code") != 0:
            print(f"[feishu] Warning: video upload failed: {resp.get('msg')}")
            continue
        media_token = resp["data"]["file_token"]

        # Step 3: PATCH replace_file
        resp = _curl_json(
            [
                "-X", "PATCH",
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
                f"/blocks/{file_block_id}",
                "-H", f"Authorization: Bearer {token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"replace_file": {"token": media_token}}),
            ]
        )
        if resp.get("code") == 0:
            inserted += 1
            print(f"[feishu] Inserted video: {video_file.name}")
        else:
            print(f"[feishu] Warning: video replace failed: {resp.get('msg')}")
        time.sleep(0.2)

    return inserted


WIKI_SPACE_ID = "7559794508562251778"


def _move_to_wiki(token, doc_token, parent_node_token):
    """Move document into wiki knowledge base."""
    move_resp = _curl_json(
        [
            "-X", "POST",
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{WIKI_SPACE_ID}/nodes/move_docs_to_wiki",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "parent_wiki_token": parent_node_token,
                "obj_type": "docx",
                "obj_token": doc_token,
            }),
        ]
    )
    if move_resp.get("code") != 0:
        raise RuntimeError(
            f"[feishu] Failed to move doc to wiki: {move_resp.get('code')} - {move_resp.get('msg')}"
        )

    # Wait for async move to complete, then get node_token
    time.sleep(3)
    resp = _curl_json(
        [
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={doc_token}&obj_type=docx",
            "-H", f"Authorization: Bearer {token}",
        ]
    )
    if "data" not in resp:
        raise RuntimeError(
            f"[feishu] Failed to get wiki node after move: {resp.get('code')} - {resp.get('msg')}"
        )
    return resp["data"]["node"]["node_token"]


def _get_all_users(token):
    """Get all users in bot's authorized scope."""
    all_users = {}  # {open_id: name}

    scopes = _curl_json(
        [
            "https://open.feishu.cn/open-apis/contact/v3/scopes",
            "-H", f"Authorization: Bearer {token}",
        ]
    ).get("data", {})

    # Get users from each department
    for dept_id in scopes.get("department_ids", []):
        resp = _curl_json(
            [
                f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department"
                f"?department_id={dept_id}&user_id_type=open_id"
                f"&department_id_type=open_department_id&page_size=50",
                "-H", f"Authorization: Bearer {token}",
            ]
        )
        for user in resp.get("data", {}).get("items", []):
            all_users[user["open_id"]] = user.get("name", "unknown")

    # Add directly authorized users
    for uid in scopes.get("user_ids", []):
        if uid not in all_users:
            all_users[uid] = f"user_{uid[-8:]}"

    return all_users


def _filter_recipients(all_users, recipients):
    """Filter users by recipient specification.

    Args:
        all_users: {open_id: name} dict of all users.
        recipients: 'all' or list of names to match.

    Returns:
        Filtered {open_id: name} dict.
    """
    if recipients == "all":
        return all_users
    name_set = set(recipients)
    return {uid: name for uid, name in all_users.items() if name in name_set}


def _broadcast_card(token, users, card):
    """Send interactive card message to users."""
    sent = 0
    for uid, name in users.items():
        body = {
            "receive_id": uid,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        }
        resp = _curl_json(
            [
                "-X", "POST",
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                "-H", f"Authorization: Bearer {token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(body, ensure_ascii=False),
            ]
        )
        sent += 1
        time.sleep(0.1)

    return sent


def publish_to_feishu(
    md_path,
    doc_title,
    wiki_parent_node,
    card_template="blue",
    card_title="Daily Digest",
    card_summary="",
    recipients="all",
    media_dir=None,
):
    """Publish markdown to Feishu wiki and broadcast card to users.

    Args:
        md_path: Path to the markdown file to publish.
        doc_title: Title for the Feishu document.
        wiki_parent_node: Parent wiki node token.
        card_template: Card header color ('blue', 'orange', etc.).
        card_title: Card header title text.
        card_summary: Lark markdown content for card body.
        recipients: 'all' for all users, or list of names.
        media_dir: Optional path to directory with cover.png, tweet-*.png, tweet-*.mp4.

    Returns:
        dict with doc_token, node_token, doc_url, sent_count, images_inserted, videos_inserted.
    """
    # 1. Get credentials and token
    app_id, app_secret = _get_feishu_credentials()
    token = _get_tenant_token(app_id, app_secret)
    print(f"[feishu] Got tenant token")

    # 2. Check for existing doc (update mode)
    existing_node_token = _read_existing_node_token(md_path)
    content = _preprocess_markdown(md_path)

    if existing_node_token:
        # UPDATE MODE: reuse existing doc
        doc_token = _update_existing_doc(
            token, content, doc_title, existing_node_token
        )
        node_token = existing_node_token
        doc_url = f"https://huazhi-ai.feishu.cn/docx/{doc_token}"
        print(f"[feishu] Updated existing doc: {doc_url}")
    else:
        # CREATE MODE: import new doc and move to wiki
        filename = os.path.basename(os.path.expanduser(md_path))
        file_token = _upload_md_file(token, content, filename)
        print(f"[feishu] Uploaded file: {file_token}")

        doc_token = _import_as_docx(token, file_token, doc_title)
        print(f"[feishu] Imported doc: {doc_token}")

        node_token = _move_to_wiki(token, doc_token, wiki_parent_node)
        doc_url = f"https://huazhi-ai.feishu.cn/docx/{doc_token}"
        print(f"[feishu] Moved to wiki: {doc_url}")

    # 4.5 Insert media (images + videos) if media_dir provided
    images_inserted = 0
    videos_inserted = 0
    if media_dir:
        media_dir_expanded = os.path.expanduser(media_dir)
        if os.path.isdir(media_dir_expanded):
            try:
                images_inserted = insert_images_to_doc(token, doc_token, media_dir_expanded)
                videos_inserted = insert_videos_to_doc(token, doc_token, media_dir_expanded)
                print(f"[feishu] Media: {images_inserted} images, {videos_inserted} videos inserted")
            except Exception as e:
                print(f"[feishu] Warning: media insertion failed: {e}")
        else:
            print(f"[feishu] Warning: media_dir not found: {media_dir_expanded}")

    # 5. Build card
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": card_title},
            "template": card_template,
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": card_summary},
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看完整报告"},
                        "url": doc_url,
                        "type": "primary",
                    }
                ],
            },
        ],
    }

    # 6. Broadcast
    all_users = _get_all_users(token)
    target_users = _filter_recipients(all_users, recipients)
    sent = _broadcast_card(token, target_users, card)
    print(f"[feishu] Sent card to {sent}/{len(target_users)} users")

    # 7. Update local frontmatter
    full_path = os.path.expanduser(md_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            original = f.read()
        if "feishu_node_token:" not in original:
            # Insert before closing ---
            sync_time = time.strftime("%Y-%m-%dT%H:%M:%S")
            insert = f"feishu_node_token: {node_token}\nfeishu_sync_time: {sync_time}\n"
            original = original.replace("\n---\n", f"\n{insert}---\n", 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"[feishu] Updated frontmatter with node_token")
        else:
            # Update sync time only
            sync_time = time.strftime("%Y-%m-%dT%H:%M:%S")
            original = re.sub(
                r"feishu_sync_time:\s*\S+",
                f"feishu_sync_time: {sync_time}",
                original,
            )
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"[feishu] Updated sync time")
    except Exception as e:
        print(f"[feishu] Warning: Could not update frontmatter: {e}")

    return {
        "doc_token": doc_token,
        "node_token": node_token,
        "doc_url": doc_url,
        "sent_count": sent,
        "total_users": len(target_users),
        "images_inserted": images_inserted,
        "videos_inserted": videos_inserted,
    }
