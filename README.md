# n-user-agent-pool

`n-user-agent-pool` is a small Python package for generating realistic desktop
Chrome user-agent strings from current Chrome versions. It uses official Chrome
for Testing data, keeps external calls behind proxy classes, and can persist
the last random user-agent through a Keyval-style store.

## Quick Start

Run the verbose service to discover, select, and inspect a ranked user-agent
pool:

```python
from core.service.verbose_chrome_user_agent_pool_service import (
    VerboseChromeUserAgentPoolService,
)

verboseChromeUserAgentPoolService = VerboseChromeUserAgentPoolService()
verboseChromeUserAgentPoolService.run()

print("Final selected user-agent:", verboseChromeUserAgentPoolService.finalValueStr)
print("Ranked user-agent list:", verboseChromeUserAgentPoolService.rankedUserAgentList)
```

From this repository, the same flow is available through the example runner:

```bash
. ./activate
LOGGER=INFO python testUserAgentPool.py
```

Use `LOGGER=DEBUG` when you want to inspect version fetching, user-agent
generation, Keyval reads and writes, fallback decisions, random selection, and
timing metadata.

## Installation

Install from GitHub:

```bash
pip install "git+https://github.com/R4Ajeti/n-user-agent-pool.git"
```

Install locally for development:

```bash
. ./activate
pip install -e .
```

The package requires Python 3.10 or newer and has no required third-party
runtime dependencies.

## Purpose

This project is designed for legitimate browser compatibility testing,
infrastructure-safe test data generation, and reusable package architecture. It
returns Chrome-compatible desktop user-agent strings across Windows, macOS, and
Linux platform fragments.

It does not provide scraping evasion, CAPTCHA bypass, rate-limit bypass,
credential stuffing, account abuse, spam automation, or stealth workflow logic.

## Features

- `latest()` returns one latest generated Chrome user-agent string.
- `latest(count)` returns up to `count` generated user-agent strings, ordered
  from newest to older Chrome versions.
- `random()` returns a random desktop Chrome user-agent string.
- `random()` saves the last returned value and avoids returning the exact same
  full user-agent twice in a row when alternatives exist.
- Chrome versions are fetched from official Chrome for Testing JSON endpoints.
- Remote failures fall back to cached Keyval or in-memory state when valid
  cached data exists.
- Release-channel helpers support Stable, Beta, Dev, and Canary.
- Timing helpers expose the elapsed duration and success state of public calls.
- The codebase follows an N-layer structure: service, repo, proxy, helper, and
  constant.

## Basic Usage

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

userAgentStr = service.latest()
print(userAgentStr)
```

Example output:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36
```

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

`latest(count)` is safe when `count` is larger than the generated pool. It
returns every available value.

Return a random user-agent string:

```python
userAgentStr = service.random()
```

`random()` chooses across current Chrome versions and supported desktop platform
families. When more than one value is available, it avoids returning the exact
same full user-agent string twice in a row.

## Channel-Aware Usage

Use Chrome release channels when you need Stable, Beta, Dev, or Canary
versions explicitly:

```python
stableUserAgentStr = service.latestByChannel("Stable")
betaUserAgentList = service.latestByChannel("Beta", count=3)
canaryRandomUserAgentStr = service.random("Canary")
```

Inspect versions directly:

```python
latestVersionStr = service.latestVersion()
stableVersionStr = service.latestVersion("Stable")
channelVersionMap = service.channelVersionMap()
```

Inspect supported desktop platform fragments:

```python
platformMap = service.supportedPlatformList()
```

## Timing

Every public generation and version call records timing metadata:

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

payload = service.randomWithTiming()

print(payload["result"])
print(payload["timing"]["durationSecond"])
```

The same pattern is available for latest user agents and channel-aware user
agents:

```python
latestPayload = service.latestWithTiming()
latestListPayload = service.latestWithTiming(5)
stablePayload = service.latestByChannelWithTiming("Stable")
```

You can also inspect timing after a normal call:

```python
service.random()

lastTiming = service.lastTiming()
timingHistory = service.timingHistory()
```

Timing payloads include the operation name, duration in seconds and
milliseconds, success state, error type, and completion timestamp.

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
`core/proxy/chrome_for_testing_version_proxy.py`. Services call that proxy
instead of calling external URLs directly.

## Keyval Persistence

Keyval persistence is optional for local development and useful when you want
cross-process state for `random()` no-repeat behavior.

By default, the package uses public KeyVal storage:

```text
https://api.keyval.org
```

The package stores descriptive internal keys after hashing them with SHA-256.
The stored values can include:

- latest generated user-agent list
- last random user-agent returned
- latest Chrome release-channel version map

Set these environment variables only when you want to use a custom
Keyval-compatible provider:

```bash
export KEY_VAL_BASE_URL="https://your-keyval-provider.example/store"
export KEY_VAL_AUTH_TOKEN="optional-bearer-token"
```

Do not store secrets in public KeyVal. The package never prints
`KEY_VAL_AUTH_TOKEN`, credentials, cookies, private keys, or authorization
headers.

## Logging

The package is quiet by default. Set `LOGGER` to enable runtime logs:

```bash
LOGGER=INFO python testUserAgentPool.py
LOGGER=DEBUG python testUserAgentPool.py
```

`LOGGER=INFO` prints a compact run summary. `LOGGER=DEBUG` prints safe
operational details about Chrome for Testing fetches, generated pool size,
selected random values, fallback behavior, hashed Keyval keys, and timing.

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

Current structure:

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

skill/
```

## Proxy Contract

All external web API calls must go through `core/proxy/`.

Each proxy implementation has matching safe raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

The raw examples document request shape and expected payloads without storing
credentials, tokens, private infrastructure details, or production request
dumps.

## Testing

Run the test suite from the repository root:

```bash
. ./activate
python -m unittest discover -s test -p "test_*.py"
```

Tests use fakes and local fixtures. They do not require internet access, real
Keyval credentials, paid external services, or live Chrome for Testing calls.

## Development Notes

When contributing, keep these project rules intact:

- Use singular folder and file naming.
- Keep service, repo, proxy, helper, and constant responsibilities separated.
- Keep public methods simple and centered on `ChromeUserAgentPoolService`.
- Put external API behavior in proxy classes only.
- Update matching `raw/proxy/` examples whenever a proxy contract changes.
- Validate generated user-agent strings before returning them.
- Do not commit `.env` files, credentials, tokens, cookies, or private keys.

## License

MIT
