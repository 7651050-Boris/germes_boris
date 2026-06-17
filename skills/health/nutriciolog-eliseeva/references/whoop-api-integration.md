# Whoop API Integration (Notes)

## OAuth 2.0 Authorization Code Flow

- **Auth URL:** `https://api.prod.whoop.com/oauth/oauth2/auth`
- **Token URL:** `https://api.prod.whoop.com/oauth/oauth2/token`
- **Scopes:** `read:recovery read:cycles read:workout read:sleep read:profile read:body_measurement`

## Known Limitation (June 2026)

The developer portal at `developer.whoop.com` creates OAuth apps that:
1. Default to `client_secret_post` authentication method
2. Have **no UI setting** to change the method to `client_secret_basic`
3. There is no "Edit" button — apps cannot be reconfigured after creation
4. The production token endpoint (`api.prod.whoop.com/oauth/oauth2/token`) **requires** `client_secret_basic` (HTTP Basic Auth header)

This mismatch causes `401 invalid_client` with error code `1010` regardless of:
- Sending credentials via Basic Auth header
- Sending credentials in POST body
- Using any grant_type (authorization_code, client_credentials, password)

**Status:** Blocked until Whoop either adds the `token_endpoint_auth_method` setting to the dev portal or the token endpoint accepts `client_secret_post`.

### What was tried
- Both `client_secret_basic` (Authorization header) and `client_secret_post` (body params)
- PKCE code challenge (S256) — not required, auth code flows without it
- Multiple app registrations with identical results
- Various grant types (authorization_code, client_credentials, password)

### Workaround ideas (untested)
- Contact Whoop developer support to have the auth method changed server-side
- Investigate if the "Trusted Partner" OAuth flow works (uses `clientCredentials` at a different token URL: `https://api.prod.whoop.com/developer/v2/partner/token`) — but this requires partner-level access
- Monitor for changes to the dev portal UI
