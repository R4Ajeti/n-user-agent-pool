Capture the package changes introduced after the logging and application
configuration covered by prompt `0007_reorganize_app_version_and_logger_configuration.md`.

The goal is to align release `1.0.2`, expose selected user agents through normal
library logging, give operational logs and verbose reports a consistent format,
and document safe local environment setup.

This is an incremental prompt based on the repository through commit `b4faf7a`.
Preserve changes that are already implemented; do not repeat the application
move or logging-level normalization covered by prompt `0007`. The current
`app/user_agent_pool_app.py` filename is already reflected there.

Read `AGENTS.md` and the relevant repository skills before implementation.
Preserve N-layer boundaries and the existing public API, selection behavior,
cache fallback, opt-in remote persistence, and offline test strategy.

## Release Version and License

Advance the package release from `1.0.1` to `1.0.2` consistently in:

- `pyproject.toml`
- `PACKAGE_VERSION_STR`
- `PACKAGE_USER_AGENT_STR`, using `n-user-agent-pool/1.0.2`
- version-focused tests
- the Chrome for Testing, Keyval, Firebase Realtime Database, and Firestore raw
  request examples that identify the package in a `User-Agent` header

Do not rewrite historical prompt version targets or unrelated Chrome-version
fixtures. No provider request or response schema changes are required.

Keep the MIT license and use the copyright line:

```text
Copyright (c) 2026 R!n0
```

## Selected User-Agent Summaries

Emit selected values from `ChromeUserAgentPoolService` itself, so callers from
other packages receive the same logging behavior without using the verbose
runner.

After a successful `latest`, `random`, or `latestByChannel` operation, emit one
INFO selection summary before recording completion timing:

```python
logger.info(
    "[run] selected user-agent%s: %r operation=%s",
    " list" if isinstance(resultObject, list) else "",
    resultObject,
    operationNameStr,
)
```

Include the full returned user-agent string or list. Use representation formatting
for the result and parameterized logging. Failed operations must not emit a
successful-selection summary.

At INFO, show selection summaries and operation timing alongside existing safe
operational summaries. At DEBUG, also retain detailed pool generation, cache,
filtering, and selection diagnostics. WARNING, ERROR, and CRITICAL suppress INFO
selection and timing messages when `DEBUGGING` is unset or blank.

Keep the existing `DEBUGGING` precedence, named/numeric `LOGGER` levels, aliases,
invalid-value fallback, and quiet-by-default library configuration unchanged.

## Shared Log Identity and Format

Use these constants:

```python
CORE_LOGGER_NAME_STR = "n-user-agent-pool"
LOGGER_FORMAT_STR = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
```

Use a full date and time with milliseconds, pipe separators, severity, and the
package logger name. Operational logs and verbose report lines should share
this format:

```text
2026-08-30 18:55:54,969 | INFO | n-user-agent-pool | Total run time: 22.56 seconds operation=random
```

Add or preserve the generic `formatLogMessage` helper in
`core/helper/logger_config_helper.py`. It should accept a message, logger name,
level, and format, construct a logging record, and return formatted text without
adding handlers or changing logger levels.

Keep logger configuration centralized and idempotent. Do not mutate the root
logger, introduce duplicate handlers, or add a new logging dependency.

## Operation Timing and Verbose Output

Replace the old INFO `Operation completed ...` message with:

```text
Total run time: <two-decimal duration> seconds operation=<operation name>
```

Preserve timing records in the repo, including success status and error type.
Retain those diagnostic fields in the DEBUG `Operation timing recorded ...`
message; they need not appear in the concise INFO runtime line. Preserve existing
timing return behavior and exception propagation.

Route verbose discovery messages through a `logInfo` method that formats each
physical line with `formatLogMessage` and sends it to the injected `outputFunc`.
Suppress these INFO report lines at effective WARNING, ERROR, or CRITICAL.

Preserve the verbose report's existing discovery narrative, safe storage key,
configuration note, options, cache inspection, selected value, ranked-list state,
and duplicate-core-INFO muting behavior. Keep injected output and clock functions
for deterministic offline testing.

Use `try/finally` around the verbose run so it attempts to emit exactly one
two-decimal total-time line with `operation=run` on both success and failure,
subject to the INFO output filter. Re-raise the original operation error.

Distinguish configured library logging from explicit report output: an explicitly
invoked verbose report can still print when logging variables are unset. The
entry point also prints its final selected value and ranked list directly;
do not claim that WARNING makes the entire application silent.

## Safe Environment Example and Local Files

Provide a tracked `.env.example` documenting these settings with safe defaults
or blank values and short explanations:

- `ENVIRONMENT_PATH=env/bin/activate`
- `DEBUGGING` and `LOGGER`
- `KEY_VAL_BASE_URL` and `KEY_VAL_AUTH_TOKEN`
- `USER_AGENT_POOL_NAMESPACE`
- `USER_AGENT_HISTORY_BACKEND=memory`
- `FIREBASE_REALTIME_DATABASE_URL`
- `FIREBASE_REALTIME_DATABASE_CREDENTIAL_BASE64`
- `FIREBASE_FIRESTORE_PROJECT_ID`
- `FIREBASE_FIRESTORE_CREDENTIAL_BASE64`

Document the history backend choices: `memory`, `keyval`,
`firebase_realtime_database`, and `firebase_firestore`. Explain which Firebase
settings apply to each backend. Leave remote provider credentials and URLs blank;
do not enable a public shared Keyval namespace by default.

The example documents configuration, not automatic `.env` loading or virtual
environment activation. Do not imply that `ENVIRONMENT_PATH` is consumed by the
package or add a dotenv dependency for this change.

Ignore `experimental-resource/*`, the local `activate` file, and `commands.txt`.
Keep real `.env` files, credentials, and local development artifacts untracked
while allowing the safe `.env.example` to be committed.

## Documentation and Logging Guidance

Document library-level selection summaries, INFO/DEBUG visibility, the renamed
logger, the shared timestamp format, and two-decimal runtime messages in README
diagnostics. Preserve existing environment precedence and credential-safety
guidance.

The repository's `design-logging-system` skill still describes the older
`user_agent_pool` logger, old format/timing wording, and a prohibition on full
user-agent strings in internal logs. This prompt explicitly supersedes those
points: full selected public user-agent values are now intentional INFO output.
Align that guidance when maintaining it; do not revert current implementation
to the older contract. All restrictions on credentials, authorization headers,
unsafe URLs, private payloads, and Firebase secrets remain in force.

## Offline Verification

Use fakes, mocks, captured output, and injected clocks. Verify:

- INFO and DEBUG emit a single selection summary for a successful random call.
- DEBUG retains detailed request diagnostics that are absent at INFO.
- WARNING and higher suppress INFO selection/timing messages.
- `latest(count)` logs its returned list, including each selected value.
- Verbose report lines have the timestamp, INFO level, package name, and pipes.
- Successful verbose runs retain their selected value and ranked-list state.
- A failed verbose run emits its runtime once when INFO output is enabled and
  preserves the original error.
- Runtime messages show two decimal places and the correct operation name.
- Version metadata, runtime identification, and raw request headers agree.
- Tests restore modified environment and logger state and never call live
  Chrome for Testing, Keyval, or Firebase services.

Run the existing offline suite:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Verify that the package builds as `n_user_agent_pool-1.0.2-py3-none-any.whl`,
raw example JSON remains valid, and no secrets are introduced. Do not publish
the package or contact live providers as part of this prompt.
