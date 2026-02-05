---
name: telegram-notify
description: Use when you need to send Telegram notifications - supports markdown formatting, auto-retry with backoff, rate limiting, and message history tracking
---

# Telegram Notify

## Overview

Send Telegram messages with markdown formatting, auto-retry, and rate limiting. Reliable notification delivery with built-in resilience.

**Core principle:** Simple, reliable Telegram messaging with automatic retries and rate limiting.

## When to Use

- Send Telegram notifications for alerts
- Notify about task completion
- Send formatted messages with markdown
- Need reliable delivery (auto-retry)
- Track message history

## Quick Reference

| Feature | Behavior |
|---------|----------|
| **Send** | Message delivered via Telegram |
| **Format** | Markdown support (`*bold*`, `_italic_`, `` `code` ``) |
| **Retry** | Auto-retry up to 3 times on failure |
| **Rate Limit** | Configurable delay between messages |
| **History** | All sent messages logged |
| **Test** | Verify Telegram connection |

## Natural Language Examples

| Input | Action |
|-------|--------|
| "Send 'Task complete'" | Sends plain text message |
| "Send formatted: **bold** and _italic_" | Sends with Telegram markdown |
| "Notify about backup completion" | Sends notification |
| "Test Telegram connection" | Verifies bot connectivity |

## Message Formatting

Supports Telegram markdown:
- `*bold*` → **bold**
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
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_MAX_RETRIES=3
TELEGRAM_RETRY_DELAY=5
TELEGRAM_RATE_LIMIT=1.0
```

## Auto-Retry

When send fails:
1. Wait (retry_delay seconds)
2. Retry (up to max_retries times)
3. Exponential backoff between attempts
4. Log all retry attempts

## Rate Limiting

Prevents flooding:
- Default: 1 message per second
- Configurable via TELEGRAM_RATE_LIMIT
- Applies across all messages

## Verification

Test connection before sending:
```
Action: "Test Telegram connection"
Response: "✓ Telegram connection successful"
```

See README.md for complete documentation.
