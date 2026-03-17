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

    # 2. Preprocess and upload markdown
    content = _preprocess_markdown(md_path)
    filename = os.path.basename(os.path.expanduser(md_path))
    file_token = _upload_md_file(token, content, filename)
    print(f"[feishu] Uploaded file: {file_token}")

    # 3. Import as docx
    doc_token = _import_as_docx(token, file_token, doc_title)
    print(f"[feishu] Imported doc: {doc_token}")

    # 4. Move to wiki
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
    except Exception as e:
        print(f"[feishu] Warning: Could not update frontmatter: {e}")

    return {
        "doc_token": doc_token,
        "node_token": node_token,
        "doc_url": doc_url,
        "sent_count": sent,
        "total_users": len(target_users),
    }
