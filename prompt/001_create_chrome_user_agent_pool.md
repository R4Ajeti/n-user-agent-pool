Create a new public repository similar in structure and quality to my previous `n-elastic-ip-pool` project, but this time the package should be focused on finding and providing latest Chrome user-agent strings.

Suggested repository/package name:

`n-user-agent-pool`

Goal:

Build a small reusable Python package that returns realistic Chrome user-agent strings based on the latest Chrome versions.

The package should use this official Chrome for Testing endpoint as the main source of truth:

https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json

Core behavior:

1. Fetch latest Chrome versions from the Chrome for Testing JSON endpoint.
2. Generate valid Chrome user-agent strings using those versions.
3. Expose a clean service/class API similar to the previous `n-elastic-ip-pool` style. "../n-proxy"
4. Store state in Keyval, similar to the previous project, so the package can remember the last returned user agent.

Required public methods:

`latest()`

Returns the single latest Chrome user-agent string.

`latest(count)`

If `count` is provided, returns the latest `count` Chrome user-agent strings, ordered from newest to older.

Example behavior:

* `latest()` returns one string.
* `latest(5)` returns a list of 5 strings.

`random()`

Returns a random Chrome user-agent string from the latest available generated user-agent pool.

Important rule for `random()`:

* It must save the last returned random user-agent string in Keyval.
* When `random()` is called again, it must not return the exact same user-agent string twice in a row.
* If only one user-agent exists, it can return the same one, but this edge case should be handled intentionally.

User-agent format:

Generate realistic desktop Chrome user agents, for example:

`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36`

Support multiple common platforms if possible:

* Windows
* macOS
* Linux

The latest Chrome version should be inserted into the `Chrome/<version>` section.

Persistence:

Use Keyval in the same style as the previous project.

Create descriptive constants for Keyval keys.

Hash Keyval keys using the existing helper pattern from the previous project, or create a clean helper function if this is a new repository.

Suggested stored values:

* latest fetched/generated user-agent list
* last random user-agent returned

Architecture expectations:

* Keep code clean and production-ready.
* Use clear service classes.
* Avoid putting all logic in one file.
* Separate responsibilities:

  * fetching Chrome version data
  * generating user-agent strings
  * saving/loading state from Keyval
  * public service API

Suggested service name:

`ChromeUserAgentPoolService`

Suggested internal methods:

* `fetchLatestChromeVersions`
* `generateUserAgents`
* `getCachedUserAgents`
* `saveUserAgents`
* `getLastRandomUserAgent`
* `saveLastRandomUserAgent`

Public methods must remain simple:

* `latest`
* `random`

Error handling:

* If the Chrome for Testing endpoint is unavailable, fall back to cached user agents from Keyval.
* If there is no cache and the endpoint fails, raise a clear custom error.
* Validate that returned Chrome versions are usable strings.
* Avoid returning empty or invalid user-agent strings.

Testing requirements:

Add useful tests that cover:

1. `latest()` returns one latest user-agent string.
2. `latest(count)` returns the requested number of user-agent strings.
3. `latest(count)` handles count larger than available list safely.
4. `random()` returns a valid user-agent string.
5. `random()` does not return the same user agent twice in a row when alternatives exist.
6. The service falls back to cached Keyval data when the remote endpoint fails.
7. Invalid/empty remote responses are handled safely.
8. Keyval keys are descriptive and hashed consistently.
9. Generated user-agent strings contain valid Chrome versions.
10. Add any extra edge cases that improve reliability.

README requirements:

Create a strong README with:

* What the package does
* Installation instructions
* Basic usage examples
* `latest()` example
* `latest(5)` example
* `random()` example
* Explanation that `random()` avoids returning the same user agent twice in a row
* Explanation of the Chrome for Testing source
* Environment variables needed for Keyval, if any
* Test command
* License section

General quality:

* Keep the implementation minimal but clean.
* Follow the style and patterns from `n-elastic-ip-pool` where it makes sense.
* Use descriptive names.
* Add type hints.
* Add docstrings where helpful.
* Make the package ready to publish as a public GitHub repository.


Random user-agent selection requirements:

The `random()` method should be as random and realistic as possible across different desktop operating systems.

It should not only randomize the Chrome version. It should also randomize the operating system/platform part of the user-agent string.

Supported desktop platform types should include:

* Windows
* macOS
* Linux

Example platform variations:

Windows:

`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36`

macOS:

`Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36`

Linux:

`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36`

The `random()` method should randomly choose from:

1. available latest Chrome versions
2. supported desktop operating systems
3. generated user-agent combinations

Important behavior:

* `random()` should avoid returning the exact same full user-agent string twice in a row.
* It should try to distribute results across Windows, macOS, and Linux as naturally as possible.
* Do not hardcode only one OS type.
* Keep the generated user agents realistic and Chrome-compatible.
* If the pool contains enough values, consecutive calls should usually return different combinations of OS and Chrome version.
