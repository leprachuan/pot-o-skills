# WebEx Notification Skill

Send WebEx messages to flipkey-home-bot with markdown formatting, auto-retry, and rate limiting.

## Features
✅ Send text notifications to WebEx room (flipkey-home-bot)
✅ Auto-retry (max 3, configurable)
✅ Rate limiting (configurable)
✅ Message history
✅ Connection testing
✅ Logging
✅ Cross-runtime (Claude, Copilot, Gemini)

## Setup

### 1. Create WebEx Bot Token

1. Go to https://developer.webex.com/
2. Create a new bot for flipkey-home-bot
3. Copy the bot token

### 2. Get Room ID

1. Add the bot to your WebEx room
2. Message the bot to get room ID, or
3. Use WebEx API to list rooms

### 3. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Then edit `.env`:

```
WEBEX_BOT_TOKEN=your_bot_token
WEBEX_ROOM_ID=your_room_id
WEBEX_MAX_RETRIES=3
WEBEX_RETRY_DELAY=2
WEBEX_RATE_LIMIT_MESSAGES=30
WEBEX_RATE_LIMIT_WINDOW=60
WEBEX_LOGS_DIR=/opt/.webex-notify/logs/
```

## Usage

### Claude

```python
from webex_notify import WebExNotifySkill

skill = WebExNotifySkill()

# Send notification
skill.send_notification("Hello from WebEx!")

# Send alert
skill.send_alert("System backup complete")

# Test connection
skill.test_connection()

# Get history
skill.get_message_history()
```

### Copilot CLI

```bash
python webex_notify_cli.py send_notification "Your message here"
python webex_notify_cli.py send_alert "Alert message"
python webex_notify_cli.py test_connection
```

### Gemini

Functions available:
- `send_notification(text)`
- `send_alert(text)`
- `test_connection()`
- `get_message_history()`
- `configure(token, room_id)`

## Markdown Support

WebEx markdown formatting:
- `**bold**` → **bold**
- `_italic_` → _italic_
- `` `code` `` → `code`
- `[link](url)` → hyperlinks

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

## Message History

All sent messages logged to:
```
/opt/.webex-notify/logs/messages.log
```

Format:
```
[2024-02-05T12:34:56.789Z] Sent: Your message here (msg_id: abc123def456)
[2024-02-05T12:35:10.123Z] Error: Connection timeout
```

## Testing

```bash
# Test connection
python webex_notify_cli.py test_connection

# Send test message
python webex_notify_cli.py send_notification "Test message"

# Check history
python webex_notify_cli.py get_message_history
```

## Troubleshooting

### "WEBEX_BOT_TOKEN and WEBEX_ROOM_ID must be set"
- Ensure .env file exists in the skill directory
- Check .env has correct token and room_id
- Source the .env: `export $(cat .env | xargs)`

### "Connection failed"
- Verify bot token is valid
- Check room_id is correct
- Ensure bot is added to the room

### "HTTP 403 - Forbidden"
- Bot token may be invalid or expired
- Bot may not have permission to send to room
- Room ID may be incorrect

## Dependencies

- `requests` - HTTP client library (auto-installed)

## Schedule Integration

This skill can be used with task-scheduler for automatic notifications:

```yaml
notifications:
  - name: "Daily backup alert"
    schedule: "0 22 * * *"
    action: send_notification
    text: "Daily backup starting at 10 PM"
```

## Configuration

Environment variables control behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| WEBEX_BOT_TOKEN | (required) | Bot authentication token |
| WEBEX_ROOM_ID | (required) | Target WebEx room ID |
| WEBEX_MAX_RETRIES | 3 | Max retry attempts on failure |
| WEBEX_RETRY_DELAY | 2 | Seconds between retries |
| WEBEX_RATE_LIMIT_MESSAGES | 30 | Messages in rate limit window |
| WEBEX_RATE_LIMIT_WINDOW | 60 | Rate limit window in seconds |
| WEBEX_LOGS_DIR | /opt/.webex-notify/logs/ | Log directory |

## See Also

- [WebEx Developer Docs](https://developer.webex.com/)
- [WebEx Markdown Guide](https://help.webex.com/en-us/article/WBX44602/Webex-Markdown-guide)
- Telegram Notify Skill (similar functionality for Telegram)
