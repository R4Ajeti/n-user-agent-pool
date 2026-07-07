# n-user-agent-pool

`n-user-agent-pool` is a small Python package for generating realistic desktop
Chrome user-agent strings from current Chrome versions. It uses official Chrome
for Testing data, keeps external calls behind proxy classes, and can optionally
persist cached state through a Keyval-style store.

The project is for legitimate browser compatibility testing, infrastructure-safe
test data generation, and reusable package architecture. It does not provide
scraping evasion, CAPTCHA bypass, rate-limit bypass, credential stuffing,
account abuse, spam automation, or stealth workflow logic.

## Quick Start

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

print(service.latest())
print(service.latest(5))
print(service.random())
```

`latest()` returns one latest generated Chrome user-agent string. `latest(5)`
returns up to five generated user-agent strings, ordered from newest to older
Chrome versions. `random()` chooses across current Chrome versions and desktop
platforms, saves the last returned value to configured state, and avoids
returning the exact same full user-agent twice in a row when alternatives exist.

Example output:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36
```

## Installation

Install from GitHub:

```bash
python3 -m pip install "git+https://github.com/R4Ajeti/n-user-agent-pool.git"
```

Install locally for development:

```bash
python3 -m venv env
. env/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

The package requires Python 3.10 or newer and has no required third-party
runtime dependencies.

## Public API

Return one latest user-agent string:

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()
userAgentStr = service.latest()
```

Return a list of generated user-agent strings:

```python
userAgentList = service.latest(5)
```

Return a random user-agent string:

```python
userAgentStr = service.random()
```

You can narrow the random candidate pool:

```python
userAgentStr = service.random(
    releaseChannelList=["Stable", "Beta"],
    count=10,
    platformFamilyList=["macOS", "Linux"],
)
```

Random options:

| Parameter | Description |
| --- | --- |
| `channelStr` | Backward-compatible single release channel, such as `"Canary"`. |
| `releaseChannelList` | One channel or a list of channels: `"Stable"`, `"Beta"`, `"Dev"`, `"Canary"`. |
| `count` | Limits the candidate pool before choosing randomly. |
| `platformFamilyList` | One family or a list of families: `"Windows"`, `"macOS"`, `"Linux"`. |

Use either `channelStr` or `releaseChannelList`, not both.

## Chrome Version Source

The main source of truth is the official Chrome for Testing endpoint:

```text
https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json
```

The package also uses the official release-channel endpoint:

```text
https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json
```

Chrome for Testing calls are implemented only in
`core/proxy/chrome_for_testing_version_proxy.py`. Services call
that proxy instead of calling external URLs directly.

## Keyval Persistence

Keyval persistence is opt-in. When `KEY_VAL_BASE_URL` is unset, reads return
cache misses, writes are skipped, and `random()` still remembers the last value
inside the in-memory repo for the current service instance.

For a custom Keyval-compatible provider:

```bash
export KEY_VAL_BASE_URL="https://your-keyval-provider.example/store"
export KEY_VAL_AUTH_TOKEN="optional-bearer-token"
```

For public KeyVal, explicitly set both the public base URL and a namespace:

```bash
export KEY_VAL_BASE_URL="https://api.keyval.org"
export USER_AGENT_POOL_NAMESPACE="your-app-or-user-namespace"
```

The namespace is included in the hashed key so separate users do not share the
same public KeyVal keys. Public KeyVal is not a trusted cache; use a private
provider for stronger control. The package never prints `KEY_VAL_AUTH_TOKEN`,
credentials, cookies, private keys, or authorization headers.

Stored values can include:

- latest generated Chrome user-agent list
- last random user-agent returned
- latest Chrome release-channel version map

Large public KeyVal values are stored in chunks, including JSON payloads.

## Firebase History

Firebase history persistence is optional. By default, `random()` records
returned user-agent history only in memory for the current service instance.
No Firebase configuration is required for normal package use.

To append history records to Firebase Realtime Database:

```bash
export USER_AGENT_HISTORY_BACKEND="firebase_realtime_database"
export FIREBASE_REALTIME_DATABASE_URL="https://your-project-default-rtdb.firebaseio.com"
export FIREBASE_REALTIME_DATABASE_CREDENTIAL_BASE64="<base64-json-credential>"
```

To append history records to Firestore:

```bash
export USER_AGENT_HISTORY_BACKEND="firebase_firestore"
export FIREBASE_FIRESTORE_PROJECT_ID="your-project-id"
export FIREBASE_FIRESTORE_CREDENTIAL_BASE64="<base64-json-credential>"
```

The base64 value should decode to a JSON object with an in-memory bearer token
field such as `accessToken`, `authToken`, `idToken`, or `token`. Decoded
credentials are used only in memory and are never written to disk, raw examples,
logs, or test fixtures.

History records contain only safe metadata:

```json
{
  "userAgent": "Mozilla/5.0 (...) Chrome/150.0.7871.46 Safari/537.36",
  "chromeVersion": "150.0.7871.46",
  "platformFamily": "Windows",
  "sourceMethod": "random",
  "createdAtUnixSecond": 1760000000
}
```

Firebase failures do not prevent `random()` from returning a valid user-agent
string.

## Diagnostics

A verbose local runner is available when you want to inspect a ranked
user-agent pool and safe operational logs:

```bash
LOGGER=INFO python3 example/user_agent_pool_example.py
LOGGER=DEBUG python3 example/user_agent_pool_example.py
```

The verbose service can also be used directly:

```python
from core.service.verbose_chrome_user_agent_pool_service import (
    VerboseChromeUserAgentPoolService,
)

verboseService = VerboseChromeUserAgentPoolService()
verboseService.run(
    releaseChannelList=["Stable", "Canary"],
    count=6,
    platformFamilyList=["Windows", "Linux"],
    rankedCount=3,
)
```

## Architecture

The repository follows N-layer architecture:

```text
Controller or Entry Point
        |
        v
     Service
     /     \
    v       v
  Repo    Proxy
    |       |
    v       v
 Storage  External API
```

Layer responsibilities:

| Layer | Responsibility |
| --- | --- |
| `service` | Business rules and orchestration |
| `repo` | Local or in-memory data access |
| `proxy` | External API request and response abstraction |
| `helper` | Generic reusable utility functions |
| `constant` | Application constants only |

Current package structure:

```text
core/
  constant/
  helper/
  proxy/
  service/
  repo/

test/
  constant/
  helper/
  proxy/
  service/
  repo/

raw/
  proxy/
```

Every proxy implementation has matching safe raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

## Testing

Run the test suite from the repository root:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Tests use fakes and local fixtures. They do not require internet access, real
Keyval credentials, paid external services, or live Chrome for Testing calls.

Build a wheel locally:

```bash
python3 -m pip wheel . -w /tmp/n-user-agent-pool-wheel --no-deps
```

## Development Notes

- Use singular folder and file naming.
- Keep service, repo, proxy, helper, and constant responsibilities separated.
- Keep the stable public API centered on `ChromeUserAgentPoolService.latest()`
  and `ChromeUserAgentPoolService.random()`.
- Put external API behavior in proxy classes only.
- Update matching `raw/proxy/` examples whenever a proxy contract changes.
- Validate generated user-agent strings before returning them.
- Do not commit `.env` files, credentials, tokens, cookies, or private keys.

## License

MIT
