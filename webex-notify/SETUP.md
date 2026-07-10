# WebEx Notify - Setup Guide

## Prerequisites

- WebEx account
- Bot token for flipkey-home-bot
- Room ID where bot is added

## Step 1: Create Bot Token

### Option A: Create New Bot

1. Visit https://developer.webex.com/
2. Sign in with your WebEx account
3. Click **Create a New App** → **Create a Bot**
4. Fill in bot details:
   - **Bot name:** flipkey-home-bot (or your preferred name)
   - **Bot username:** @flipkey-home-bot (choose unique handle)
   - **Icon:** (optional)
   - **Description:** Notification bot for home automation
5. Copy the **Bot Access Token** (starts with `OWY1Y`)
6. Click **Save**

### Option B: Use Existing Bot

If you already have a bot token, skip to Step 2.

## Step 2: Get Room ID

### Option A: List Rooms via API

1. Get your bot token from Step 1
2. Run:

```bash
curl -X GET "https://webexapis.com/v1/rooms" \
  -H "Authorization: Bearer YOUR_BOT_TOKEN"
```

3. Find the `id` field for your target room
4. Copy the room ID (looks like `Y2lzcm9...`)

### Option B: Manual Discovery

1. Add the bot to your WebEx room
2. Send a message in the room that triggers the bot
3. The bot can log the room ID on first message

## Step 3: Configure .env File

1. Copy the example file:
```bash
cd /opt/skills/webex-notify
cp .env.example .env
```

2. Edit `.env` with your values:
```bash
nano .env
```

3. Paste your credentials:
```
WEBEX_BOT_TOKEN=YOUR_BOT_ACCESS_TOKEN_HERE
WEBEX_ROOM_ID=YOUR_ROOM_ID_HERE
WEBEX_MAX_RETRIES=3
WEBEX_RETRY_DELAY=2
WEBEX_RATE_LIMIT_MESSAGES=30
WEBEX_RATE_LIMIT_WINDOW=60
WEBEX_LOGS_DIR=/opt/.webex-notify/logs/
```

## Step 4: Test Connection

```bash
cd /opt/skills/webex-notify

# Source the environment
export $(cat .env | xargs)

# Test via CLI
python3 copilot/implementation/webex_notify_cli.py test_connection
```

Expected output:
```json
{"success": true, "message": "Connection OK - Bot: flipkey-home-bot"}
```

## Step 5: Send Test Message

```bash
export $(cat .env | xargs)
python3 copilot/implementation/webex_notify_cli.py send_notification "Hello from WebEx Notify!"
```

You should see the message in your WebEx room.

## Step 6: Check Message History

```bash
export $(cat .env | xargs)
python3 copilot/implementation/webex_notify_cli.py get_message_history
```

## Integration with Task Scheduler

Add to your scheduler config to get automatic notifications:

```yaml
notifications:
  - name: "Daily System Check"
    schedule: "0 09 * * *"
    action: send_notification
    text: "Daily system health check started"
```

## Troubleshooting

### "WEBEX_BOT_TOKEN and WEBEX_ROOM_ID must be set"

**Solution:**
```bash
# Make sure you're in the skill directory
cd /opt/skills/webex-notify

# Source the .env file before running
export $(cat .env | xargs)

# Verify variables are set
echo $WEBEX_BOT_TOKEN
echo $WEBEX_ROOM_ID
```

### "HTTP 401 - Unauthorized"

**Causes:**
- Invalid or expired bot token
- Token not copied correctly

**Solution:**
1. Get a new token from https://developer.webex.com/
2. Update `.env` with correct token
3. Test again

### "HTTP 404 - Not Found"

**Causes:**
- Invalid room ID
- Bot not added to room
- Room deleted

**Solution:**
1. Verify room ID is correct
2. Ensure bot is added to the room
3. Get fresh room ID from API

### "HTTP 403 - Forbidden"

**Causes:**
- Bot doesn't have permission to send messages
- Account/org restrictions

**Solution:**
1. Verify bot is added to the room
2. Check WebEx org policies
3. Try creating a new bot with broader permissions

### Rate Limiting Issues

If messages are being dropped:
```bash
# Increase the rate limit window
export WEBEX_RATE_LIMIT_MESSAGES=10
export WEBEX_RATE_LIMIT_WINDOW=120
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Review [SKILL.md](SKILL.md) for usage patterns
- Check schedule integration docs for automatic notifications
- Set up proper logging in `/opt/.webex-notify/logs/`

## WebEx API References

- [Bot Creation Guide](https://developer.webex.com/docs/bots)
- [Rooms API](https://developer.webex.com/docs/api/v1/rooms)
- [Messages API](https://developer.webex.com/docs/api/v1/messages)
- [Markdown Guide](https://help.webex.com/en-us/article/WBX44602/Webex-Markdown-guide)
