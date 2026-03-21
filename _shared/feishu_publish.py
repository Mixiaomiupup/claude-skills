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


WIKI_SPACE_ID = "7559794508562251778"


def _move_to_wiki(token, doc_token, parent_node_token):
    """Move document into wiki knowledge base."""
    _curl_json(
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

    # Wait for async move to complete, then get node_token
    time.sleep(3)
    resp = _curl_json(
        [
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={doc_token}&obj_type=docx",
            "-H", f"Authorization: Bearer {token}",
        ]
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

    Returns:
        dict with doc_token, node_token, doc_url, sent_count.
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
    }
