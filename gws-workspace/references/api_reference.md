# GWS API Reference

Quick reference for all 16 services exposed by the `gws` CLI.

---

## Drive (`gws drive`)

| Resource | Methods |
|----------|---------|
| `files` | list, get, create, copy, update, delete, download, export, watch, emptyTrash, generateIds, modifyLabels, listLabels |
| `permissions` | list, get, create, update, delete |
| `comments` | list, get, create, update, delete |
| `revisions` | list, get, update, delete |
| `changes` | list, getStartPageToken, watch |
| `drives` | list, get, create, update, delete, hide, unhide |
| `about` | get |

**Helpers:** `+upload`

**Common search operators for `--params '{"q": "..."}'`:**
- `name contains 'report'`
- `mimeType = 'application/vnd.google-apps.folder'`
- `'me' in owners`
- `modifiedTime > '2026-01-01T00:00:00'`
- `trashed = false`

**MIME types for Google files:**
| Type | MIME |
|------|------|
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| Google Form | `application/vnd.google-apps.form` |
| Folder | `application/vnd.google-apps.folder` |

---

## Sheets (`gws sheets`)

| Resource | Methods |
|----------|---------|
| `spreadsheets` | get, create, batchUpdate |
| `spreadsheets.values` | get, update, append, clear, batchGet, batchUpdate, batchClear |
| `spreadsheets.sheets` | copyTo |

**Helpers:** `+read`, `+append`

**Range notation:** `Sheet1!A1:D10`, `Sheet1` (entire sheet), `A:Z` (full columns)

---

## Gmail (`gws gmail`)

| Resource | Methods |
|----------|---------|
| `users.messages` | list, get, send, delete, trash, untrash, modify, batchModify, batchDelete, import, insert |
| `users.threads` | list, get, delete, trash, untrash, modify |
| `users.labels` | list, get, create, update, patch, delete |
| `users.drafts` | list, get, create, update, delete, send |
| `users.history` | list |
| `users.settings` | getAutoForwarding, updateAutoForwarding, getImap, updateImap, getPop, updatePop, getVacation, updateVacation |
| `users.watch` | watch, stop |

**Helpers:** `+send`, `+triage`, `+reply`, `+reply-all`, `+forward`, `+watch`

**Gmail search operators for `q` param:**
- `is:unread`, `is:starred`, `in:inbox`
- `from:user@example.com`, `to:user@example.com`
- `subject:keyword`
- `has:attachment`
- `after:2026/01/01`, `before:2026/03/01`
- `label:important`

---

## Calendar (`gws calendar`)

| Resource | Methods |
|----------|---------|
| `events` | list, get, insert, update, patch, delete, quickAdd, import, move, instances, watch |
| `calendars` | get, insert, update, patch, delete, clear |
| `calendarList` | list, get, insert, update, patch, delete, watch |
| `acl` | list, get, insert, update, patch, delete, watch |
| `freebusy` | query |
| `colors` | get |
| `settings` | list, get, watch |
| `channels` | stop |

**Helpers:** `+insert`, `+agenda`

**Common event fields:**
```json
{
  "summary": "Event title",
  "description": "Optional notes",
  "location": "Room / address",
  "start": {"dateTime": "2026-03-15T10:00:00-05:00", "timeZone": "America/New_York"},
  "end": {"dateTime": "2026-03-15T11:00:00-05:00", "timeZone": "America/New_York"},
  "attendees": [{"email": "person@example.com"}],
  "reminders": {"useDefault": true},
  "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"]
}
```

---

## Docs (`gws docs`)

| Resource | Methods |
|----------|---------|
| `documents` | get, create, batchUpdate, export |

**Helpers:** `+write`

---

## Slides (`gws slides`)

| Resource | Methods |
|----------|---------|
| `presentations` | get, create, batchUpdate |

---

## Tasks (`gws tasks`)

| Resource | Methods |
|----------|---------|
| `tasklists` | list, get, insert, update, patch, delete |
| `tasks` | list, get, insert, update, patch, delete, move, clear |

**Task status values:** `needsAction`, `completed`

---

## People (`gws people`)

| Resource | Methods |
|----------|---------|
| `people` | get, getBatchGet, listDirectoryPeople, searchDirectoryPeople, searchContacts, createContact, updateContact, deleteContact |
| `people.connections` | list |
| `contactGroups` | list, get, create, update, delete |
| `otherContacts` | list, search, copyOtherContactToMyContactsGroup |

**Common personFields:** `names`, `emailAddresses`, `phoneNumbers`, `addresses`, `birthdays`, `organizations`

---

## Chat (`gws chat`)

| Resource | Methods |
|----------|---------|
| `spaces` | list, get, create, update, delete, findDirectMessage, completeImport, setup |
| `spaces.members` | list, get, create, delete |
| `spaces.messages` | list, get, create, update, delete |
| `spaces.messages.attachments` | get |
| `customEmojis` | list, get, create, delete |

**Helpers:** `+send`

---

## Classroom (`gws classroom`)

| Resource | Methods |
|----------|---------|
| `courses` | list, get, create, update, patch, delete |
| `courses.students` | list, get, create, delete |
| `courses.teachers` | list, get, create, delete |
| `courses.courseWork` | list, get, create, update, patch, delete |
| `invitations` | list, get, create, delete, accept |
| `userProfiles` | get |

---

## Forms (`gws forms`)

| Resource | Methods |
|----------|---------|
| `forms` | get, create, batchUpdate, setPublishSettings |
| `forms.responses` | list, get |
| `forms.watches` | list, create, renew, delete |

---

## Keep (`gws keep`)

| Resource | Methods |
|----------|---------|
| `notes` | list, get, create, delete |
| `notes.permissions` | create, delete |
| `media` | download |

---

## Meet (`gws meet`)

| Resource | Methods |
|----------|---------|
| `spaces` | get, create, endActiveConference |
| `conferenceRecords` | list, get |
| `conferenceRecords.participants` | list, get |
| `conferenceRecords.participantSessions` | list, get |
| `conferenceRecords.transcripts` | list, get |
| `conferenceRecords.recordings` | list, get |

---

## Admin Reports (`gws admin-reports`)

| Resource | Methods |
|----------|---------|
| `activities` | list, watch |
| `customerUsageReports` | get |
| `entityUsageReports` | get |
| `userUsageReport` | get |
| `channels` | stop |

**Application names for activities:** `drive`, `gmail`, `calendar`, `login`, `admin`, `token`, `groups`, `chat`, `meet`

---

## Events / Workspace Events (`gws events`)

| Resource | Methods |
|----------|---------|
| `subscriptions` | list, get, create, update, patch, delete, reactivate |
| `operations` | get |

**Helpers:** `+subscribe`, `+renew`

**Supported event targets:**
- `//chat.googleapis.com/spaces/SPACE_ID`
- `//drive.googleapis.com/drives/DRIVE_ID`
- `//gmail.googleapis.com/users/USER_ID`

---

## Model Armor (`gws modelarmor`)

**Helpers:** `+sanitize-prompt`, `+sanitize-response`, `+create-template`

Used to filter LLM prompts/responses for safety, harmful content, and data leakage.

---

## Workflows (`gws workflow` or `gws wf`)

| Helper | Description |
|--------|-------------|
| `+standup-report` | Today's calendar events + open tasks |
| `+meeting-prep` | Next meeting agenda + attendees + linked docs |
| `+email-to-task` | Convert Gmail message to Google Task |
| `+weekly-digest` | This week's meetings + unread email count |
| `+file-announce` | Share Drive file in Chat space |

---

## Schema Inspection

```bash
# Inspect any method
gws schema <service>.<resource>.<method>

# Examples
gws schema drive.files.list
gws schema calendar.events.insert
gws schema gmail.users.messages.send
gws schema sheets.spreadsheets.values.append
gws schema tasks.tasks.insert
```

Schema output includes: parameters, httpMethod, path, response schema, required OAuth scopes.
