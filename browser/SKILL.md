---
name: browser
description: Minimal Chrome DevTools Protocol tools for browser automation and scraping. Use when you need to start Chrome, navigate pages, execute JavaScript, take screenshots, or interactively pick DOM elements.
---

# Browser Tools

Minimal CDP tools for collaborative site exploration and scraping.

**IMPORTANT**: All scripts are located in `~/.claude/skills/browser/` and must be called with full paths, or can be called as `browser-start.js`, `browser-nav.js`, etc. if the directory is in PATH.

## Start Chrome

```bash
~/.claude/skills/browser/browser-start.js              # Fresh profile
~/.claude/skills/browser/browser-start.js --profile    # Copy your profile (cookies, logins)
```

Start Chrome on `:9222` with remote debugging.

## Navigate

```bash
~/.claude/skills/browser/browser-nav.js https://example.com
~/.claude/skills/browser/browser-nav.js https://example.com --new
```

Navigate current tab or open new tab.

## Evaluate JavaScript

```bash
~/.claude/skills/browser/browser-eval.js 'document.title'
~/.claude/skills/browser/browser-eval.js 'document.querySelectorAll("a").length'
```

Execute JavaScript in active tab (async context).

**IMPORTANT**: The code must be a single expression or use IIFE for multiple statements:

- Single expression: `'document.title'`
- Multiple statements: `'(() => { const x = 1; return x + 1; })()'`
- Avoid newlines in the code string - keep it on one line

## Screenshot

```bash
~/.claude/skills/browser/browser-screenshot.js
```

Screenshot current viewport, returns temp file path.

## Pick Elements

```bash
~/.claude/skills/browser/browser-pick.js "Click the submit button"
```

Interactive element picker. Click to select, Cmd/Ctrl+Click for multi-select, Enter to finish.

## Usage Notes

- Start Chrome first before using other tools
- The `--profile` flag syncs your actual Chrome profile so you're logged in everywhere
- JavaScript evaluation runs in an async context in the page
- Pick tool allows you to visually select DOM elements by clicking on them

```

## Workflow recipe

1. **Start Chrome** with `browser-start.js --profile` to mirror your authenticated state.
2. **Drive navigation** via `browser-nav.js https://target.app` or open secondary tabs with `--new`.
3. **Inspect the DOM** using `browser-eval.js` for quick counts, attribute checks, or extracting JSON payloads.
4. **Capture artifacts** with `browser-screenshot.js` for visual proof or `browser-pick.js` when you need precise selectors or text snapshots.
5. **Return the gathered evidence** (file paths, DOM metadata, query outputs) in your session summary or PR description.

This workflow keeps the agent focused on the current browsing context and avoids shipping raw credentials or cookies outside your machine.

## Verification

- `~/.claude/skills/browser/browser-start.js --profile` should print `✓ Chrome started on :9222 with your profile`.
- `~/.claude/skills/browser/browser-nav.js https://example.com` should confirm navigation.
- `~/.claude/skills/browser/browser-eval.js 'document.title'` should echo the current page title.
- `~/.claude/skills/browser/browser-screenshot.js` should output a valid PNG path under your system temp directory.

If any step fails, rerun `browser-start.js`, confirm Chrome is listening on `localhost:9222/json/version`, and ensure `puppeteer-core` is installed.
```
