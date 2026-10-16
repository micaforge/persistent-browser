# Workflow 02: Tracker blocking

Sites load analytics, ad networks, and consent frameworks that slow pages
and pollute screenshots. Block them per-tab via CDP.

## Steps

1. **Find the tab:**
   ```bash
   ~/workspace/bin/cdp tabs
   ```

2. **Block trackers and reload:**
   ```bash
   ~/workspace/bin/cdp-block <tab-id-prefix>
   ```
   Blocks ~25 known tracker/ad/analytics domains via
   `Network.setBlockedURLs`, then reloads the tab.

3. **Verify:** reload the page, take a screenshot. Consent popups and
   tracker requests should be gone.

## Customizing

Edit the `BLOCKED` list in `~/workspace/bin/cdp-block` to add domains.
Patterns support `*` wildcards (CDP URL pattern syntax).

## When to use

- Before screenshots for READMEs or demos
- When a page is slow or shows cookie/consent walls
- When automating flows that shouldn't phone home to analytics
