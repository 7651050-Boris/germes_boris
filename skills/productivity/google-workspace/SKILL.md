---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/alternative-calendars.md` — Non-Google calendars: iCloud CalDAV, Yandex CalDAV, macOS Calendar limitations

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library.
>    Quick-enable links (one per API — open in browser and tap Enable):
>    - **Calendar API**: https://console.cloud.google.com/apis/enableflow?apiid=calendar.googleapis.com&project=PROJECT_ID
>    - **Gmail API**: https://console.cloud.google.com/apis/enableflow?apiid=gmail.googleapis.com&project=PROJECT_ID
>    - **Drive API**: https://console.cloud.google.com/apis/enableflow?apiid=drive.googleapis.com&project=PROJECT_ID
>    - **Sheets API**: https://console.cloud.google.com/apis/enableflow?apiid=sheets.googleapis.com&project=PROJECT_ID
>    - **Docs API**: https://console.cloud.google.com/apis/enableflow?apiid=docs.googleapis.com&project=PROJECT_ID
>    - **People API**: https://console.cloud.google.com/apis/enableflow?apiid=people.googleapis.com&project=PROJECT_ID
>    Replace `PROJECT_ID` with your actual project ID.
>    > **Mobile users**: The full API Library page may fail to load on phone browsers. The `enableflow` links above are more reliable. Open them one at a time (not in parallel tabs). If even those fail, try from a desktop browser later — the setup can continue as far as getting the auth URL without APIs enabled.
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and send it to me

**Receiving the JSON file:** The user may send it as a document attachment (Telegram/Discord file upload) or paste the file path. Handle both:

- **Document attachment in messenger** → Look for the file at `~/.hermes/profiles/PROFILE/cache/documents/doc_*_client_secret*.json`. Copy it to `~/.hermes/google_client_secret.json`:
  ```bash
  cp ~/.hermes/profiles/PROFILE/cache/documents/doc_*_client_secret*.json ~/.hermes/google_client_secret.json
  ```
- **File path from the user** → Copy it to the Hermes Google directory:
  ```bash
  $GSETUP --client-secret /path/to/client_secret.json
  ```
- **Raw paste of client_id / client_secret** → Write a valid Desktop OAuth JSON file yourself, save it, then run `--client-secret` against it.

> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command.

### Step 3: Get authorization URL

Use the service set chosen in Step 1. Examples:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

This returns JSON with an `auth_url` field and also saves the exact URL to
`~/.hermes/google_oauth_last_url.txt`.

Agent rules for this step:
- Extract the `auth_url` field and send that exact URL to the user as a single line.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

If `--auth-code` fails because the code expired, was already used, or came from
an older browser tab, it now returns a fresh `fresh_auth_url`. In that case,
immediately send the new URL to the user and have them retry with the newest
browser redirect only.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| `HttpError 403: Access Not Configured` | API not enabled. Use enableflow links from Step 2 (replace PROJECT_ID). Mobile users: try each link one at a time, not in parallel. |
| Google Console not loading on mobile phone | Use the `enableflow` URLs: `https://console.cloud.google.com/apis/enableflow?apiid=SERVICE&project=PROJECT_ID`. If still failing, the user needs desktop browser access to complete API enabling — the rest of OAuth setup (get auth URL, exchange code) can proceed without enabled APIs. Enable APIs hits at `--auth-url` step. |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```

## Alternative: Yandex Calendar (CalDAV)

If the user uses **Yandex Calendar** instead of Google Calendar, OAuth setup via Google Cloud Console is not needed. Yandex Calendar supports the CalDAV protocol:

**Requirements:**
1. Yandex account email (e.g. `user@yandex.ru`)
2. **App password** (not the main account password), created at:
   - https://id.yandex.ru/security → App Passwords → Create
   - Select service: "Mail" or "Calendar"
   - A 16-character password is generated

**CalDAV connection details:**
- Server: `https://caldav.yandex.ru`
- Username: Yandex email
- Password: App password (16 characters)

**Creating events with reminders via curl:**
```bash
curl -u 'email:app_password' -X PUT \
  -H "Content-Type: text/calendar; charset=utf-8" \
  -d 'BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes Agent//EN
BEGIN:VEVENT
UID:unique-id-123
DTSTART:20260616T100000Z
DTEND:20260616T103000Z
SUMMARY:Event title
DESCRIPTION:Event description
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
END:VCALENDAR' \
  'https://caldav.yandex.ru/email@yandex.ru/Calendar-Name/event-id.ics'
```

**Listing calendars:**
```bash
curl -u 'email:app_password' -X PROPFIND \
  -H "Depth: 0" \
  'https://caldav.yandex.ru'
```

**Pitfalls:**
- App passwords must be created at https://id.yandex.ru/security — this is a one-time setup
- Each app password can be revoked individually
- Yandex CalDAV does NOT support OAuth2 bearer tokens — only Basic Auth with app passwords
- The CalDAV server requires `Depth: 1` header for PROPFIND
- Event UIDs must be unique per event; use `uuidgen` or Python's `uuid` module
- Timezone: Yandex defaults to Moscow Time (UTC+3/MSK). Use UTC for portability
