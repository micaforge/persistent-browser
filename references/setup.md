# Persistent Browser: Setup Walkthrough

How to get a session-keeping Chromium running on a headless VM behind an
authenticated egress proxy — and control it via CDP.

## The problem

`browser.spawn_task` gives you a fresh browser every time. Log in, do work,
close it — next task, you're logged out again. For anything that needs
persistent sessions (dashboards, authenticated tools, frequent sites), that's
friction on every run.

## The solution

Run your own Chromium with `--remote-debugging-port` and a persistent
`--user-data-dir`. Control it over CDP. Sessions live on disk, survive
restarts.

## Step 1: Launch Chromium

```bash
/opt/meta-chromium/chrome --headless --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --remote-allow-origins='*' \
  --user-data-dir=~/workspace/browser-profile \
  --no-first-run --no-default-browser-check \
  about:blank
```

Verify: `curl -s http://127.0.0.1:9222/json/version`

The `--remote-allow-origins='*'` is required — without it, websocket
connections get 403.

## Step 2: Handle the egress proxy

If your VM routes through an authenticated proxy, headless Chrome can't
prompt for credentials. The fix: a tiny local forward proxy that injects
`Proxy-Authorization`.

See `bin/proxy-auth` — ~120 lines of Python, handles CONNECT + plain HTTP,
reads upstream creds from a file, listens on 127.0.0.1:8888.

Then point Chrome at it:

```bash
--proxy-server="http://127.0.0.1:8888" \
--ignore-certificate-errors   # proxy MITM certs
```

## Step 3: Control via CDP

HTTP API (no websocket needed) for tabs:

```bash
curl -s http://127.0.0.1:9222/json/list          # list tabs
curl -s -X PUT "http://127.0.0.1:9222/json/new?url=https://example.com"  # new tab
curl -s http://127.0.0.1:9222/json/close/<id>    # close tab
```

Websocket for page control (navigate, screenshot, evaluate):

```python
from websocket import create_connection
import json, urllib.request, base64

targets = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:9222/json/list").read())
page = next(t for t in targets if t["type"] == "page")
ws = create_connection(page["webSocketDebuggerUrl"])

# Navigate
ws.send(json.dumps({"id": 1, "method": "Page.navigate",
                    "params": {"url": "https://example.com"}}))
print(ws.recv())

# Screenshot
ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot",
                    "params": {"format": "png"}}))
img = base64.b64decode(json.loads(ws.recv())["result"]["data"])
open("/tmp/shot.png", "wb").write(img)
```

## Step 4: Block trackers

Sites load analytics, ads, and consent popups. Block them per-tab:

```python
ws.send(json.dumps({"id": 3, "method": "Network.setBlockedURLs",
    "params": {"urls": ["*google-analytics.com*", "*doubleclick.net*",
                        "*hotjar.com*", "*facebook.net*"]}}))
```

See `bin/cdp-block` for a ready-made list.

## Step 5: Keep it alive

- A cron/hook checks port 9222 every ~20 min and relaunches if down.
- If you have an idle-Chrome reaper, exclude your CDP port.
- The profile directory is the persistent state — back it up if sessions matter.

## What you get

A browser that remembers logins. Open a site, log in once, and it's still
logged in tomorrow. Drive it from scripts, take screenshots, automate flows —
all without re-authenticating.
