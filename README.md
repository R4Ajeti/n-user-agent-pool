# n-user-agent-pool

`n-user-agent-pool` is a small Python package for returning realistic desktop
Chrome user-agent strings from the latest Chrome versions.

It uses the official Chrome for Testing JSON data as its source of truth, builds
Chrome-compatible desktop user agents, and can persist the generated pool plus
the last random value in a Keyval-style store.

## Features

- `latest()` returns one latest Chrome user-agent string.
- `latest(5)` returns the latest 5 generated Chrome user-agent strings.
- `random()` returns a random Chrome user agent and avoids the exact same full
  string twice in a row when alternatives exist.
- Random selection uses multiple desktop platform families: Windows, macOS, and
  Linux, with several realistic platform fragments per family.
- Default `latest()` and `random()` use the newest version pool from the
  latest-patch-per-build endpoint, not a hardcoded browser version.
- `latestByChannel("Stable")`, `latestByChannel("Beta")`,
  `latestByChannel("Dev")`, and `latestByChannel("Canary")` generate user
  agents from Chrome release-channel versions.
- `latestVersion()` and `latestVersion("Canary")` return Chrome version strings
  without building a user-agent string.
- `channelVersionMap()` returns the current Stable/Beta/Dev/Canary version map.
- If Chrome for Testing is unavailable, the service falls back to cached Keyval
  state when available.

## Source Of Truth

The package uses these official Chrome for Testing endpoints:

- [latest-patch-versions-per-build.json](https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json)
- [last-known-good-versions.json](https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json)
- [Chrome for Testing availability page](https://googlechromelabs.github.io/chrome-for-testing/)

The availability page lists the current Chrome release channels and supported
Chrome for Testing platforms such as `linux64`, `mac-arm64`, `mac-x64`, `win32`,
and `win64`. This package uses that data for version discovery, then generates
desktop browser user-agent strings for Windows, macOS, and Linux.

## Installation

From this repository:

```bash
pip install .
```

For local development in this workspace:

```bash
. ./activate
pip install -e .
```

## Basic Usage

```python
from n_user_agent_pool import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent = service.latest()
print(user_agent)
```

Example output:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36
```

## latest()

Return one latest Chrome user-agent string:

```python
from n_user_agent_pool import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent = service.latest()
```

By default this uses the newest Chrome versions available from the
`latest-patch-versions-per-build.json` endpoint. If you specifically want the
latest Stable channel version, use `latestByChannel("Stable")`.

## latest(count)

Return a list of the latest generated Chrome user-agent strings:

```python
from n_user_agent_pool import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent_list = service.latest(5)
```

`latest(count)` is safe when `count` is larger than the available generated
pool; it returns every available value.

## random()

Return a random Chrome user-agent string:

```python
from n_user_agent_pool import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent = service.random()
```

`random()` chooses from current Chrome versions and desktop platform variants.
It saves the last random value and avoids returning the same full user-agent
string twice in a row when another value exists. If the generated pool only has
one value, it may return that same value intentionally.

The random pool is built from the newest Chrome versions returned by Chrome for
Testing, then combined with Windows, macOS, and Linux desktop platform fragments.

You can also restrict random generation to a Chrome channel:

```python
stable_user_agent = service.random("Stable")
canary_user_agent = service.random("Canary")
```

## Channel-Aware Usage

Return the latest Stable channel user agent:

```python
stable_user_agent = service.latestByChannel("Stable")
```

Return multiple Beta channel user agents across desktop platforms:

```python
beta_user_agent_list = service.latestByChannel("Beta", count=3)
```

Return the latest version only:

```python
latest_version = service.latestVersion()
stable_version = service.latestVersion("Stable")
canary_version = service.latestVersion("Canary")
```

Return the release-channel version map:

```python
channel_version_map = service.channelVersionMap()
```

Return supported platform fragments:

```python
platform_map = service.supportedPlatformList()
```

## Keyval Persistence

Keyval persistence is optional for local use but recommended when you want
repeatable cross-process state, especially for `random()` no-repeat behavior.

Set these environment variables for a Keyval-style provider:

```bash
export KEY_VAL_BASE_URL="https://your-keyval-provider.example/store"
export KEY_VAL_AUTH_TOKEN="optional-bearer-token"
```

The package stores:

- latest generated user-agent list
- last random user-agent returned
- latest Chrome release-channel version map

Descriptive Keyval keys are hashed before they are sent to the remote store.

Without `KEY_VAL_BASE_URL`, the service still works with in-memory state during
the current Python process, but values are not persisted across processes.

## Error Handling

If Chrome for Testing is unavailable, the service attempts to use cached Keyval
or in-memory state. If there is no valid remote data and no valid cache, it
raises `ChromeUserAgentPoolUnavailableError`.

Invalid Chrome version payloads raise or flow into fallback handling through
`ChromeVersionPayloadError`.

## Test Command

```bash
. ./activate
python -m unittest discover -s test
```

Tests use fakes and local fixtures. They do not require internet access, Keyval
credentials, or live Chrome for Testing calls.

## Safety

This package is intended for browser compatibility testing, infrastructure-safe
user-agent generation, and clean service architecture. It does not include
scraping evasion, CAPTCHA bypass, rate-limit bypass, credential stuffing, spam
automation, or stealth workflow logic.

## License

MIT
