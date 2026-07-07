Add optional Firebase persistence for historical used Chrome user-agent values.

The goal is to let the package record a history of user-agent strings that were
returned in the past, without requiring Firebase for normal local use.

## Requirements

Support two optional Firebase backends:

- Firebase Realtime Database
- Firebase Firestore

Both backends must be disabled unless their required environment variables are
configured.

Use base64-encoded credential values from environment variables. If a base64
credential value is present, decode it at runtime and use it only in memory.
Never write decoded credentials to disk, logs, raw examples, test fixtures, or
the README.

Suggested environment variables:

```text
FIREBASE_REALTIME_DATABASE_CREDENTIAL_BASE64
FIREBASE_REALTIME_DATABASE_URL
FIREBASE_FIRESTORE_CREDENTIAL_BASE64
FIREBASE_FIRESTORE_PROJECT_ID
USER_AGENT_HISTORY_BACKEND
```

`USER_AGENT_HISTORY_BACKEND` may support values such as:

```text
memory
keyval
firebase_realtime_database
firebase_firestore
```

Default behavior must remain local/offline-safe. If no Firebase environment is
configured, the service must continue working with the in-memory repo and any
existing optional Keyval behavior.

## Architecture

Follow the existing N-layer structure.

External Firebase communication must be implemented only through proxy classes.
Services must not call Firebase SDKs, REST APIs, or HTTP clients directly.

Suggested files:

```text
core/proxy/firebase_realtime_database_history_proxy.py
core/proxy/firebase_firestore_history_proxy.py
core/repo/user_agent_history_repo.py
core/helper/base64_json_decode_helper.py
```

Only add helper functions that are generic and reusable. A base64 JSON decode
helper is acceptable if it validates input format only and does not know about
Firebase business behavior.

The service layer owns business decisions:

- when a returned user-agent should be appended to history
- which history backend is enabled
- how many history rows to keep, if a limit is implemented
- what to do when history persistence fails
- how history persistence interacts with `random()` no-repeat behavior

Firebase persistence failures must not break `latest()` or `random()` unless a
future task explicitly asks for strict persistence.

## History Data

Record safe, non-secret metadata for each used user-agent value:

```json
{
  "userAgent": "Mozilla/5.0 (...) Chrome/150.0.7871.46 Safari/537.36",
  "chromeVersion": "150.0.7871.46",
  "platformFamily": "Windows",
  "sourceMethod": "random",
  "createdAtUnixSecond": 1760000000
}
```

Do not store request headers, cookies, auth tokens, decoded Firebase credentials,
private URLs, client IP addresses, or any user-identifying data.

Use history only for legitimate observability and package behavior. Do not add
abuse, stealth, ban-bypass, CAPTCHA-bypass, scraping-evasion, account-abuse, or
rate-limit-bypass workflows.

## Public API

Keep the primary public API centered on:

```text
ChromeUserAgentPoolService.latest()
ChromeUserAgentPoolService.latest(count)
ChromeUserAgentPoolService.random()
```

If history inspection is added, keep it small and clearly named, for example:

```text
history(count)
```

Do not make Firebase configuration required for package import or basic usage.

## Raw Proxy Examples

Because Firebase is an external provider, each Firebase proxy must include raw
example contract files:

```text
raw/proxy/firebase_realtime_database_history_proxy/request.txt
raw/proxy/firebase_realtime_database_history_proxy/json/input.json
raw/proxy/firebase_realtime_database_history_proxy/json/output.json

raw/proxy/firebase_firestore_history_proxy/request.txt
raw/proxy/firebase_firestore_history_proxy/json/input.json
raw/proxy/firebase_firestore_history_proxy/json/output.json
```

Raw examples must use placeholder values only. Do not include real Firebase
service account JSON, private keys, project IDs, database URLs, tokens, or
production request dumps.

## Tests

Add offline tests only.

Tests must not call live Firebase services, require internet access, or require
real credentials.

Cover at least:

- base64 JSON credential decoding succeeds for valid sample JSON
- invalid base64 values are rejected safely
- missing Firebase env vars disable Firebase persistence
- Realtime Database proxy maps a safe internal history record to its request
  payload without exposing credentials
- Firestore proxy maps a safe internal history record to its request payload
  without exposing credentials
- service appends a history entry after `random()` when a fake history backend is
  enabled
- history persistence failure does not prevent `random()` from returning a valid
  user-agent string
- raw Firebase example JSON files are valid JSON

Use fakes, mocks, or local fixtures at the proxy boundary. Do not add tests that
depend on Firebase SDK initialization with real credentials.

## Documentation

Update the README only after implementation is complete.

Document:

- Firebase history persistence is optional
- required environment variables
- credentials must be base64 encoded
- decoded credentials are kept in memory only
- local/default usage does not require Firebase
- test command

## Completion Checklist

Before finishing, verify:

- no Firebase credentials or decoded credential examples are committed
- no `.env` file is committed
- no raw examples contain real provider data
- Firebase calls live only in proxy classes
- service coordinates Firebase through clean proxy/repo interfaces
- helper layer has no Firebase-specific business logic
- tests pass offline
- `latest()` and `random()` still work without Firebase configured
