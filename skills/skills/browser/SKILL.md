---
name: browser
description: Control browser via browser-harness for E2E testing. Thin wrapper — reads upstream skill for full API reference.
---

# browser skill

> **Full API reference**: read `vendor/browser-harness/SKILL.md` before use.

This skill is a thin policy layer for E2E testing of internal web apps.  
All browser control primitives (navigation, clicks, screenshots, DOM, tabs) are documented in the upstream skill.

## Screenshot convention

Screenshots save to `./tmp/` with timestamp filenames.  
Always retrieve the latest path via `get_latest_screenshot()`:

```bash
browser-harness -c '
import os; os.makedirs("tmp", exist_ok=True)
capture_screenshot("tmp/shot.png")
print(get_latest_screenshot())
'
```

Then pass the returned path to `read_file` so the LLM can see the image.

## E2E testing conventions

- Use `new_tab(url)` for all test navigation — never `goto_url()` on the active tab
- Always `wait_for_load()` after navigation
- Screenshot **before** an action (to locate targets) and **after** (to verify result)
- On assertion failure: capture screenshot as evidence, then report FAIL — do not retry blindly
- For login-gated apps: stop and ask the user for credentials

## Interaction skills

### Screenshots

`capture_screenshot()` writes a PNG of the current viewport in **device pixels** — on a 2× display a 2296×1143 CSS viewport produces a 4592×2286 PNG.

Two things to watch:

1. **Click coordinates are CSS pixels.** Divide screenshot pixel coordinates by `js("window.devicePixelRatio")` before passing to `click_at_xy()`.
2. **Some LLMs reject images > 2000 px per side.** Pass `max_dim=1800` to downscale:
   ```python
   capture_screenshot("tmp/shot.png", max_dim=1800)
   ```
   Safe to leave on every shot — only downscales when needed.

Use `full=True` only when you need content below the fold (much larger and slower).

---

### Tabs

Use **CDP for control**, **UI automation for user-visible order**.

```python
tabs = list_tabs()                    # includes chrome:// pages
real_tabs = list_tabs(include_chrome=False)
tid = new_tab("https://example.com")  # create + attach
switch_tab(tid)                       # attach harness to tab
cdp("Target.activateTarget", targetId=tid)  # show it in Chrome
print(current_tab())
print(page_info())
```

Rules:
- `switch_tab()` alone does not visibly change Chrome — also call `Target.activateTarget` if the user needs to see it
- `list_tabs()` includes `chrome://newtab/` by default; use `include_chrome=False` for real pages only
- If `page_info()` returns `w=0 h=0`, you may be attached to the wrong target

---

### Dialogs

Browser dialogs (`alert`, `confirm`, `prompt`, `beforeunload`) freeze the JS thread.

**Detection:** `page_info()` returns `{"dialog": {"type", "message", ...}}` when a dialog is open. Check for it after any action that might trigger one.

**Reactive (preferred) — dismiss via CDP:**
```python
cdp("Page.handleJavaScriptDialog", accept=True)   # OK / Leave
cdp("Page.handleJavaScriptDialog", accept=False)  # Cancel / Stay

# Read what the dialog said
events = drain_events()
for e in events:
    if e["method"] == "Page.javascriptDialogOpening":
        print(e["params"]["type"], e["params"]["message"])
```

**Proactive — stub via JS (when expecting multiple dialogs):**
```python
js("""
window.__dialogs__=[];
window.alert=m=>window.__dialogs__.push(String(m));
window.confirm=m=>{window.__dialogs__.push(String(m));return true;};
""")
msgs = js("window.__dialogs__||[]")
```
Note: stubs are lost on navigation; `confirm()` always returns `true`; does NOT handle `beforeunload`.

**beforeunload (navigate away from unsaved forms):**
```python
goto_url("https://new-url.com")
try:
    cdp("Page.handleJavaScriptDialog", accept=True)  # click Leave
except:
    pass  # no dialog — normal
```

---

### Dropdowns

Split dropdowns into four types and handle each differently:

| Type | How to identify | How to interact |
|---|---|---|
| Native `<select>` | `js("el.tagName") == 'SELECT'` | `js("el.value = 'x'; el.dispatchEvent(new Event('change', {bubbles:true}))")` |
| Custom overlay | Opens a detached list/popover on click | Click trigger → wait → screenshot to find option → `click_at_xy` |
| Searchable combobox | Has an `<input>` inside | Click → `type_text(query)` → wait for results → click option |
| Virtualized menu | List renders only visible rows | Scroll inside the container, not the page |

Always re-screenshot after opening — option geometry often appears late (async render).

---

### Iframes

`click_at_xy(x, y)` passes through iframes automatically at the compositor level — no extra work for coordinate clicks.

For DOM reads inside a same-origin iframe, use `contentDocument` / `contentWindow`:
```python
js("document.querySelector('iframe').contentDocument.querySelector('.target').textContent")
```

For cross-origin iframes, use `iframe_target(url_substr)` to get the target ID, then pass it to `js(..., target_id=...)`.

**Coordinate warning:** iframe-local coordinates differ from page coordinates. Use screenshots to read the actual pixel positions rather than computing offsets manually.

---

### Uploads

Use `upload_file(selector, path)` with an absolute path:

```python
upload_file("input[type=file]", "/absolute/path/to/file.pdf")
```

Uses `DOM.setFileInputFiles` via CDP — no file dialog interaction needed. `path` must be absolute (use `os.path.abspath()` or `pathlib.Path(...).resolve()` if needed).

---

### Connection & startup

**Startup sequence:**
```python
tabs = list_tabs()
tab = ensure_real_tab()   # attaches to a real page, skips omnibox popups
```

**Stale session recovery:** Call `ensure_real_tab()` when the current tab is chrome:// or stale. The daemon also auto-recovers on the next CDP call.

**Bring Chrome to front (macOS):**
```python
import subprocess
subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])
```

**Omnibox popup trap:** When Chrome opens fresh, CDP may see `chrome://omnibox-popup.top-chrome/` as a fake page target. `ensure_real_tab()` filters this out automatically.