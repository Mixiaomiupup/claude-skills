#!/usr/bin/env python3
"""wx_upload — 上传图片到微信公众号 CDN。

用法:
    python3 upload.py --token TOKEN --cookie COOKIE image1.png image2.png
    python3 upload.py --creds /tmp/wx_creds.json image1.png  # 从 auth.py 输出读取

输出: JSON {"filename": {"cdn_url": "...", "fileid": "..."}, ...} 到 stdout

依赖: 无（纯 Python 标准库）
"""

import argparse
import http.client
import json
import mimetypes
import os
import sys
import uuid


def upload_image(path: str, token: str, cookie: str) -> dict:
    """上传单张图片到微信 CDN。

    Returns: {"cdn_url": "https://mmbiz.qpic.cn/...", "fileid": "..."}
    """
    boundary = uuid.uuid4().hex
    filename = os.path.basename(path)
    mime = mimetypes.guess_type(path)[0] or "image/png"

    with open(path, "rb") as f:
        file_data = f.read()

    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        + file_data
        + f"\r\n--{boundary}--\r\n".encode()
    )

    url = (
        f"/cgi-bin/filetransfer?action=upload_material&f=json"
        f"&writetype=doublewrite&groupid=1&token={token}"
        f"&lang=zh_CN&t=ajax-editor-upload-loc-img"
    )

    import time

    last_err = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 * attempt)
        try:
            conn = http.client.HTTPSConnection("mp.weixin.qq.com", timeout=30)
            conn.request(
                "POST",
                url,
                body=body,
                headers={
                    "Cookie": cookie,
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                },
            )
            resp = conn.getresponse()
            raw = resp.read()
            conn.close()
            try:
                result = json.loads(raw)
            except Exception as e:
                last_err = f"non-JSON response (status={resp.status}, body[:200]={raw[:200]!r})"
                continue
            cdn_url = result.get("cdn_url", "")
            fileid = result.get("content", "")
            if not cdn_url:
                last_err = f"no cdn_url: {result}"
                continue
            return {"cdn_url": cdn_url, "fileid": fileid}
        except Exception as e:
            last_err = str(e)
            continue
    print(f"WARNING: 上传失败 {filename} (3 retries): {last_err}", file=sys.stderr)
    return {"cdn_url": "", "fileid": ""}


def main():
    ap = argparse.ArgumentParser(prog="wx_upload", description="上传图片到微信 CDN")
    ap.add_argument("images", nargs="+", help="图片文件路径")
    ap.add_argument("--token", help="微信 token")
    ap.add_argument("--cookie", help="微信 cookie")
    ap.add_argument(
        "--creds", help="auth.py 输出的 JSON 文件路径（替代 --token/--cookie）"
    )
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

    # 上传
    results = {}
    for img_path in args.images:
        if not os.path.exists(img_path):
            print(f"SKIP: {img_path} 不存在", file=sys.stderr)
            continue
        name = os.path.basename(img_path)
        info = upload_image(img_path, token, cookie)
        results[name] = info
        print(f"  {name} → {info['cdn_url'][:60]}...", file=sys.stderr)

    json.dump(results, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
