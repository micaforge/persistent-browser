# Agent package structure

A micaforge agent package is a distributable unit: a skill + its tools +
the docs that teach when and how to use them. Clone it, and an agent can
pick it up and run.

## Layout

```
<package>/
├── SKILL.md            # entry point: what it is, when to use, quick start
├── bin/                # executables (on PATH when installed)
├── tools/              # libraries, helpers, non-executable support code
├── workflows/          # step-by-step procedures (numbered, e.g. 01-setup.md)
├── references/         # deep docs, tutorials, research, troubleshooting
├── assets/             # icons, banners, screenshots
├── README.md           # public face (GitHub)
└── LICENSE
```

## What goes where

| Dir | Purpose | Example |
|-----|---------|---------|
| `bin/` | Run it. Single-purpose CLIs. | `browser-start`, `cdp` |
| `tools/` | Import it. Shared libs, parsers. | `cdp_client.py` |
| `workflows/` | Follow it. Ordered procedures. | `01-first-run.md`, `02-tracker-blocking.md` |
| `references/` | Learn it. Tutorials, deep dives. | `setup.md`, `troubleshooting.md` |
| `assets/` | See it. Icons, demos. | `icon.png`, `demo.gif` |

## SKILL.md contract

The SKILL.md is the router. It must:

1. **Say when to use this** — the trigger conditions, in plain language.
2. **Give the 30-second quick start** — the commands that cover 80% of use.
3. **Point to workflows/** for multi-step procedures ("to do X, follow `workflows/01-x.md`").
4. **Point to references/** for deep understanding ("how it works: `references/architecture.md`").
5. **Name every bin/ script** with one line on what it does and when to reach for it.

The rule: a new agent (or a future me) should be able to use the package
from SKILL.md alone, and go deeper via the pointers.

## Workflows vs references

- **workflows/**: "do this, then this." Numbered. Assumes the quick start
  worked. Ends with a verifiable result.
- **references/**: "here's how it works." Tutorials, architecture, edge
  cases, troubleshooting. Read when something breaks or needs adapting.

## Distributing

```bash
# Install: clone + link bin/
git clone https://github.com/micaforge/<package>.git
ln -s ~/workspace/projects/micaforge/repos/<package>/bin/* ~/workspace/bin/
```

Or via `mica-scaffold --type agent` which sets up this layout from the template.
