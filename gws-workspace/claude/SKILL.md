---
name: gws-workspace
description: Interact with all Google Workspace services via the official gws CLI — Drive, Gmail, Calendar, Docs, Sheets, Tasks, Chat, Forms, Keep, Meet, People, Classroom, and cross-service Workflows.
---

# GWS — Google Workspace CLI Skill (Claude Runtime)

## Prerequisites Check

Before using, verify gws is installed and authenticated:
```bash
which gws && gws auth status
```

If not installed, see Installation section in the parent SKILL.md.

## Usage Pattern for Claude

When the user asks to interact with Google Workspace services, use Bash tool to run `gws` commands.

### Always check auth first:
```bash
gws auth status 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'User: {d.get(\"user\",\"NOT AUTH\")} | Valid: {d.get(\"token_valid\",False)}')"
```

### Use --format table for human-readable output, --format json for processing:
```bash
# Human-readable
gws calendar events list --params '{"calendarId":"primary","maxResults":10}' --format table

# For processing with jq
gws drive files list --params '{"pageSize":20}' | jq -r '.files[] | "\(.id)\t\(.name)"'
```

### For creating events (Calendar):
```bash
gws calendar events insert --params '{"calendarId": "primary"}' \
  --json '{
    "summary": "EVENT_TITLE",
    "start": {"dateTime": "2026-03-15T10:00:00-05:00", "timeZone": "America/New_York"},
    "end": {"dateTime": "2026-03-15T11:00:00-05:00", "timeZone": "America/New_York"},
    "description": "Optional description"
  }'
```

### For all-day events:
```bash
gws calendar events insert --params '{"calendarId": "primary"}' \
  --json '{"summary": "Holiday", "start": {"date": "2026-03-17"}, "end": {"date": "2026-03-18"}}'
```

### For sending email:
```bash
gws gmail +send --to "recipient@example.com" --subject "Subject" --body "Body text"
# HTML email:
gws gmail +send --to "recipient@example.com" --body "<b>Bold</b>" --html
```

### For uploading to Drive:
```bash
gws drive +upload /path/to/file.pdf --name "Custom Name.pdf"
# Upload to specific folder:
gws drive +upload /path/to/file.pdf --parent FOLDER_ID
```

### For reading Sheets:
```bash
gws sheets +read --spreadsheet SPREADSHEET_ID --range "Sheet1!A1:Z100"
```

### Schema inspection (understand any API method):
```bash
gws schema calendar.events.insert
gws schema drive.files.list
gws schema gmail.users.messages.send
```

## Error Handling

Check exit codes:
- Exit 1: API error — check the JSON error response for details
- Exit 2: Auth error — run `gws auth login` to re-authenticate
- Exit 3: Validation error — check your `--params` or `--json` arguments

If Calendar/Drive/Gmail API is not enabled, visit the GCP Console APIs Library to enable it.

## Multi-step Workflows

For complex tasks, chain commands using shell variables:
```bash
# Create a doc and get its ID
DOC_ID=$(gws docs documents create --json '{"title": "Report"}' | jq -r '.documentId')

# Append content to it
gws docs +write --document "$DOC_ID" --text "Content here"

# Share it with anyone
gws drive permissions create --params '{"fileId": "'"$DOC_ID"'"}' \
  --json '{"role": "reader", "type": "anyone"}'
echo "https://docs.google.com/document/d/$DOC_ID"
```
