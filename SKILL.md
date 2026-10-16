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
./bin/browser-start    # launch (CDP on 9222)
./bin/cdp tabs         # list tabs
./bin/cdp new <url>    # open URL in new tab
./bin/cdp close <id>   # close tab (prefix match)
./bin/cdp-block <id>   # block trackers + reload tab
```

## Scripts (bin/)

| Script | When to use |
|--------|-------------|
| `browser-start` | First run, or browser is down. Kills stale, ensures proxy, launches. → `workflows/01-first-run.md` |
| `cdp` | Tab management: list, open, close. Daily driver. |
| `cdp-block` | Page is slow, has consent walls, or you need clean screenshots. → `workflows/02-tracker-blocking.md` |
| `proxy-auth` | Runs automatically via `browser-start`. Only touch if egress breaks. |

## Workflows

- `workflows/01-first-run.md` — launch and verify (start here)
- `workflows/02-tracker-blocking.md` — block analytics/ads per tab

## References

- `references/setup.md` — full tutorial: the problem, the proxy fix, CDP patterns
- `SKILL.md` — proxy auth, cert errors, CDP quirks (TODO)

## Architecture

```
browser-start → proxy-auth (127.0.0.1:8888) → egress proxy → internet
                  ↑
           injects Proxy-Authorization (headless Chrome can't do proxy auth via CLI)
```

## Driving pages (screenshots, navigation)

The HTTP API only does tabs. For page control, use the websocket —
see `references/setup.md` for the Python pattern.

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
