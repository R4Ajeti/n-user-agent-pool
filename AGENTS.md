# AGENTS.md

## Project

Project name: `user_agent_pool`

Repository/package name: `n-user-agent-pool`

This is a small reusable Python package for finding, generating, caching, and returning realistic desktop Chrome user-agent strings based on the latest Chrome versions.

The project should follow the structure and quality bar of the previous `n-elastic-ip-pool` project, but the domain is Chrome user-agent pooling, not Elastic IP management.

The main external source of truth for Chrome versions is the official Chrome for Testing endpoint:

```text
https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json
```

The package must keep responsibilities separated between service, repo, proxy, helper, and constant layers.

## Codex Instructions

Before making changes, read this file and follow the relevant skill from the `skill/` directory.

Use repository skills for repeatable workflows:

- `skill/n-layer-scaffold/SKILL.md`
- `skill/service-boundary-review/SKILL.md`
- `skill/test-placeholder/SKILL.md`
- `skill/proxy-example-contract/SKILL.md`

If the skill files still mention the previous Elastic IP project, treat their architecture guidance as a template and adapt names and behavior to this Chrome user-agent pool project.

If Codex native skill discovery is available, use the `.agents/skills` symlink, which points to `skill/`.

When the user explicitly says to update only one file, update only that file.

## Architecture

Use N-layer programming.

Required flow:

```text
Controller or Entry Point -> Service -> Repo -> Storage
Controller or Entry Point -> Service -> Proxy -> External API
```

The service layer coordinates application logic and exposes the public package API.

The repo layer abstracts local or in-memory data access.

The proxy layer abstracts external API calls, including Chrome for Testing and Keyval.

The helper layer contains generic reusable utility functions only.

The constant layer contains application constants only.

Required folders:

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

## Public API

Expose a clean service/class API centered on:

```text
ChromeUserAgentPoolService
```

Required public methods:

- `latest()`
- `latest(count)`
- `random()`

Behavior:

- `latest()` returns a single latest Chrome user-agent string.
- `latest(count)` returns up to `count` Chrome user-agent strings, ordered from newest to older.
- `random()` returns a random Chrome user-agent string from the latest available generated pool.
- `random()` must persist the last returned random user-agent string in configured state; use in-memory repo state when Keyval is not configured, and Keyval only when `KEY_VAL_BASE_URL` is explicitly set.
- `random()` must avoid returning the exact same full user-agent string twice in a row when alternatives exist.
- If only one user-agent exists, `random()` may return the same value again, but that edge case must be handled intentionally.

Suggested internal service methods:

- `fetchLatestChromeVersions`
- `generateUserAgents`
- `getCachedUserAgents`
- `saveUserAgents`
- `getLastRandomUserAgent`
- `saveLastRandomUserAgent`

Public methods must remain simple. Internal methods may coordinate proxies, repos, helpers, and constants.

## Naming Rules

Use singular naming everywhere.

Use snake_case for folders and files.

Use PascalCase for classes.

Use camelCase for Python functions and methods.

Use UPPER_SNAKE_CASE for constants.

All constants must include a type suffix.

Examples:

- `CORE_LOGGER_NAME_STR`
- `DEFAULT_TIMEOUT_SECOND_INT`
- `DEFAULT_USER_AGENT_COUNT_INT`
- `MAX_CHROME_VERSION_COUNT_INT`
- `CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR`
- `KEY_VAL_USER_AGENT_LIST_KEY_STR`
- `KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR`
- `SUPPORTED_DESKTOP_PLATFORM_LIST`

Avoid generic file names when a descriptive domain name is possible.

Good examples:

- `chrome_user_agent_pool_service.py`
- `chrome_user_agent_pool_repo.py`
- `chrome_for_testing_version_proxy.py`
- `key_val_store_proxy.py`
- `user_agent_format_helper.py`
- `key_val_key_hash_helper.py`
- `chrome_user_agent_pool_constant.py`

Bad examples:

- `proxy_service.py`
- `proxy_repo.py`
- `proxy_client.py`
- `base_proxy.py`
- `api_proxy.py`
- `helper.py`
- `constant.py`

## Layer Rules

### constant

The `constant` folder contains only application constants.

Rules:

- Store constants only.
- Do not store business logic.
- Do not store runtime calculations.
- Use descriptive names.
- Use UPPER_SNAKE_CASE.
- Add a type suffix to every constant.
- Split constants into subfolders when a file becomes too large or mixes multiple domains.

Example:

```text
core/constant/chrome_user_agent_pool_constant.py
```

### helper

The `helper` folder contains only generic reusable utility functions.

Rules:

- Helpers must be safe to reuse outside the project.
- Helpers must not contain business logic.
- Helpers must not contain provider-specific logic.
- Helpers must not contain credentials or sensitive implementation details.
- Helpers should solve small generic problems such as formatting, parsing, validation, hashing, version sorting, or simple calculations.
- User-agent validation helpers should validate format only; they must not decide which user agent should be returned.

Examples:

```text
core/helper/user_agent_format_helper.py
core/helper/key_val_key_hash_helper.py
core/helper/dotted_version_format_helper.py
```

### proxy

The `proxy` folder contains external API abstraction classes.

In this architecture, a proxy is not the same thing as a network proxy or browser proxy.

A proxy is responsible for calling external systems, providers, HTTP APIs, SDKs, or remote services and converting their responses into clean internal data.

Services must not call external APIs directly. Services should call proxy classes.

Required flow:

```text
Service -> Proxy -> External API
```

Rules:

- Proxy classes make external API calls.
- Proxy classes abstract external providers from services.
- Proxy classes handle request construction.
- Proxy classes handle response parsing and mapping.
- Proxy classes handle provider-specific errors.
- Proxy classes must not contain business rules.
- Proxy classes must not contain local storage/database logic.
- Proxy classes must not expose credentials or raw provider secrets.
- Proxy classes must not decide which user-agent string should be selected for business use.

Chrome for Testing is an external API and must be accessed through a proxy.

Keyval is a remote key/value service and must be accessed through a proxy.

Examples:

```text
core/proxy/chrome_for_testing_version_proxy.py
core/proxy/key_val_store_proxy.py
```

Good proxy names:

- `chrome_for_testing_version_proxy.py`
- `key_val_store_proxy.py`
- `public_chrome_version_proxy.py`
- `remote_user_agent_source_proxy.py`

Bad proxy names:

- `proxy_client.py`
- `base_proxy.py`
- `api_proxy.py`
- `some_thing_proxy.py`

Whenever a proxy class is implemented or modified, follow:

- `skill/proxy-example-contract/SKILL.md`

Every proxy implementation must include matching raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

A proxy implementation is not complete unless these files are added or updated.

### service

The `service` folder contains business logic.

Rules:

- Services coordinate repos, proxies, helpers, and constants.
- Services expose the public `latest` and `random` methods.
- Services contain business rules.
- Services decide which Chrome versions are usable.
- Services decide how user-agent strings are generated from versions and platform templates.
- Services decide ordering for `latest(count)`.
- Services decide how `random()` avoids returning the same full user-agent string twice in a row.
- Services decide when to use remote Chrome for Testing data and when to fall back to cached Keyval data.
- Services decide when to raise a clear custom error because no valid remote or cached user-agent pool exists.
- Services must not contain raw database/storage logic.
- Services must not call external APIs directly.
- Services must call proxy classes for external API communication.
- Services must call repo classes for local or in-memory data access.

Example:

```text
core/service/chrome_user_agent_pool_service.py
```

### repo

The `repo` folder contains data access logic.

Rules:

- Repos hide local or in-memory storage details from services.
- Repos handle create/read/update/delete operations for local project state.
- Repos do not contain business rules.
- Repos do not call external APIs directly.
- Repos do not decide which Chrome version or user-agent string is usable.
- The first version may use placeholder or in-memory repo methods only.
- If persistent storage is remote Keyval, keep HTTP behavior in `core/proxy/key_val_store_proxy.py`.

Example:

```text
core/repo/chrome_user_agent_pool_repo.py
```

## Chrome Version Source Rule

Use the official Chrome for Testing endpoint as the main source of truth for Chrome versions:

```text
https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json
```

Rules:

- Fetch this endpoint only through `core/proxy/chrome_for_testing_version_proxy.py`.
- Do not fetch it directly from the service.
- Do not scrape unrelated websites for user-agent strings.
- Do not hardcode a permanent Chrome version list as the primary source of truth.
- Validate that returned Chrome versions are usable dotted version strings.
- Sort versions numerically by dotted version components, not lexicographically.
- Ignore invalid, empty, malformed, or incomplete version values.
- If the endpoint is unavailable, the service should fall back to cached user-agent strings from Keyval.
- If the endpoint fails and there is no valid cache, raise a clear custom error.

Suggested custom errors:

- `ChromeUserAgentPoolUnavailableError`
- `ChromeVersionPayloadError`

## User-Agent Generation Rule

Generate realistic desktop Chrome user-agent strings.

The latest Chrome version must be inserted into the `Chrome/<chromeVersion>` section.

Supported desktop platforms should include:

- Windows
- macOS
- Linux

Example platform formats:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<chromeVersion> Safari/537.36
```

Rules:

- Generate only non-empty valid Chrome user-agent strings.
- Do not return malformed values.
- Do not generate mobile user agents unless a future task explicitly asks for them.
- Do not generate non-Chrome browser user agents unless a future task explicitly asks for them.
- Keep platform templates realistic and Chrome-compatible.
- Generate combinations across available Chrome versions and supported desktop platforms.
- Keep `latest(count)` ordered from newest to older.
- Keep `random()` randomized across both Chrome versions and desktop platforms.
- If the pool contains enough values, consecutive `random()` calls should usually return different combinations of OS and Chrome version.

## Keyval Persistence Rule

Use Keyval in the same style as the previous project so the package can remember state between calls.

Remote Keyval persistence is opt-in. Do not default to a public shared Keyval
namespace when `KEY_VAL_BASE_URL` is unset.

Suggested stored values:

- latest fetched/generated user-agent list
- last random user-agent returned

Rules:

- Implement Keyval external API calls only in `core/proxy/key_val_store_proxy.py`.
- Create descriptive constants for Keyval keys.
- Hash Keyval keys using the existing helper pattern from the previous project, or create a clean helper function in `core/helper/key_val_key_hash_helper.py`.
- Keep human-readable raw key constants with type suffixes.
- Do not hardcode real Keyval credentials.
- Do not commit `.env` files.
- Do not let Keyval persistence decide business behavior; the service owns that decision.

Example constants:

```text
KEY_VAL_USER_AGENT_LIST_KEY_STR
KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR
KEY_VAL_KEY_HASH_ALGORITHM_STR
```

## External API Proxy Rule

All external web API calls must be implemented inside the `core/proxy/` layer.

Services must not use raw HTTP libraries, SDK clients, or direct external API calls.

This applies to:

- Chrome for Testing
- Keyval-style key/value APIs
- any future external user-agent or browser-version provider

For Chrome for Testing, use:

```text
core/proxy/chrome_for_testing_version_proxy.py
```

For Keyval-style external APIs, use:

```text
core/proxy/key_val_store_proxy.py
```

The service should call clean domain methods exposed by proxies.

The proxy should handle:

- external endpoint URLs
- HTTP method choice
- request payload construction
- request headers
- timeout configuration
- response parsing
- response mapping
- provider-specific errors

The service should handle:

- business rules
- when data should be saved
- what the stored data means
- how remote Chrome version data affects the generated user-agent pool
- whether to return a latest user agent, a list of latest user agents, a random user agent, cached data, or an error

## Raw Example Rule

The `raw/` folder is used for safe implementation examples, request samples, and expected input/output documentation.

For every proxy named `some_thing_proxy`, create this structure:

```text
raw/
  proxy/
    some_thing_proxy/
      request.txt
      json/
        input.json
        output.json
```

For this project, expected proxy examples include:

```text
raw/
  proxy/
    chrome_for_testing_version_proxy/
      request.txt
      json/
        input.json
        output.json
    key_val_store_proxy/
      request.txt
      json/
        input.json
        output.json
```

Required files:

- `request.txt` must contain at least one example request description.
- `json/input.json` must contain at least one valid example input payload.
- `json/output.json` must contain at least one valid example output payload.

`request.txt` should include:

- endpoint or target URL
- HTTP method
- required headers if needed
- short explanation of what the request does
- notes about authentication placeholders if applicable

Raw examples must use realistic but safe sample data.

Do not include:

- real credentials
- real tokens
- API keys
- proxy passwords
- sensitive provider data
- session cookies
- private keys
- cloud credentials
- private infrastructure details

If the proxy class changes its request or response format, update the matching raw example files in the same change.

## Testing Rules

Use the same structure as `core`.

Add placeholder unit tests only during the first setup phase.

Tests may be marked as skipped or expected failure until implementation exists.

After implementation starts, add useful tests that cover:

- `latest()` returns one latest user-agent string.
- `latest(count)` returns the requested number of user-agent strings.
- `latest(count)` handles count larger than the available list safely.
- `random()` returns a valid user-agent string.
- `random()` does not return the same user agent twice in a row when alternatives exist.
- The service falls back to cached Keyval data when the remote endpoint fails.
- Invalid or empty remote responses are handled safely.
- Keyval keys are descriptive and hashed consistently.
- Generated user-agent strings contain valid Chrome versions.
- Additional edge cases that improve reliability.

Do not create tests that require:

- real Keyval credentials
- real cloud credentials
- paid external services
- internet access
- live Chrome for Testing calls
- production request dumps
- private infrastructure

Use mocks, fakes, fixtures, or placeholder tests for external proxy behavior.

## README Rules

Create or update the README when implementation work reaches package-readiness.

The README should include:

- what the package does
- installation instructions
- basic usage examples
- `latest()` example
- `latest(5)` example
- `random()` example
- explanation that `random()` avoids returning the same user agent twice in a row when alternatives exist
- explanation of the Chrome for Testing source
- environment variables needed for Keyval, if any
- test command
- license section

## Safety Rules

Do not commit secrets.

Do not hardcode real Keyval credentials.

Do not add `.env` files to git.

Do not commit:

- provider secrets
- cloud credentials
- proxy usernames
- proxy passwords
- tokens
- session cookies
- private keys
- production request dumps
- customer data
- sensitive provider data

Do not implement:

- abuse workflows
- ban bypass
- scraping evasion
- restriction bypass
- CAPTCHA bypass
- account creation abuse
- rate-limit bypass logic
- credential stuffing
- spam automation
- stealth or evasion mechanisms

This project is for legitimate browser compatibility testing, infrastructure-safe user-agent generation, package reuse, and clean external API abstraction.

## First Milestone

Create only the project skeleton, interfaces, placeholder classes, constants, raw proxy example files, and placeholder tests.

Do not implement real Chrome version fetching, real Keyval integration, live external API behavior, or final random-selection behavior yet.

Expected first structure:

```text
core/
  constant/
    chrome_user_agent_pool_constant.py
  helper/
    user_agent_format_helper.py
    key_val_key_hash_helper.py
  proxy/
    chrome_for_testing_version_proxy.py
    key_val_store_proxy.py
  service/
    chrome_user_agent_pool_service.py
  repo/
    chrome_user_agent_pool_repo.py

test/
  constant/
    test_chrome_user_agent_pool_constant.py
  helper/
    test_user_agent_format_helper.py
    test_key_val_key_hash_helper.py
  proxy/
    test_chrome_for_testing_version_proxy.py
    test_key_val_store_proxy.py
  service/
    test_chrome_user_agent_pool_service.py
  repo/
    test_chrome_user_agent_pool_repo.py

raw/
  proxy/
    chrome_for_testing_version_proxy/
      request.txt
      json/
        input.json
        output.json
    key_val_store_proxy/
      request.txt
      json/
        input.json
        output.json
```

## Second Milestone

Implement local, placeholder-safe service behavior without live external providers.

Implement:

- dotted Chrome version validation
- deterministic user-agent generation from supplied version data
- Windows, macOS, and Linux desktop platform templates
- `latest()` and `latest(count)`
- `random()` with injected or fake state
- no-consecutive-repeat behavior when alternatives exist
- in-memory repo behavior where useful

Do not require internet access or real Keyval credentials in tests.

## Third Milestone

Add external integration only after the service contract is stable.

Implement through proxy classes only:

- Chrome for Testing version fetch
- Keyval state read/write
- fallback from remote endpoint failure to cached Keyval user-agent pool

When adding or modifying these proxies, also add or update required raw example contract files under:

```text
raw/proxy/<proxy_name>/
```

The service must call proxy classes.

The service must not directly call external provider APIs.

## Fourth Milestone

Prepare the package for public repository use.

Add or verify:

- README
- type hints
- helpful docstrings
- package metadata
- test command
- license section
- no secrets or live-provider assumptions

## Completion Checklist

Before finishing any task, verify:

- N-layer structure is respected.
- Singular naming is used.
- File names are descriptive.
- Constants use UPPER_SNAKE_CASE and type suffixes.
- Service contains business logic only.
- Repo contains data access only.
- Proxy contains external API abstraction only.
- Helper contains generic reusable utility logic only.
- Public methods are `latest` and `random`.
- Chrome for Testing calls are only in the proxy layer.
- Keyval calls are only in the proxy layer.
- User-agent strings are validated before return.
- `random()` avoids exact consecutive repeats when alternatives exist.
- Tests do not call real external providers.
- No credentials or secrets are committed.
- New or modified proxy classes include matching raw examples.
- Raw example JSON files are valid JSON.
- Raw examples do not expose secrets or sensitive data.
