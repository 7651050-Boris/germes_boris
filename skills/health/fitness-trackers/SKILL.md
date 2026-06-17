---
name: fitness-trackers
description: "Integrate wearable fitness trackers (Whoop, Oura, Garmin, Fitbit, etc.) via OAuth2 APIs. Get recovery, sleep, workout, heart rate, and body measurement data. Auto-refresh tokens, schedule data pulls, store to local or publish to Telegram."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [WHOOP, Oura, Garmin, Fitbit, Fitness, Wearable, API, OAuth2, Health-Data, Biometrics]
    related_skills: [nutriciolog-eliseeva, ocr-and-documents, russian-boxoffice]
---
# Fitness Trackers API Integration

Covers OAuth2-connected wearable trackers. Currently documented: **Whoop**. Oura, Garmin Health API, Fitbit follow similar patterns.

## Whoop API

### Prerequisites: EasyOCR for Screenshot Verification

When the user sends screenshots of the Whoop developer dashboard or Whoop app UI, use **EasyOCR** to read text from images. This is useful for:
- Verifying Client ID / Client Secret match what the user copied
- Reading dashboard settings (scopes, redirect URLs, contact info)
- Reading Whoop app data (recovery scores, sleep stages) if displayed on screen

**Installation:**
```bash
pip3 install easyocr
# Installs Torch (~2GB) + torchvision + easyocr
# First run downloads detection model (~200MB) — takes 2-3 minutes
```

**Usage:**
```python
import easyocr
reader = easyocr.Reader(['ru', 'en'], gpu=False)  # CPU mode is slower but works
result = reader.readtext('/path/to/image.jpg', detail=0, paragraph=True)
for line in result:
    print(line)
```

**EasyOCR pitfalls:**
- **GPU vs CPU**: set `gpu=False` unless hardware acceleration is confirmed. CPU is slow but functional.
- **Cyrillic vs Latin lookalikes**: EasyOCR may confuse `а` (Cyrillic) with `a` (Latin). This is CRITICAL for credentials — OCR errors in Client ID/Secret produce strings that look correct but fail silently with `invalid_client`. Always cross-check with user-typed text.
- **Large output**: EasyOCR prints progress bars to stderr. Filter with `grep -v -E '^(Progress|Using CPU|UserWarning)'` or capture only unique lines.
- **First-run delay**: The detection model download can take 2-3 minutes on first run. Subsequent runs are faster.

### Step 1: Register Application

1. Go to https://developer.whoop.com
2. Click "GET STARTED" (requires WHOOP account login)
3. Register a new application to get **Client ID** and **Client Secret**
4. Set a **Redirect URI** (e.g. `http://localhost:3002/callback`)
5. Ensure all desired scopes are checked in the dashboard
6. Note: the dashboard does NOT expose `token_endpoint_auth_method`. The default is `client_secret_post`. If the server later requests `client_secret_basic`, the only fix is to delete and recreate the app.

### Step 2: OAuth2 Authorization Code Flow

Whoop uses standard OAuth2 Authorization Code flow. PKCE is not required.

**Endpoints:**
- Authorization: `https://api.prod.whoop.com/oauth/oauth2/auth`
- Token: `https://api.prod.whoop.com/oauth/oauth2/token`

**Available Scopes:**
- `read:recovery` — Recovery score, HRV, resting heart rate
- `read:cycles` — Daily Strain, average heart rate per cycle
- `read:workout` — Workout data, activity Strain, average heart rate
- `read:sleep` — Sleep performance %, sleep stage durations
- `read:profile` — Name, email
- `read:body_measurement` — Height, weight, max heart rate

**Auth URL generation:**
```python
import secrets, urllib.parse

state = secrets.token_urlsafe(16)  # minimum 8 chars required — Whoop enforces this

auth_url = (
    "https://api.prod.whoop.com/oauth/oauth2/auth"
    "?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
    f"&scope={urllib.parse.quote(SCOPES, safe='')}"
    f"&state={state}"
)
```

**Callback handling (two scenarios):**

*Scenario A — same machine:* Run a local HTTP server on port 3002 that handles the redirect and immediately exchanges the code.

*Scenario B — user on a different device (phone):*
1. Generate `state` + auth URL on the Hermes machine
2. Send the auth URL to the user via Telegram
3. User authorizes on phone → gets redirected to `localhost:3002` (which won't resolve on phone)
4. User copies the **entire redirect URL** from the browser address bar and pastes it in chat
5. Agent extracts `code` from URL query param and immediately exchanges it
6. Codes expire in ~2 minutes — if exchange fails with 403/1010, generate fresh URL and retry immediately

**Token exchange:**
```python
import urllib.request, urllib.parse

token_data = {
    'grant_type': 'authorization_code',
    'code': code_extracted_from_url,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI
}
data = urllib.parse.urlencode(token_data).encode()
req = urllib.request.Request(
    'https://api.prod.whoop.com/oauth/oauth2/token',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
with urllib.request.urlopen(req) as resp:
    tokens = json.loads(resp.read())
```

**Token exchange response:**
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read:recovery read:cycles...",
  "refresh_token": "..."
}
```

### Step 3: Refresh Tokens

Access tokens expire in 1 hour:
```python
data = urllib.parse.urlencode({
    'grant_type': 'refresh_token',
    'refresh_token': REFRESH_TOKEN,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET
}).encode()
req = urllib.request.Request(TOKEN_URL, data=data, headers={
    'Content-Type': 'application/x-www-form-urlencoded'
})
with urllib.request.urlopen(req) as resp:
    new_tokens = json.loads(resp.read())
```

### Step 4: Fetch Data

Base URL: `https://api.prod.whoop.com/`. Header: `Authorization: Bearer {access_token}`.

**Profile:** `GET /v2/user/profile/basic`
**Recovery (latest):** `GET /v2/recovery?limit=1`
**Cycle (current):** `GET /v2/cycles?limit=1`
**Sleep (last night):** `GET /v2/sleep?limit=1`
**Workout (recent):** `GET /v2/workout?limit=5`
**Body measurements:** `GET /v2/user/measurement/body`

**Date range queries:**
```python
from datetime import datetime, timedelta
start = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
end = datetime.now().isoformat() + "Z"
# ?start={start}&end={end}&limit=10
```

### Step 5: Schedule Automated Data Pull

Use `cronjob` to periodically fetch Whoop data (e.g., daily morning recovery + sleep report to Telegram).

## Common Pitfalls

### Auth Code Expiry
Authorization codes live ~2 minutes. User must paste the callback URL immediately. If token exchange returns HTTP 403 `error code: 1010`, the code expired. Generate fresh URL and retry.

If you get repeated 403/1010 even with fresh codes that were pasted within seconds, wait 30-60s (rate limiting) and retry. After 3-4 attempts, the problem is likely not expiry — move to the credentials section below.

### 401 invalid_client vs 403 error code 1010
Two different errors, different causes:

- **HTTP 401 `invalid_client`**: Client ID or Client Secret is wrong. This happens when credentials were copied from a phone screenshot with OCR homoglyph errors, or manually transcribed with typos. Whoop may also hint about `client_secret_post` vs `client_secret_basic` mismatch.
- **HTTP 403 `error code: 1010`**: Auth code expired, scopes not approved in dashboard, or rate-limited. Regenerate auth URL and retry immediately.

### Credential Copying Is Unreliable via Screenshots
EasyOCR and manual transcription from phone screenshots frequently introduce Cyrillic/Latin homoglyph errors: `а` vs `a`, `е` vs `e`, `о` vs `o`, `с` vs `c`, `g` vs `9`, `b` vs `6`. The resulting string looks correct but authentication fails silently with `invalid_client`.

**Always** ask the user to copy-paste credentials from the dashboard directly. If on a different device, have them use the browser's native "Copy" button (not select+drag) and paste into chat. Verify each character if possible.

### No Dashboard Toggle for Auth Method
Whoop developer dashboard does NOT expose `token_endpoint_auth_method`. If the app defaults to `client_secret_post` but the server demands `client_secret_basic`, the only fix is to delete and recreate the app. Creating a new app with a different name sometimes resets the default.

### Recreating the App
If persistent 401 or 403 errors after multiple fresh auth code attempts:

1. Delete the app on developer.whoop.com
2. Create a new app with:
   - Different app name (e.g. append version number)
   - Same redirect URI: `http://localhost:3002/callback`
   - All 6 scopes CHECKED in dashboard (this matters — URL alone isn't enough)
   - Copy fresh Client ID + Client Secret immediately via Cmd+C (not OCR, not screenshot)
3. The new app sometimes resets the `token_endpoint_auth_method` default that was causing issues
4. Start the OAuth flow from scratch with the new credentials
5. The previously generated auth codes are worthless — generate a fresh auth URL

If even the recreated app fails with 401 `invalid_client`, the credentials being pasted have character corruption. Ask the user to read each character group aloud, or switch to a different communication channel (e.g. voice note reading hex characters).

### State Validation
Whoop enforces minimum 8-char state. Always generate with `secrets.token_urlsafe(16)`. If too short: `error=invalid_state`.

### localhost Callback on Different Device
When the user opens the auth URL on a phone, the redirect to `localhost:3002` won't resolve. The user must manually copy the full redirect URL from the browser address bar and paste it in chat. Do NOT expect a local server to receive the callback in this case.

### Token Exchange Script
Write exchange requests to a `.py` file and run with `python3 file.py`. Inline shell escaping with complex dicts and nested quotes triggers bash parsing errors.

### Server Port Conflicts
If port 3002 is busy: `lsof -ti:3002 | xargs kill` or `pkill -f callback_server`.

### Dashboard Scopes
Verify all requested scopes are actually checked/selected in the developer dashboard app settings. The auth URL alone is not enough if scopes aren't approved at the app level.

### Invalid Client despite Correct Credentials
If `client_secret_post` is the app's default (and Whoop dashboard shows no option to change it), but the server returns hints about `client_secret_basic`:
- Deleting and recreating the app does NOT fix this — the new app also defaults to `client_secret_post`
- The Whoop developer dashboard has NO setting to change `token_endpoint_auth_method`
- Both `-u "client_id:secret"` (Basic Auth header) and `-d "client_id=...&client_secret=..."` (body post) fail with the same `invalid_client` error
- The resulting HTTP 401 body includes `error_hint` mentioning the mismatch, but there is no known fix — the app's default auth method is set at creation and the dashboard doesn't expose it
- **If verified credentials fail both auth methods on a fresh app, this is a Whoop platform limitation.** Document it for the user and pivot to an alternative integration approach (manual data export, or third-party Whoop data aggregator)
- If even the recreated app fails 401 with verified credentials, the issue may be character corruption from copy-paste or OCR homoglyphs

### Phone-to-Server OAuth Flow
When user is on phone and agent on server:
1. Generate auth URL + state on server
2. Send URL via Telegram
3. User authorizes on phone → redirected to `localhost:3002` (fails on phone)
4. User copies full redirect URL from browser and pastes in chat
5. Agent immediately extracts code and exchanges it
6. Server-side HTTP listener on port 3002 is ONLY useful if user is on the same machine — skip it for phone flow

### Rate Limiting
Whoop API rate limits are undocumented. If getting 403/1010 repeatedly even with fresh codes, wait 30-60 seconds between attempts.

## References

- `references/integration-status.md` — Current integration state per tracker
- `references/whoop-oauth-commands.md` — Exact curl/Python commands for OAuth flow, token exchange, server scripts, and troubleshooting

## Non-Interactive OAuth Setup Flow

When the user cannot sit at the Hermes machine (e.g. interacting via Telegram from phone):

1. Generate `state` + auth URL on the Hermes machine
2. Send the auth URL to the user via Telegram
3. User opens on phone, authorizes, copy-pastes the redirect URL back
4. Agent extracts `code` from URL and exchanges immediately (codes expire ~2 min)
5. If 403/1010 → generate fresh URL, retry immediately
6. If 401/invalid_client → credentials are corrupted. Ask to:
   - Copy-paste from dashboard (not OCR/screenshot)
   - Or recreate the app
7. Save `refresh_token` for permanent access
8. Store tokens in a JSON file (`/tmp/` or profile dir) for cron job use

## Preserving Credentials

Whoop API credentials (client_id, client_secret) should be saved to memory under `memory` target so they survive across sessions. Tokens (access + refresh) go to a local JSON file for runtime use.
