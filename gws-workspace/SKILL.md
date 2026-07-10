---
name: gws-workspace
aliases: [google-workspace-cli, google-cli, gws]
description: Interact with all Google Workspace services via the official gws CLI — Drive, Gmail, Calendar, Docs, Sheets, Slides, Tasks, Chat, Forms, Keep, Meet, People, Classroom, and cross-service Workflows.
keywords: [google, workspace, drive, gmail, calendar, docs, sheets, cli, productivity, automation]
searchable: ["google cli", "google drive cli", "gmail cli", "calendar cli", "google workspace api"]
---

# 🔧 GWS — Google Workspace CLI Skill

**Unified command-line interface for all Google Workspace APIs.** Manage Gmail, Drive, Calendar, Docs, Sheets, and more from the CLI.

Unified command-line interface for all Google Workspace APIs. Uses the official
`@googleworkspace/cli` npm package (binary: `gws`), which reads Google's Discovery
Service at runtime and dynamically exposes every available method.

> **Note:** This is not an officially supported Google product.
> GitHub: https://github.com/googleworkspace/cli

---

## Installation

### 1. Install via npm (requires Node.js 18+)
```bash
npm install -g @googleworkspace/cli
gws --version   # verify
```

### 2. Set Up a GCP Project & OAuth Credentials

You need a Google Cloud project with an OAuth 2.0 Desktop App credential.

**Option A — Using gcloud (recommended):**
```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install
gws auth setup --project YOUR_GCP_PROJECT_ID --login
```

**Option B — Manual (no gcloud required):**
1. Go to https://console.cloud.google.com → Select or create a project
2. Navigate to **APIs & Services → Library** and enable the APIs you need:
   - Google Calendar API
   - Google Drive API
   - Gmail API
   - Google Sheets API
   - (any others you'll use)
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
4. Select **Desktop app** → Download JSON
5. Save it to `~/.config/gws/client_secret.json`

### 3. Authenticate

```bash
gws auth login                        # Full default scopes
gws auth login -s drive,gmail         # Limit to specific services
gws auth login --readonly             # Read-only scopes
gws auth login --full                 # All scopes incl. pubsub + cloud-platform
```

A browser window opens for OAuth consent. After completing it, credentials are
stored encrypted in `~/.config/gws/`.

### 4. Verify Auth
```bash
gws auth status
```

### Multiple Accounts

Use `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` to manage multiple accounts:
```bash
# Set up second account
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-work gws auth login

# Use second account
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-work gws gmail users messages list --params '{"userId":"me"}'

# Shell aliases for convenience
alias gws-personal='gws'
alias gws-work='GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-work gws'
```

---

## Command Structure

```
gws <service> <resource> [sub-resource] <method> [flags]
gws schema <service.resource.method>         # Inspect API schema
gws <service> +<helper> [options]            # High-level helper commands
```

---

## Global Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--params <JSON>` | URL/query parameters | `--params '{"pageSize": 10}'` |
| `--json <JSON>` | Request body (POST/PATCH/PUT) | `--json '{"name": "file"}'` |
| `--upload <PATH>` | Upload local file as media | `--upload ./report.pdf` |
| `--upload-content-type <MIME>` | Override MIME type | `--upload-content-type application/pdf` |
| `--output <PATH>` | Save binary response to file | `--output ./downloaded.pdf` |
| `--format <FMT>` | Output format | `json` (default), `table`, `yaml`, `csv` |
| `--api-version <VER>` | Override API version | `--api-version v2` |
| `--page-all` | Auto-paginate all results (NDJSON) | |
| `--page-limit <N>` | Max pages (default: 10) | `--page-limit 5` |
| `--page-delay <MS>` | Delay between pages (default: 100ms) | `--page-delay 500` |
| `--dry-run` | Validate without sending request | |

---

## Services & Key Operations

### Drive
```bash
# List files
gws drive files list --params '{"pageSize": 20}' --format table
gws drive files list --params '{"q": "name contains '\''report'\''"}'

# Upload file
gws drive +upload ./report.pdf --name "Q1 Report.pdf"
gws drive +upload ./photo.jpg --parent FOLDER_ID

# Download / export
gws drive files get --params '{"fileId": "FILE_ID", "alt": "media"}' --output ./file.pdf
gws drive files export --params '{"fileId": "DOC_ID", "mimeType": "application/pdf"}' --output ./doc.pdf

# Manage permissions (sharing)
gws drive permissions create --params '{"fileId": "FILE_ID"}' \
  --json '{"role": "writer", "type": "user", "emailAddress": "person@example.com"}'

# Trash / delete
gws drive files delete --params '{"fileId": "FILE_ID"}'
gws drive files emptyTrash
```

### Gmail
```bash
# Send email
gws gmail +send --to recipient@example.com --subject "Hello" --body "Hi there!"
gws gmail +send --to user@example.com --body "<b>Bold</b>" --html --cc cc@example.com

# Triage inbox (summary of unread)
gws gmail +triage --max 20 --format table

# List messages
gws gmail users messages list --params '{"userId": "me", "q": "is:unread", "maxResults": 10}'

# Reply / reply-all / forward
gws gmail +reply --message-id MESSAGE_ID --body "Thanks!"
gws gmail +reply-all --message-id MESSAGE_ID --body "Team reply"
gws gmail +forward --message-id MESSAGE_ID --to other@example.com

# Batch operations
gws gmail users messages batchModify --json '{"ids": ["id1","id2"], "removeLabelIds": ["UNREAD"]}'

# Watch inbox via Pub/Sub (streams new emails as NDJSON)
gws gmail +watch --project GCP_PROJECT_ID --label-ids INBOX --once
```

### Calendar
```bash
# View upcoming events
gws calendar +agenda

# List events
gws calendar events list --params '{"calendarId": "primary", "maxResults": 20}' --format table
gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-03-14T00:00:00Z", "timeMax": "2026-04-14T00:00:00Z"}'

# Create event (helper)
gws calendar +insert --summary "Team Standup" \
  --start "2026-03-15T09:00:00-05:00" \
  --end "2026-03-15T09:30:00-05:00" \
  --attendee alice@example.com \
  --description "Daily sync"

# Create event (raw)
gws calendar events insert --params '{"calendarId": "primary"}' \
  --json '{"summary": "Meeting", "start": {"dateTime": "2026-03-15T10:00:00-05:00", "timeZone": "America/New_York"}, "end": {"dateTime": "2026-03-15T11:00:00-05:00", "timeZone": "America/New_York"}}'

# All-day event
gws calendar events insert --params '{"calendarId": "primary"}' \
  --json '{"summary": "Holiday", "start": {"date": "2026-03-17"}, "end": {"date": "2026-03-18"}}'

# Quick add from natural language
gws calendar events quickAdd --params '{"calendarId": "primary", "text": "Meeting tomorrow at 3pm"}'

# List calendars
gws calendar calendarList list --format table

# Delete event
gws calendar events delete --params '{"calendarId": "primary", "eventId": "EVENT_ID"}'
```

### Docs
```bash
# Create document
DOC_ID=$(gws docs documents create --json '{"title": "Meeting Notes"}' | jq -r '.documentId')

# Append text
gws docs +write --document $DOC_ID --text "## March 14\n- Action item 1"

# Get document content
gws docs documents get --params '{"documentId": "DOC_ID"}'

# Export as PDF
gws docs documents export --params '{"documentId": "DOC_ID", "mimeType": "application/pdf"}' --output ./notes.pdf
```

### Sheets
```bash
# Read a range
gws sheets +read --spreadsheet SPREADSHEET_ID --range "Sheet1!A1:D10"
gws sheets +read --spreadsheet SPREADSHEET_ID --range Sheet1   # entire sheet

# Append rows
gws sheets +append --spreadsheet SPREADSHEET_ID --values "Alice,100,2026-03-14"
gws sheets +append --spreadsheet SPREADSHEET_ID --json-values '[["Bob",200,"2026-03-15"],["Carol",300,"2026-03-16"]]'

# Create spreadsheet
gws sheets spreadsheets create --json '{"properties": {"title": "New Report"}}'

# Get metadata
gws sheets spreadsheets get --params '{"spreadsheetId": "SPREADSHEET_ID"}' | jq '.sheets[].properties.title'
```

### Tasks
```bash
# List task lists
gws tasks tasklists list --format table

# Create task list
TASKLIST_ID=$(gws tasks tasklists insert --json '{"title": "Weekly Goals"}' | jq -r '.id')

# Add task
gws tasks tasks insert --params '{"tasklist": "@default"}' \
  --json '{"title": "Write report", "notes": "Due Friday", "due": "2026-03-20T00:00:00.000Z"}'

# List tasks
gws tasks tasks list --params '{"tasklist": "@default"}' --format table

# Complete task
gws tasks tasks patch --params '{"tasklist": "@default", "task": "TASK_ID"}' \
  --json '{"status": "completed"}'
```

### Chat
```bash
# Send message to a space
gws chat +send --space "spaces/SPACE_ID" --text "Hello team!"

# List spaces
gws chat spaces list --format table

# List members of a space
gws chat spaces members list --params '{"parent": "spaces/SPACE_ID"}' --format table
```

### People / Contacts
```bash
# Search contacts
gws people people searchContacts --params '{"query": "Alice", "readMask": "names,emailAddresses"}' --format table

# Get contact
gws people people get --params '{"resourceName": "people/CONTACT_ID", "personFields": "names,emailAddresses,phoneNumbers"}'

# List all contacts
gws people people connections list --params '{"resourceName": "people/me", "personFields": "names,emailAddresses"}' --page-all
```

### Keep
```bash
# List notes
gws keep notes list --format table

# Create note
gws keep notes create --json '{"title": "Quick Note", "body": {"text": {"text": "Remember this!"}}}'

# Delete note
gws keep notes delete --params '{"name": "notes/NOTE_ID"}'
```

### Forms
```bash
# Get form structure
gws forms forms get --params '{"formId": "FORM_ID"}'

# Get responses
gws forms forms responses list --params '{"formId": "FORM_ID"}' --format table

# Create form
gws forms forms create --json '{"info": {"title": "Survey"}}'
```

### Meet
```bash
# Create meeting space
gws meet spaces create --json '{}'

# Get meeting space
gws meet spaces get --params '{"name": "spaces/SPACE_ID"}'
```

### Admin Reports (Workspace Admins only)
```bash
# Audit log for a user
gws admin-reports activities list \
  --params '{"userEmail": "user@example.com", "applicationName": "drive", "maxResults": 50}'

# Domain-wide usage report
gws admin-reports customerUsageReports get --params '{"date": "2026-03-13"}'
```

---

## Cross-Service Workflows

```bash
# Daily standup: today's calendar + open tasks
gws workflow +standup-report --format table

# Meeting prep: agenda + attendees + linked docs
gws workflow +meeting-prep

# Convert email to task
gws workflow +email-to-task --message-id MSG_ID --tasklist "@default"

# Weekly digest: meetings summary + unread count
gws workflow +weekly-digest

# Announce a Drive file in a Chat space
gws workflow +file-announce --file-id FILE_ID --space spaces/SPACE_ID
```

---

## Schema Inspection

Inspect any API method's parameters, request body, and response format:

```bash
gws schema drive.files.list
gws schema calendar.events.insert
gws schema gmail.users.messages.send
gws schema sheets.spreadsheets.values.update
```

---

## Advanced Patterns

### Pagination
```bash
# Stream all files, one page per line (NDJSON)
gws drive files list --params '{"pageSize": 100}' --page-all | jq -r '.files[].name'
```

### Field Masking (reduce bandwidth)
```bash
gws drive files list --params '{"fields": "files(id,name,mimeType,size)"}'
```

### Chaining with jq
```bash
# Get all unread email subjects
gws gmail users messages list --params '{"userId":"me","q":"is:unread","maxResults":20}' | \
  jq -r '.messages[].id' | \
  xargs -I{} gws gmail users messages get --params '{"userId":"me","id":"{}","format":"metadata","metadataHeaders":["Subject"]}' | \
  jq -r '.payload.headers[] | select(.name=="Subject") | .value'

# Create doc and share it
DOC_ID=$(gws docs documents create --json '{"title": "Report"}' | jq -r '.documentId')
gws drive permissions create --params '{"fileId": "'$DOC_ID'"}' \
  --json '{"role": "reader", "type": "anyone"}'
echo "https://docs.google.com/document/d/$DOC_ID"
```

### Dry Run (preview before executing)
```bash
gws gmail +send --to user@example.com --subject "Test" --body "Hello" --dry-run
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_WORKSPACE_CLI_TOKEN` | Pre-obtained OAuth2 access token (bypasses stored creds) |
| `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` | Path to credentials JSON file |
| `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` | Override config dir (default: `~/.config/gws`) |
| `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND` | `keyring` (default, encrypted) or `file` |
| `GOOGLE_WORKSPACE_PROJECT_ID` | Override GCP project ID for quota/billing |
| `GOOGLE_WORKSPACE_CLI_LOG` | Log level: `gws=debug` or `gws=trace` |
| `GOOGLE_WORKSPACE_CLI_LOG_FILE` | Directory for JSON log files |

---

## Auth Management

```bash
gws auth status        # Show current auth state, user, scopes
gws auth login         # Re-authenticate or add scopes
gws auth logout        # Clear credentials and token cache
gws auth export        # Print decrypted credentials (for migration)
```

### Credential Files (all in `~/.config/gws/`)
- `client_secret.json` — Your OAuth app credentials (NEVER commit this)
- `credentials.enc` — Encrypted user token (managed by gws)
- `token_cache.json` — Access token cache (auto-managed)

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | API error (Google returned an error) |
| `2` | Auth error (missing or invalid credentials) |
| `3` | Validation error (bad arguments) |
| `4` | Discovery error (could not fetch API schema) |
| `5` | Internal error |

---

## Common Issues

**"API not enabled"** — Enable the specific Google API in GCP Console:
```
https://console.developers.google.com/apis/library?project=YOUR_PROJECT_ID
```

**"Token expired"** — Re-authenticate:
```bash
gws auth login
```

**"Insufficient scopes"** — Re-auth with broader scopes:
```bash
gws auth logout && gws auth login --full
```

**"This browser is not secure"** on headless servers — Complete `gws auth login`
on a machine with a real browser, then copy `~/.config/gws/` to the server.
