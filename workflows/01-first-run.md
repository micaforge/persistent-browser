# Workflow 01: First run

Get the persistent browser up and verify it works. Ends with a loaded page
and a screenshot.

## Steps

1. **Launch:**
   ```bash
   ~/workspace/bin/browser-start
   ```
   This kills any stale instance, ensures `proxy-auth` is running, and
   starts Chromium headless on CDP port 9222.

2. **Verify CDP is up:**
   ```bash
   curl -s http://127.0.0.1:9222/json/version | head -3
   ```
   Expect a JSON block with `"Browser": "Chrome/..."`.

3. **Open a page:**
   ```bash
   ~/workspace/bin/cdp new https://example.com
   ```

4. **Confirm it loaded:**
   ```bash
   ~/workspace/bin/cdp tabs
   ```
   Expect the tab title (not `about:blank`).

## If it fails

- CDP not responding → check `/tmp/chrome-cdp.log`
- Page stays blank → proxy issue; see `references/troubleshooting.md`
- Port 9222 in use → `browser-start` kills stale instances; if stuck,
  the `chrome-cleanup` hook revives it within 20 min.
