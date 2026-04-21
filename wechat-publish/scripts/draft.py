#!/usr/bin/env python3
"""wx_draft — 创建/更新微信公众号草稿。

用法:
    # 创建草稿
    python3 draft.py --token TOKEN --cookie COOKIE \
        --title "标题" --content /tmp/body.html --author "智涌MindSurge"

    # 带封面
    python3 draft.py --creds /tmp/wx_creds.json \
        --title "标题" --content /tmp/body.html \
        --cover-fileid 12345 --cover-cdn "https://mmbiz.qpic.cn/..."

    # 更新已有草稿
    python3 draft.py --creds /tmp/wx_creds.json \
        --title "标题" --content /tmp/body.html \
        --app-msg-id 100000123

输出: JSON {"ret": 0, "appMsgId": "..."} 到 stdout

依赖: 无（纯 Python 标准库）
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request


def create_or_update_draft(
    token: str,
    cookie: str,
    title: str,
    html_content: str,
    author: str = "智涌MindSurge",
    digest: str = "",
    cover_fileid: str = "",
    cover_cdn: str = "",
    app_msg_id: str = "",
) -> dict:
    """创建或更新微信草稿。

    app_msg_id 为空时创建新草稿，非空时更新已有草稿。
    """
    sub = "update" if app_msg_id else "create"
    url = f"https://mp.weixin.qq.com/cgi-bin/operate_appmsg?t=ajax-response&sub={sub}&type=77&token={token}&lang=zh_CN"

    params = {
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "AppMsgId": app_msg_id,
        "count": "1",
        "title0": title,
        "content0": html_content,
        "digest0": (digest or title)[:120],
        "author0": author,
        "writerid0": "0",
        "fileid0": cover_fileid,
        "cdn_url0": cover_cdn,
        "cdn_235_1_url0": cover_cdn,
        "cdn_1_1_url0": cover_cdn,
        "need_open_comment0": "1",
    }

    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Cookie", cookie)
    req.add_header("Referer", f"https://mp.weixin.qq.com/cgi-bin/appmsg?token={token}")
    req.add_header("User-Agent", "Mozilla/5.0")

    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser(prog="wx_draft", description="创建/更新微信草稿")
    ap.add_argument("--token", help="微信 token")
    ap.add_argument("--cookie", help="微信 cookie")
    ap.add_argument("--creds", help="auth.py 输出的 JSON 文件")
    ap.add_argument("--title", required=True, help="文章标题")
    ap.add_argument("--content", required=True, help="HTML 内容文件路径")
    ap.add_argument("--author", default="智涌MindSurge")
    ap.add_argument("--digest", default="", help="文章摘要（默认用标题）")
    ap.add_argument("--cover-fileid", default="", help="封面图 fileid")
    ap.add_argument("--cover-cdn", default="", help="封面图 CDN URL")
    ap.add_argument("--app-msg-id", default="", help="已有草稿 ID（更新模式）")
    args = ap.parse_args()

    # 读取凭证
    if args.creds:
        with open(args.creds) as f:
            creds = json.load(f)
        token, cookie = creds["token"], creds["cookie"]
    elif args.token and args.cookie:
        token, cookie = args.token, args.cookie
    else:
        print("ERROR: 需要 --creds 或 --token + --cookie", file=sys.stderr)
        sys.exit(1)

    # 读取 HTML
    with open(args.content, encoding="utf-8") as f:
        html = f.read()

    result = create_or_update_draft(
        token=token,
        cookie=cookie,
        title=args.title,
        html_content=html,
        author=args.author,
        digest=args.digest,
        cover_fileid=args.cover_fileid,
        cover_cdn=args.cover_cdn,
        app_msg_id=args.app_msg_id,
    )

    ret = result.get("base_resp", {}).get("ret", -1)
    aid = result.get("appMsgId", "")
    if ret == 0:
        print(f"✅ {'更新' if args.app_msg_id else '创建'}成功 appMsgId={aid}", file=sys.stderr)
    else:
        print(f"❌ 失败 ret={ret}", file=sys.stderr)

    json.dump({"ret": ret, "appMsgId": aid}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
