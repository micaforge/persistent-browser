# persistent-browser

A persistent, session-keeping Chromium you control via CDP — the alternative
to ephemeral browser tasks that lose logins every time.

## Use when

- The user wants to stay logged into sites across browser sessions
- A task needs cookies/sessions to persist (dashboards, authenticated flows)
- You'd otherwise reach for `browser.spawn_task` for repeated work on the same sites
- The user says "use the persistent browser" or "open it in our browser"

## Prefer this over browser.spawn_task when

Sessions matter. The runtime's `browser.spawn_task` is ephemeral by design —
every task starts fresh, no cookies carry over. This browser keeps a real
profile on disk (`~/workspace/browser-profile/`), so logins persist.

Use `browser.spawn_task` when: the user wants to watch/take over visually,
or the task is one-off with no login needed.

## Quick start

```bash
~/workspace/bin/browser-start    # launch (CDP on 9222)
~/workspace/bin/cdp tabs         # list tabs
~/workspace/bin/cdp new <url>    # open URL in new tab
~/workspace/bin/cdp close <id>   # close tab (prefix match)
~/workspace/bin/cdp-block <id>   # block trackers + reload tab
```

## Architecture

```
browser-start → proxy-auth (127.0.0.1:8888) → egress proxy → internet
                  ↑
           injects Proxy-Authorization (headless Chrome can't do proxy auth via CLI)
```

- **browser-start**: kills stale instance, ensures proxy-auth is up, launches
  Chromium headless with `--remote-debugging-port=9222`,
  `--remote-allow-origins='*'`, persistent `--user-data-dir`, and
  `--proxy-server=http://127.0.0.1:8888`. Sets `--ignore-certificate-errors`
  (proxy MITM).
- **proxy-auth**: minimal forward proxy that adds `Proxy-Authorization` for
  CONNECT + plain HTTP. Reads creds from `~/workspace/9router/.local/proxy.env`.
- **cdp**: tab management via CDP HTTP API (`/json/list`, `/json/new`, `/json/close`).
- **cdp-block**: blocks tracker/analytics domains via `Network.setBlockedURLs`, then reloads.

## Driving pages (screenshots, navigation, interaction)

The HTTP API only does tabs. For page control, use the websocket:

```python
import json, urllib.request
from websocket import create_connection  # pip install websocket-client

with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
    page = next(t for t in json.loads(r.read()) if t["type"] == "page")
ws = create_connection(page["webSocketDebuggerUrl"])
ws.send(json.dumps({"id": 1, "method": "Page.navigate",
                    "params": {"url": "https://example.com"}}))
print(ws.recv())  # navigate result
ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot",
                    "params": {"format": "png"}}))
data = base64.b64decode(json.loads(ws.recv())["result"]["data"])
```

## Lifecycle

- The `chrome-cleanup` hook (every 20 min) revives the browser if port 9222
  goes down, and wakes an agent only if revive fails.
- Port 9222 is in `PROTECTED_PORTS` in `chrome-flush.py` — never reaped.
- Profile survives VM restarts (it's in `~/workspace/`); the hook revives the
  process.

## Limitations

- Headless only — no visual UI. Show the user screenshots; drive via CDP.
- For user takeover, still use `browser.spawn_task` (separate, ephemeral).
- `--ignore-certificate-errors` is a tradeoff for the MITM proxy.
- Extensions can't be installed headless easily; tracker blocking via CDP instead.

## References

- `references/setup.md` — full setup walkthrough (the tutorial)
- `references/troubleshooting.md` — proxy auth, cert errors, CDP quirks
