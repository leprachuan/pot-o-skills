---
name: mac-control
description: Use when you need to access your macOS devices - read Apple Notes, control browsers with Playwright, take screenshots, execute shell commands, or automate tasks on registered Macs via SSH
---

# Mac Control

## Overview

Remote control your macOS devices via SSH. Register Macs once, then control them by name, alias, or index to access Notes, automate browsers with Playwright, capture screenshots, and execute commands.

**Core principle:** Multi-Mac support with flexible selection and unified automation interface.

## When to Use

- Need to read/search Apple Notes on your Mac
- Want to navigate a website and take screenshots on the Mac
- Need to click elements, fill forms, or extract data from web pages
- Want to capture the Mac screen
- Need to run shell commands on your Mac remotely
- Managing multiple Macs and need unified control

## Mac Registration

Register each Mac once in `~/.mac-control/macs.json`:

```json
{
  "name": "macbook-air-m4",
  "hostname": "192.168.1.100",
  "ssh_user": "username",
  "ssh_key_path": "~/.ssh/id_rsa",
  "aliases": ["air", "laptop", "main"]
}
```

**Select Mac by:** name, alias, or index number (1-based)

## Quick Reference

| Operation | Method | Example |
|-----------|--------|---------|
| **Navigate URL** | Playwright headless | "Go to apple.com on my Mac and screenshot it" |
| **Screenshot page** | Playwright screenshot | "Take a screenshot of google.com on my MacBook" |
| **Click element** | CSS selector click | "Click the login button on the page" |
| **Extract text** | CSS selector extract | "Get all the headlines from that page" |
| **Screen capture** | macOS screencapture | "Capture my Mac screen" |
| **Fetch note** | AppleScript search | "Get 'Dinner Plans' note from my MacBook" |
| **Shell command** | SSH execute | "Check disk usage on my Mac" |

## Browser Automation (Playwright)

Full headless Chromium browser control via Playwright, running on the Mac:

### Navigate + Screenshot
```bash
python3 copilot/mac_control.py --host fosterlipkey@192.168.1.51 \
  --browser-navigate "https://example.com" -o /tmp/page.png
```

### Screenshot Only
```bash
python3 copilot/mac_control.py --host fosterlipkey@192.168.1.51 \
  --browser-screenshot "https://example.com" --full-page -o /tmp/fullpage.png
```

### Click + Screenshot
```bash
python3 copilot/mac_control.py --host fosterlipkey@192.168.1.51 \
  --browser-click "https://example.com" --selector "button.submit" -o /tmp/after_click.png
```

### Extract Text
```bash
python3 copilot/mac_control.py --host fosterlipkey@192.168.1.51 \
  --browser-extract "https://example.com" --selector "h1, h2, h3"
```

### How It Works

1. Agent SSHs to Mac → invokes `~/bin/mac_browser_helper.py`
2. Helper launches headless Chromium via Playwright
3. Executes the requested action (navigate, click, extract, etc.)
4. Takes screenshot if requested
5. Returns JSON result to lepbuntu
6. Agent SCPs screenshot back for display

## Screen Capture

Captures the actual macOS desktop (not just browser).

```bash
python3 copilot/mac_control.py --host fosterlipkey@192.168.1.51 \
  --screen-capture -o /tmp/mac_screen.png
```

**⚠️ Requires Screen Recording permission:** In System Settings > Privacy & Security > Screen Recording, grant permission to `sshd-keygen-wrapper`. Without this, screen capture won't work (browser screenshots still work fine via Playwright).

## Capabilities

### 1. Browser Automation (Playwright)
- Navigate to any URL
- Take viewport or full-page screenshots
- Click elements by CSS selector
- Type into form fields
- Extract text from elements
- Run custom JavaScript
- All screenshots auto-fetched to lepbuntu via SCP

### 2. Screen Capture (macOS native)
- Full desktop capture via `screencapture`
- Requires TCC Screen Recording permission
- Falls back gracefully with instructions if not permitted

### 3. Apple Notes Access
- Fetch notes by title or search term
- List all available notes
- Get note content and metadata

### 4. Shell Commands
- Execute arbitrary shell commands
- Get command output
- Run automation scripts

## Common Patterns

**Pattern 1: Screenshot a website**
```
User: "Screenshot apple.com on my MacBook"
→ SSH to Mac → Playwright navigates → screenshots → SCP back → display
```

**Pattern 2: Extract data from a page**
```
User: "Get all the product names from that Amazon page"
→ SSH to Mac → Playwright navigates → extract by selector → return text
```

**Pattern 3: Read a specific note**
```
User: "What's for dinner on my MacBook?"
→ SSH to Mac → AppleScript → search Notes → return content
```

## Integration

- **SSH Access:** Key-based auth (fosterlipkey@192.168.1.51)
- **Notes Access:** AppleScript bridge over SSH
- **Browser Automation:** Playwright Python + Chromium (installed on Mac)
- **Screen Capture:** macOS `screencapture` (needs TCC permission)
- **Configuration:** `~/.mac-control/macs.json` file
- **Helper Script:** `~/bin/mac_browser_helper.py` on Mac

## Red Flags - STOP

- Mac not responding to SSH → Check network/SSH setup
- Playwright errors → Run `python3 -m playwright install chromium` on Mac
- Screen capture fails → Grant Screen Recording permission in System Settings
- Note not found → Try broader search term
- Timeout → Check Mac availability

## Selection

When selecting a Mac, you can use:
- **Full name:** "foster-macbook"
- **Alias:** "mac", "macbook", "main"
- **Index:** 1 (first Mac)
- **Shorthand:** Just say "my Mac" or "my MacBook"
