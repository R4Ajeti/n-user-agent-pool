# n-user-agent-pool

`n-user-agent-pool` is a small Python package for returning realistic desktop
Chrome user-agent strings from the latest Chrome versions.

It uses the official Chrome for Testing JSON data as its source of truth, builds
Chrome-compatible desktop user agents, and can persist the generated pool plus
the last random value in a Keyval-style store.

## Quick Start

Use the local environment first:

```bash
. ./activate
pip install -e .
```

Run the included example script:

```bash
LOGGER=INFO python testUserAgentPool.py
```

Expected output shape:

```text
=== User-agent pool discovery run ===
[run] hashed storage key: 6afea62a4fa12ba71f405a4f11932955e08ec5a6177ebd1c81aaf7b73e5c9689
[run] log level: INFO
[run] note: KeyVal is public; credentials are never stored
[cache] checking saved user-agent list
[cache] usable saved user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
[run] selected user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
[run] took 0.420 seconds
Final selected user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
Ranked user-agent list: ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36']
```

The runner prints a compact discovery transcript: the hashed KeyVal storage
key, log level, cache check, selected user-agent, elapsed time, and a small
ranked list from the generated pool.

`testUserAgentPool.py` is intentionally a small runner around
`VerboseChromeUserAgentPoolService.run()`, then prints
`finalValueStr` and `rankedUserAgentList`.

Use deeper internal logs when you want to see version fetching, generation,
fallback, KeyVal, and random-selection decisions:

```bash
LOGGER=DEBUG python testUserAgentPool.py
```

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
- Each public generation/version call records elapsed timing metadata.
- `latestWithTiming()`, `randomWithTiming()`, and
  `latestByChannelWithTiming()` return the result and timing together.
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

Install directly from this repository:

```bash
. ./activate
pip install .
```

For local development in this workspace:

```bash
. ./activate
pip install -e .
```

## Basic Usage

```python
from core import ChromeUserAgentPoolService

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
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent = service.latest()
```

By default this uses the newest Chrome versions available from the
`latest-patch-versions-per-build.json` endpoint. If you specifically want the
latest Stable channel version, use `latestByChannel("Stable")`.

## latest(count)

Return a list of the latest generated Chrome user-agent strings:

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent_list = service.latest(5)
```

`latest(count)` is safe when `count` is larger than the available generated
pool; it returns every available value.

## random()

Return a random Chrome user-agent string:

```python
from core import ChromeUserAgentPoolService

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

## Timing

Every public generation/version call records how long the call took. The timing
includes the full service call path: version fetch or cache lookup, user-agent
generation, random selection when used, and state save attempts.

Inspect the latest call timing:

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

user_agent = service.random()
timing = service.lastTiming()

print(user_agent)
print(timing["durationSecond"])
```

Return the result and timing together:

```python
from core import ChromeUserAgentPoolService

service = ChromeUserAgentPoolService()

payload = service.randomWithTiming()

print(payload["result"])
print(payload["timing"]["durationSecond"])
```

The same pattern is available for latest user agents:

```python
payload = service.latestWithTiming()
payload_list = service.latestWithTiming(5)
stable_payload = service.latestByChannelWithTiming("Stable")
```

Timing payload shape:

```python
{
    "operation": "random",
    "durationSecond": 0.12,
    "success": True,
    "errorType": None,
    "finishedAtUnixSecond": 1783332000.0,
}
```

`durationSecond` is rounded to two decimal places. A
`durationMillisecond` compatibility field is still recorded in timing metadata
for callers that need milliseconds.

You can inspect all recorded timings for the current service instance:

```python
history = service.timingHistory()
```

## Debug Logging

By default the package is quiet. Set `LOGGER=DEBUG` to see detailed logs about
Chrome version fetching, user-agent generation, Keyval reads/writes, fallback
decisions, random selection, and timing.

For a concise runtime summary, use `LOGGER=INFO`:

```bash
. ./activate
LOGGER=INFO python testUserAgentPool.py
```

`LOGGER=INFO` prints the hashed KeyVal storage key, cache status, selected
user-agent, and total operation duration in a compact run format:

```text
=== User-agent pool discovery run ===
[run] hashed storage key: 6afea62a4fa12ba71f405a4f11932955e08ec5a6177ebd1c81aaf7b73e5c9689
[run] log level: INFO
[run] note: KeyVal is public; credentials are never stored
[cache] checking saved user-agent list
[cache] usable saved user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
[run] selected user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
[run] took 0.420 seconds
Final selected user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36
Ranked user-agent list: ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7929.0 Safari/537.36']
```

Example:

```bash
. ./activate
LOGGER=DEBUG python testUserAgentPool.py
```

Debug logs include safe operational details such as:

- Chrome for Testing endpoint being fetched
- raw and valid Chrome version counts
- newest Chrome version selected
- generated user-agent pool size
- selected random Chrome version and desktop platform family
- Keyval configured or skipped status
- descriptive Keyval key names
- hashed Keyval storage keys
- public KeyVal `get/<hashed-key>` URLs for saved values
- whether Keyval values were read, missed, saved, or skipped
- fallback from remote data to Keyval or in-memory cache
- operation duration in seconds with two decimal places

The logs do not print `KEY_VAL_AUTH_TOKEN`, credentials, cookies, private keys,
or authorization headers. Keyval URL logs are sanitized and still include the
hashed storage key so you can tell where a value is stored without exposing
secrets.

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

By default the package uses public [KeyVal](https://keyval.org/) storage:

```text
https://api.keyval.org
```

For public KeyVal mode, the package writes with the JSON `POST /set` API and
logs readable `GET /get/<hashed-key>` URLs. The package hashes descriptive
constants before using them as public KeyVal keys.

The last random user-agent base URL looks like this:

```text
https://api.keyval.org/get/eb2d215b030edc308327e3c77b5d8236997054581a92b89495a8ac06a55b2a0d
```

That hash is produced from:

```python
KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR
```

The public KeyVal API is best for small values. A full desktop Chrome
user-agent can be longer than one public KeyVal value, so the package stores the
last random user-agent like this:

- `getUrl` points to the base key and usually stores a marker such as
  `chunked:2`.
- `chunkGetUrlList` points to the chunk keys that store the actual user-agent
  pieces.
- The service reads the marker, loads each chunk, and joins the pieces back into
  the original user-agent string.

When service-level INFO logs are used outside the example runner, the saved
location line includes both the base `getUrl` and the `chunkGetUrlList`:

```text
getUrl=https://api.keyval.org/get/eb2d215b030edc308327e3c77b5d8236997054581a92b89495a8ac06a55b2a0d chunkGetUrlList=['https://api.keyval.org/get/1d13a38cd8b1109d861236778f730c8c73712e843da45ea163650f6b879167e6', 'https://api.keyval.org/get/51b2579f32557055644b94e2a7b6f88bb935a19593319b098d4ffdb8d84123ce']
```

Very large values, such as the full generated user-agent list, are skipped in
public KeyVal mode unless a custom store is configured.

Set these environment variables only when you want to use a custom Keyval-style
provider:

```bash
. ./activate
export KEY_VAL_BASE_URL="https://your-keyval-provider.example/store"
export KEY_VAL_AUTH_TOKEN="optional-bearer-token"
```

The package stores:

- latest generated user-agent list
- last random user-agent returned
- latest Chrome release-channel version map

Descriptive Keyval keys are hashed before they are sent to the remote store.

Without `KEY_VAL_BASE_URL`, the service uses `https://api.keyval.org` for the
last random user-agent and in-memory state for values that are too large for the
public API.

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
