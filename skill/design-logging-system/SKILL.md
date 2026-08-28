---
name: design-logging-system
description: Define, implement, or review the logging system for n-user-agent-pool while preserving its DEBUGGING and LOGGER environment contract, shared logger, N-layer boundaries, verbose discovery output, safe provider diagnostics, timing events, and offline tests. Use for requests to add or change logs, choose log levels or fields, diagnose duplicate or missing output, review credential safety, document diagnostics, or test logging behavior.
---

# Design Logging System

## Goal

Keep logging aligned with the repository's existing behavior: quiet by default, useful at `INFO` or `DEBUG`, safe around provider credentials, and owned by the correct N-layer component.

## Inspect the Current Contract First

Read the files relevant to the requested change before editing. Treat their current behavior and tests as the source of truth:

- `AGENTS.md`
- `core/constant/chrome_user_agent_pool_constant.py`
- `core/helper/logger_config_helper.py`
- `core/service/chrome_user_agent_pool_service.py`
- `core/service/verbose_chrome_user_agent_pool_service.py`
- each affected file in `core/proxy/`
- `test/helper/test_logger_config_helper.py`
- affected proxy and service tests
- the `Diagnostics` section in `README.md`

Preserve current log wording, field names, level choices, and tested behavior unless the user explicitly requests a contract change. Honor an instruction to update only one file.

## Preserve the Existing Shape

Use the shared `user_agent_pool` logger for operational logs. Keep the explicit verbose runner as a separate user-facing report.

```text
DEBUGGING (preferred) or LOGGER environment variable
        |
        v
configureLoggerFromEnv
        |
        v
shared user_agent_pool logger
        |
        +--> service business-flow and timing logs
        +--> proxy provider and transport logs

VerboseChromeUserAgentPoolService
        |
        v
injected outputFunc for a deterministic local report
```

Keep layer ownership as follows:

| Layer | Logging responsibility |
| --- | --- |
| `constant` | Store logger name, environment name, format, and timing field constants only. |
| `helper` | Configure a supplied logger generically; do not add domain decisions. |
| `service` | Log public operations, business decisions, filtering, selection, cache fallback, history routing, and operation timing. |
| `proxy` | Log safe request lifecycle, provider response shape/counts, status, byte counts, and provider-specific failures. |
| `repo` | Keep storage access simple. Do not configure logging or move business-event decisions here. |
| verbose service | Print the discovery narrative, selected value, ranked values, safety note, options, and elapsed time through `outputFunc`. |

Do not use logging to bypass the required `Service -> Proxy -> External API` or `Service -> Repo -> Storage` flows.

## Keep the Configuration Contract

Preserve these current constants and semantics:

```python
CORE_LOGGER_NAME_STR = "user_agent_pool"
LOGGER_LEVEL_ENV_STR = "LOGGER"
DEBUGGING_ENV_STR = "DEBUGGING"
LOGGER_FORMAT_STR = "%(asctime)s %(levelname)s %(name)s: %(message)s"
```

Configure the logger through `configureLoggerFromEnv` from service and proxy construction paths that need it.

- `DEBUGGING=true` selects `DEBUG`; `DEBUGGING=false` selects `INFO`.
- When both variables are nonblank, `DEBUGGING` takes precedence over `LOGGER`.
- Ignore blank `DEBUGGING` and fall back to `LOGGER`.
- Return the named logger unchanged when both variables are missing or blank. This keeps normal package use quiet.
- Strip and uppercase the configured level name.
- Resolve valid standard `logging` levels dynamically.
- Fall back to `INFO` for an invalid non-empty level.
- Set `propagate = False` only when package logging is enabled.
- Add at most one `StreamHandler`; reuse existing handlers on later configuration calls.
- Apply the selected level to the logger and every attached handler.
- Avoid `logging.basicConfig()` and avoid changing the root logger.
- Use module-level `logging.getLogger(CORE_LOGGER_NAME_STR)` instances.
- Use parameterized logging calls such as `logger.debug("... count=%s", count)` instead of eager f-strings.

Keep configuration idempotent so constructing several services and proxies does not duplicate every line.

## Follow the Current Message Style

Write a short human-readable event phrase followed by stable `camelCaseField=%s` pairs. Prefer counts, booleans, types, source names, versions, platform families, status codes, and safe URLs.

Use existing phrases and field names when extending a flow. Representative current patterns include:

```python
logger.debug("Latest user-agent requested count=%s", count)
logger.debug(
    "Chrome user-agent pool resolved from cache cachedUserAgentCount=%s",
    len(cachedUserAgentList),
)
logger.debug(
    "Random user-agent selected chromeVersion=%s platformFamily=%s",
    chromeVersionStr,
    platformFamilyStr,
)
logger.info(
    "Operation completed operation=%s durationSecond=%.2f success=%s errorType=%s",
    operationNameStr,
    durationSecondFloat,
    successBool,
    errorTypeStr,
)
```

Do not introduce a second message convention, JSON logging dependency, correlation system, or different logger hierarchy unless the task explicitly asks for it.

## Apply the Existing Level Semantics

Use `DEBUG` for detailed flow explanation:

- service or proxy initialization using configuration booleans and safe values
- public request parameters and normalized filters
- remote fetch start, success, parse, and validation
- raw, valid, kept, skipped, generated, and candidate counts
- cache source and remote-to-Keyval-to-repo fallback decisions
- random previous-value exclusion and selected Chrome version/platform family
- Keyval read/write start, miss, skip, success, safe failure, chunking, and JSON type
- Firebase backend selection, configured booleans, append result, and safe failure type
- timing persistence details

Use `INFO` only for the existing high-value operational summaries:

- `Operation completed operation=... durationSecond=... success=... errorType=...`
- the last-random Keyval location summary containing safe URLs, save status, Chrome version, and platform family

Do not promote the many existing diagnostic branches to `INFO`; that would make `LOGGER=INFO` noisy and duplicate the verbose runner.

Add `WARNING` or `ERROR` only when a new requirement needs an operator-visible condition. Keep expected fallbacks at `DEBUG`. Avoid logging an exception at several layers. Log it where it is handled or converted, then preserve the existing typed exception behavior.

## Cover the Existing Operational Flows

When modifying a flow, keep its log story complete.

### Public service operations

Wrap timed public methods through `runTimedOperation`. Keep operation names aligned with the API, including `latest`, `random`, `latestByChannel`, `latestVersion`, `channelVersionMap`, and `history`. Log request parameters at `DEBUG`, the resolved result shape or safe selection metadata at `DEBUG`, and the completion timing at `INFO`.

### Chrome version discovery and generation

Log the public Chrome for Testing endpoint, request outcome, response byte count, payload type or top-level keys, extracted raw counts, valid counts, capped counts, newest version, and channel map. Keep provider parsing in the proxy and version usability/generation decisions in the service.

Log generated-pool inputs and outcomes with the current fields:

- `inputVersionCount`
- `validVersionCount`
- `platformCount`
- `generatedUserAgentCount`
- `skippedUserAgentCount`

### Random selection

Log normalized channel/platform options, source, original and filtered pool sizes, whether a previous value existed, whether it was excluded, and the selected `chromeVersion` and `platformFamily`. Do not log the full selected user-agent in internal operational logs.

### Cache and provider fallback

Log the attempted source and the chosen source. Preserve the current sequence and vocabulary around remote failure, Keyval cache, in-memory repo state, and unavailable-after-all-attempts. Keep expected optional-provider failures safe and non-fatal where the service already treats them that way.

### Keyval

Log descriptive keys, hashed keys, safe URL variants, configured booleans, public URL mode, namespace presence, token presence as a boolean, status codes, value types, and byte/character/chunk counts.

Use `getSafeBaseUrlForLog`, `buildSafeGetUrlForLog`, `buildSafeSetUrlForLog`, and safe chunk URL helpers for URL output. Never substitute a raw URL when a safe helper exists.

### Firebase history

Log only configuration booleans, safe collection/history paths, backend name, append outcome, and exception type. Keep base64 credentials and decoded credential content out of logs.

### Verbose discovery report

Keep `VerboseChromeUserAgentPoolService` deterministic and testable through injected `outputFunc` and `perfCounterFunc`. Preserve its `[run]` and `[cache]` prefixes, hashed storage key, effective log level, Keyval safety note, normalized options, selected user-agent, ranked list state, and elapsed seconds. Preserve its current INFO muting behavior when preventing duplicate core output.

## Enforce the Safety Boundary

Never log:

- `KEY_VAL_AUTH_TOKEN` or any authorization header value
- Firebase base64 credentials or decoded credential dictionaries
- API keys, access tokens, cookies, session identifiers, private keys, or passwords
- raw request headers
- provider payloads that may contain secrets
- URL user info or query parameters that may contain credentials
- raw environment variable values other than explicitly safe options

Allow only intentionally safe diagnostics:

- official public Chrome for Testing URLs
- sanitized Keyval base/get/set/chunk URLs
- descriptive and hashed Keyval keys
- `tokenConfigured` or `credentialConfigured` booleans
- counts, types, status codes, operation names, error class names, durations, Chrome versions, and platform families
- full public user-agent strings only in explicit example or verbose output, not internal package logs

Treat a hash as a safe identifier only when the input is an application storage key, not as a general-purpose secret redaction method.

## Test Offline

Use `unittest`, fakes, mocks, injected clocks, and `assertLogs`. Do not call live Chrome for Testing, Keyval, or Firebase services.

Cover the affected contract:

- missing `DEBUGGING` and `LOGGER` leaves the logger at its default and adds no package output
- `DEBUGGING=true` enables debug flow logs
- `DEBUGGING=false` enables info flow logs
- `DEBUGGING` overrides `LOGGER` when both are nonblank
- `LOGGER=DEBUG` enables debug flow logs
- invalid non-empty levels fall back to `INFO`
- repeated configuration does not duplicate handlers
- public methods emit expected request, generation/fallback, selection, and timing phrases
- timing logs contain operation, two-decimal seconds, success, and error type
- Keyval logs contain descriptive/hashed keys and safe URLs without raw tokens
- Firebase logs expose configuration booleans and error types without credentials
- verbose output remains ordered, deterministic under injected dependencies, and free of secrets

Restore environment variables and logger state after each test. Use unique logger names for helper-only tests when possible. Assert that sentinel secret strings are absent from captured output whenever provider logging changes.

## Update Documentation When the Contract Changes

Keep the README `Diagnostics` section aligned with the implementation. Preserve examples equivalent to:

```bash
DEBUGGING=false python3 app/user_agent_pool_example.py
DEBUGGING=true python3 app/user_agent_pool_example.py
LOGGER=INFO python3 app/user_agent_pool_example.py
LOGGER=DEBUG python3 app/user_agent_pool_example.py
```

State that logging is quiet while both variables are unset, `DEBUGGING` takes precedence, and credentials are not logged. Document new operator-visible fields or levels only when they become part of the supported contract.

## Finish with This Review

Before completing a logging task, verify:

- the change matches current logger constants and message style
- the event belongs to the correct N-layer component
- normal package use remains quiet
- INFO remains concise and DEBUG explains the full decision path
- no handler duplication or root-logger mutation was introduced
- no secret, credential, unsafe URL, raw header, or sensitive payload can appear
- full user-agent strings remain limited to explicit verbose/example output
- provider tests remain mocked and offline
- affected logging and service tests pass
- README diagnostics match any user-facing contract change
