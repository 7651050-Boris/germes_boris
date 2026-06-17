# Whoop Integration Status

## Active Credentials (App 2 — "Boris_ai")
- Client ID: `2f8b1ba3-95ed-462a-a322-41e991856988`
- Client Secret: `fdd686383a29fe8c3f8ab88e44190fe6e460a0f1c6f5351fe9569098c7b4b707`
- Redirect URI: `http://localhost:3002/callback`
- Scopes: read:recovery read:cycles read:workout read:sleep read:profile read:body_measurement
- Contact: `7651050@mail.ru`
- Privacy Policy: https://gist.github.com/7651050-Boris/...
- Created: 2026-06-16

## Archived Credentials (App 1 — first reg)
- Client ID: `9f54345e-38d0-4d5d-abe1-3b6a4b18fc1c`
- Client Secret: `6aa51191685423cfe2505a966067c349347b234f2645a638008f76082f3ba31b`
- Reason for archive: Persistent 401 + 403 errors. App recreated to resolve potential auth method mismatch.

## OAuth Flow — Current State
- Application registered on developer.whoop.com ✅ (App 2)
- Credentials obtained ✅
- **Tokens NOT yet obtained** ❌ (OAuth code exchange fails)

## Attempt Log

### App 1
| # | Method | Result | Notes |
|---|--------|--------|-------|
| 1 | Auth code POST | 403/1010 | First attempt, likely code expiry |
| 2 | Auth code POST | 403/1010 | Same |
| 3 | With PKCE | access_denied | User rejected on Whoop side |
| 4 | Fast callback POST | 403/1010 | Code still expired during Telegram round-trip |
| 5 | curl POST (body) | 401 invalid_client | Client_secret correct but `client_secret_basic` required |
| 6 | curl Basic Auth | 401 + hint about `client_secret_post` | App configured for post, server wants basic |

### App 2
| # | Method | Result | Notes |
|---|--------|--------|-------|
| 1 | curl client_credentials (Basic) | 401 invalid_client | Same mismatch |
| 2 | curl client_credentials (POST) | 401 invalid_client | Even POST method fails |
| - | Auth code flow | not attempted | |

## Root Cause Analysis

The critical error chain:

1. **`invalid_client` (401 with hint)** — occurs when the app's `token_endpoint_auth_method` is `client_secret_post` but the server requests `client_secret_basic`. There is NO dashboard toggle to change this. Recreating the app does NOT fix it — the new app also gets `client_secret_post`.

2. **`403 error code 1010`** — occurs when the auth code has expired. Codes live ~2 minutes. The Telegram round-trip (user opens URL on phone → authorizes → copies URL → pastes in Telegram → agent sees it → runs script) takes longer.

3. **Possible root issue**: Whoop's token endpoint may have changed or requires header-based auth differently than documented. 

## What Worked
- EasyOCR installed and works for reading Whoop dashboard screenshots ✅
- User can generate auth URLs and copy callback URLs reliably ✅
- Auth URL generation with proper state parameter works ✅
- PKCE challenge generation works (but Whoop returned access_denied when used)

## Tools Installed
- `easyocr` (pip, 1.7.2) — for reading Whoop screenshots
- Torch 2.8.0 + torchvision 0.23.0 (CPU mode, easyocr dependency)
- Pillow 11.3.0 (for image processing)

## Next Steps
1. Try token exchange using `urllib.request` (Python) or `curl` with **both** `client_id`+`client_secret` in body AND Authorization header simultaneously
2. Debug the 401/403 discrepancy — test with a simple `curl` against the token endpoint using client_credentials grant
3. Contact Whoop developer support if unable to resolve auth method mismatch
4. Once tokens are obtained: save refresh_token, set up cron for daily data pull
5. Build Telegram message formatter for Whoop data (recovery score, sleep, HRV, strain, workout summary)
