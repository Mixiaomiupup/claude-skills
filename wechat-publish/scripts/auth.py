#!/usr/bin/env python3
"""wx_auth — 通过 CDP 从系统浏览器获取微信公众号登录凭证。

用法:
    python3 auth.py                    # 默认 Edge 端口 9224
    python3 auth.py --port 9222        # 指定 CDP 端口

输出: JSON {"token": "...", "cookie": "..."} 到 stdout

依赖: pip install websockets
"""

import argparse
import asyncio
import json
import re
import sys
import urllib.request


async def get_credentials(port: int = 9224) -> dict:
    """连接 CDP，导航到微信后台，提取 token 和 cookie。"""
    import websockets

    # 1. 找到微信后台 tab（或用第一个 tab）
    tabs = json.loads(urllib.request.urlopen(f"http://localhost:{port}/json").read())
    wx_tab = None
    for t in tabs:
        if "mp.weixin" in t.get("url", "") and "webSocketDebuggerUrl" in t:
            wx_tab = t
            break
    if not wx_tab:
        wx_tab = [t for t in tabs if t.get("type") == "page" and "webSocketDebuggerUrl" in t][0]

    ws_url = wx_tab["webSocketDebuggerUrl"]
    msg_id = 1

    async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
        # 2. 导航到后台首页
        if "mp.weixin" not in wx_tab.get("url", ""):
            await ws.send(
                json.dumps({"id": msg_id, "method": "Page.navigate", "params": {"url": "https://mp.weixin.qq.com/"}})
            )
            msg_id += 1
            await ws.recv()
            await asyncio.sleep(4)

        # 3. 提取 token（从 URL 或页面 JS）
        token = None
        for _ in range(5):
            await ws.send(
                json.dumps(
                    {"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": "window.location.href"}}
                )
            )
            msg_id += 1
            r = json.loads(await ws.recv())
            url = r.get("result", {}).get("result", {}).get("value", "")
            m = re.search(r"token=(\d+)", url)
            if m:
                token = m.group(1)
                break
            await asyncio.sleep(2)

        # 4. 提取 cookie
        await ws.send(json.dumps({"id": msg_id, "method": "Network.getCookies"}))
        msg_id += 1
        r = json.loads(await ws.recv())
        cookies = r.get("result", {}).get("cookies", [])
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies if "mp.weixin" in c.get("domain", ""))

        return {"token": token or "", "cookie": cookie_str}


def main():
    ap = argparse.ArgumentParser(prog="wx_auth", description="获取微信公众号登录凭证")
    ap.add_argument("--port", type=int, default=9224, help="CDP 端口（默认 9224）")
    args = ap.parse_args()

    creds = asyncio.run(get_credentials(args.port))
    if not creds["token"]:
        print("ERROR: 未获取到 token，请确认已登录微信后台", file=sys.stderr)
        sys.exit(1)
    if not creds["cookie"]:
        print("ERROR: 未获取到 cookie", file=sys.stderr)
        sys.exit(1)

    json.dump(creds, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
