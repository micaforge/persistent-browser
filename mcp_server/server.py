#!/usr/bin/env python3
"""MCP server for persistent-browser — exposes mica browser caps as MCP tools.

Stdio transport. Each tool shells out to `mica browser <cap>` and returns
the result. This is a thin wrapper; all browser logic lives in the caps.
"""
import base64
import json
import os
import re
import socket
import subprocess
import urllib.parse
import urllib.request

from mcp.server.mcpserver import MCPServer

MICA = os.path.expanduser("~/workspace/bin/mica")
EVAL_CAP = os.path.expanduser("~/workspace/caps/browser/eval")
CDP = "http://127.0.0.1:9222"

mcp = MCPServer("persistent-browser")


def run_cap(*args, timeout=60):
    p = subprocess.run([MICA, "browser", *args],
                       capture_output=True, text=True, timeout=timeout)
    return p.stdout.strip() or p.stderr.strip()


def get_tabs():
    with urllib.request.urlopen(f"{CDP}/json/list", timeout=10) as r:
        return json.loads(r.read())


def resolve_tab(tab_id=None):
    tabs = [t for t in get_tabs() if t["type"] == "page"]
    if not tab_id:
        if not tabs:
            raise ValueError("no page tabs open")
        return tabs[0]["id"]
    for t in get_tabs():
        if t["id"] == tab_id or t["id"].startswith(tab_id):
            return t["id"]
    raise ValueError(f"tab {tab_id} not found")


def cdp_screenshot_png(tab_id):
    """Capture a PNG screenshot via CDP Page.captureScreenshot."""
    tabs = {t["id"]: t for t in get_tabs()}
    ws_url = tabs[tab_id]["webSocketDebuggerUrl"]
    parts = urllib.parse.urlparse(ws_url)
    host, port = parts.hostname, parts.port or 80
    key = base64.b64encode(os.urandom(16)).decode()
    s = socket.create_connection((host, port), timeout=30)
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    s.sendall(
        f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\n"
        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        .encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)
    msg = json.dumps({"id": 1, "method": "Page.captureScreenshot",
                      "params": {"format": "png"}}).encode()
    mask = os.urandom(4)
    frame = bytes([0x81, 0x80 | (len(msg) & 0x7F)]) + mask
    frame += bytes(b ^ mask[i % 4] for i, b in enumerate(msg))
    s.sendall(frame)
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
        if b'"data"' in data:
            break
    s.close()
    m = re.search(rb'"data":"([A-Za-z0-9+/=]+)"', data)
    if not m:
        raise RuntimeError("no image data in CDP response")
    return base64.b64decode(m.group(1))


@mcp.tool()
def browser_start() -> str:
    """Launch the persistent Chromium browser (CDP on 127.0.0.1:9222).
    Idempotent — safe to call if already running."""
    return run_cap("start", timeout=60)


@mcp.tool()
def browser_eval(js: str, tab_id: str = "", url: str = "") -> str:
    """Evaluate a JavaScript expression in a browser tab. Returns JSON result.
    tab_id: full or prefix; omit for first page tab. url: open in new tab first."""
    if url:
        return run_cap("eval", "--new", url, js, timeout=60)
    tid = resolve_tab(tab_id or None)
    p = subprocess.run([EVAL_CAP, tid, js],
                       capture_output=True, text=True, timeout=60)
    return p.stdout.strip() or p.stderr.strip()


@mcp.tool()
def browser_screenshot(url: str = "", width: int = 1280, height: int = 800) -> str:
    """Screenshot a page. Returns base64 PNG. url: omit for current tab."""
    if url:
        req = urllib.request.Request(
            f"{CDP}/json/new?" + urllib.parse.urlencode({"url": url}),
            method="PUT")
        with urllib.request.urlopen(req, timeout=15) as r:
            tab = json.loads(r.read())
        tid = tab["id"]
    else:
        tid = resolve_tab(None)
    png = cdp_screenshot_png(tid)
    return base64.b64encode(png).decode()


@mcp.tool()
def browser_block(action: str, pattern: str = "") -> str:
    """Manage request blocking rules. action: list, add, or remove."""
    args = ["block", action] + ([pattern] if pattern else [])
    return run_cap(*args, timeout=30)


@mcp.tool()
def browser_cdp(subcommand: str, arg: str = "") -> str:
    """Raw CDP control. subcommand: tabs (list, full IDs) or new (open URL)."""
    if subcommand == "tabs":
        tabs = [t for t in get_tabs() if t["type"] == "page"]
        return "\n".join(
            f"{t['id']}  {t['title'][:60]}  {t['url'][:80]}" for t in tabs
        ) or "no page tabs"
    args = ["cdp", subcommand] + ([arg] if arg else [])
    return run_cap(*args, timeout=30)


if __name__ == "__main__":
    mcp.run(transport="stdio")
