#!/usr/bin/env python3
"""Broadcast card message to all visible Feishu users.

Usage:
    python3 feishu_broadcast.py \
      --title "文章标题" \
      --author "作者名" \
      --summary "要点1|要点2|要点3" \
      --source-url "https://原文" \
      --doc-url "https://huazhi-ai.feishu.cn/docx/xxx"

    # By department:
    python3 feishu_broadcast.py ... --department "后场-研发"
"""

import argparse
import json
import os
import subprocess
import sys
import time


KNOWN_DEPARTMENTS = {
    "后场-研发": "od-44778258d5c056a8bc746c1c9b92032e",
    "后场-研发（实习生+顾问）": "od-4d23fdda045eb2310bc154aa672ca2e0",
    "前场-业务": "od-d298abfccd172a73eda5f7194bd1812f",
    "具身语料服务": "od-32952337c6dd7b4fed51d8220aeb0080",
    "职能支撑": "od-d45883aa0889ddf7c7af6c9c3d3a7bc3",
}


def get_credentials():
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
    return curl_json([
        "-X", "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"app_id": app_id, "app_secret": app_secret}),
    ])["tenant_access_token"]


def get_all_visible_users(token: str) -> dict[str, str]:
    """Get all users visible to the bot. Returns {open_id: name}."""
    all_users = {}

    scopes = curl_json([
        "https://open.feishu.cn/open-apis/contact/v3/scopes",
        "-H", f"Authorization: Bearer {token}",
    ]).get("data", {})

    for dept_id in scopes.get("department_ids", []):
        resp = curl_json([
            f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department"
            f"?department_id={dept_id}&user_id_type=open_id"
            f"&department_id_type=open_department_id&page_size=50",
            "-H", f"Authorization: Bearer {token}",
        ])
        for user in resp.get("data", {}).get("items", []):
            all_users[user["open_id"]] = user.get("name", "unknown")

    for uid in scopes.get("user_ids", []):
        if uid not in all_users:
            all_users[uid] = f"user_{uid[-8:]}"

    return all_users


def get_department_users(token: str, dept_names: list[str]) -> dict[str, str]:
    """Get users from specific departments. Returns {open_id: name}."""
    all_users = {}
    for name in dept_names:
        dept_id = KNOWN_DEPARTMENTS.get(name)
        if not dept_id:
            print(f"  WARN: Unknown department '{name}', skipping", file=sys.stderr)
            continue
        resp = curl_json([
            f"https://open.feishu.cn/open-apis/contact/v3/users/find_by_department"
            f"?department_id={dept_id}&user_id_type=open_id"
            f"&department_id_type=open_department_id&page_size=50",
            "-H", f"Authorization: Bearer {token}",
        ])
        for user in resp.get("data", {}).get("items", []):
            all_users[user["open_id"]] = user.get("name", "unknown")
    return all_users


def build_card(title: str, author: str, summary: str, source_url: str, doc_url: str) -> dict:
    bullets = "\n".join(f"• {s.strip()}" for s in summary.split("|"))
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**作者**: {author}\n\n---\n\n**核心要点**:\n{bullets}",
                },
            },
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "查看原文"}, "url": source_url, "type": "default"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "知识库全文"}, "url": doc_url, "type": "primary"},
                ],
            },
        ],
    }


def broadcast(token: str, users: dict[str, str], card: dict) -> tuple[int, int]:
    success, fail = 0, 0
    for uid, name in users.items():
        body = {
            "receive_id": uid,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        }
        resp = curl_json([
            "-X", "POST",
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(body, ensure_ascii=False),
        ])
        if resp.get("code") == 0:
            success += 1
            print(f"  ✓ {name}")
        else:
            fail += 1
            print(f"  ✗ {name}: {resp.get('msg')}")
        time.sleep(0.1)
    return success, fail


def main():
    parser = argparse.ArgumentParser(description="Broadcast card to Feishu users")
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--summary", required=True, help="要点用 | 分隔")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--doc-url", default="")
    parser.add_argument("--department", nargs="*", help="指定部门名称（不传则全量广播）")
    args = parser.parse_args()

    token = get_token()

    if args.department:
        users = get_department_users(token, args.department)
        print(f"Department targets: {len(users)} users")
    else:
        users = get_all_visible_users(token)
        print(f"All visible users: {len(users)}")

    card = build_card(args.title, args.author, args.summary, args.source_url, args.doc_url)
    success, fail = broadcast(token, users, card)
    print(f"\nDone: {success} sent, {fail} failed")


if __name__ == "__main__":
    main()
