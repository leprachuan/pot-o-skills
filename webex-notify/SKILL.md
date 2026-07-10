---
name: webex-notify
description: Use when you need to send WebEx notifications to flipkey-home-bot - supports markdown formatting, auto-retry with backoff, rate limiting, and message history tracking
---

# WebEx Notify

## Overview

Send WebEx messages to flipkey-home-bot with markdown formatting, auto-retry, and rate limiting. Reliable notification delivery with built-in resilience.

**Core principle:** Simple, reliable WebEx messaging with automatic retries and rate limiting.

## When to Use

- Send WebEx notifications for alerts
- Notify about task completion
- Send formatted messages with markdown
- Need reliable delivery (auto-retry)
- Track message history
- Integrate with schedule-based tasks

## Quick Reference

| Feature | Behavior |
|---------|----------|
| **Send** | Message delivered via WebEx |
| **Format** | Markdown support (`**bold**`, `_italic_`, `` `code` ``) |
| **Retry** | Auto-retry up to 3 times on failure |
| **Rate Limit** | Configurable: 30 messages per 60 seconds |
| **History** | All sent messages logged |
| **Test** | Verify WebEx connection |

## Natural Language Examples

| Input | Action |
|-------|--------|
| "Send 'Task complete'" | Sends plain text message |
| "Send formatted: **bold** and _italic_" | Sends with WebEx markdown |
| "Notify about backup completion" | Sends notification |
| "Test WebEx connection" | Verifies bot connectivity |

## Message Formatting

Supports WebEx markdown:
- `**bold**` → **bold**
- `_italic_` → _italic_
- `` `code` `` → `code`
- `` ```code block``` `` → code block
- `[link text](url)` → hyperlinks

## Features

- ✅ Text notifications with markdown
- ✅ Auto-retry (max 3 times, configurable)
- ✅ Rate limiting (prevents flooding)
- ✅ Message history tracking
- ✅ Connection testing
- ✅ Comprehensive logging
- ✅ Cross-runtime support (Claude, Copilot, Gemini)

## Configuration

Environment variables:
```
WEBEX_BOT_TOKEN=your_bot_token_here
WEBEX_ROOM_ID=your_room_id_here
WEBEX_MAX_RETRIES=3
WEBEX_RETRY_DELAY=2
WEBEX_RATE_LIMIT_MESSAGES=30
WEBEX_RATE_LIMIT_WINDOW=60
```

## Auto-Retry

When send fails:
1. Wait (retry_delay seconds)
2. Retry (up to max_retries times)
3. Exponential backoff between attempts
4. Log all retry attempts

## Rate Limiting

Prevents flooding:
- Default: 30 messages per 60 seconds
- Configurable via environment variables
- Applies across all messages

## Verification

Test connection before sending:
```
Action: "Test WebEx connection"
Response: "✓ WebEx connection successful"
```

See README.md for complete documentation.
