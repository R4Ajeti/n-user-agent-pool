Reorganize the example application, align the package version, and expand the
environment-driven logging configuration.

The goal is to keep the runnable application in a clear root-level folder,
publish one consistent package version, and support Python's standard logging
levels through a shared configuration contract.

## Application Entry Point

Move the verbose runner from:

```text
example/user_agent_pool_example.py
```

to:

```text
app/user_agent_pool_example.py
```

Keep the application as a thin entry point that calls
`VerboseChromeUserAgentPoolService`. Do not move service business logic into the
`app` folder.

Update every active command, README example, skill instruction, and relevant
prompt reference that uses the old path.

The supported runner commands should include:

```bash
DEBUGGING=false python3 app/user_agent_pool_example.py
DEBUGGING=true python3 app/user_agent_pool_example.py
LOGGER=INFO python3 app/user_agent_pool_example.py
LOGGER=DEBUG python3 app/user_agent_pool_example.py
```

## Package Version

Set the package version to `1.0.1` everywhere the package release is identified,
including:

- `pyproject.toml`
- `PACKAGE_VERSION_STR`
- `PACKAGE_USER_AGENT_STR`
- proxy request examples that send the package user agent
- version-focused tests
- current milestone and repository guidance

Do not change dotted Chrome-version fixtures merely because they contain a
similar substring. A value such as `1.0.0.0` in a Chrome-version sorting or repo
test is not the package version.

Verify that a built wheel uses a filename equivalent to:

```text
n_user_agent_pool-1.0.1-py3-none-any.whl
```

## Logging Environment Contract

Support both `DEBUGGING` and `LOGGER`.

`DEBUGGING` is a simple compatibility switch:

| Value | Effective level |
| --- | --- |
| `DEBUGGING=true` | `DEBUG` |
| `DEBUGGING=false` | `INFO` |

Values are case-insensitive and surrounding whitespace is ignored. When
`DEBUGGING` and `LOGGER` are both nonblank, `DEBUGGING` must take precedence.
A blank `DEBUGGING` value must fall back to `LOGGER`. When both variables are
missing or blank, package logging must remain off.

Support Python's standard named and numeric `LOGGER` levels:

| Name | Numeric value | Intended use |
| --- | ---: | --- |
| `NOTSET` | `0` | Defer to the ancestor logger's effective level. |
| `DEBUG` | `10` | Detailed diagnostic information. |
| `INFO` | `20` | Confirmation of normal operation. |
| `WARNING` | `30` | An unexpected condition or possible future problem. |
| `ERROR` | `40` | A failure prevented an operation from completing. |
| `CRITICAL` | `50` | A severe failure may prevent continued operation. |

Named levels must be case-insensitive. Numeric values must normalize to their
standard names so the verbose runner displays a consistent effective level.
Keep `WARN` and the commonly mistyped `WARM` as compatibility aliases for
`WARNING`. Invalid nonblank `LOGGER` values must fall back to `INFO`.

Examples:

```bash
LOGGER=WARNING python3 app/user_agent_pool_example.py
LOGGER=30 python3 app/user_agent_pool_example.py
LOGGER=ERROR python3 app/user_agent_pool_example.py
LOGGER=CRITICAL python3 app/user_agent_pool_example.py
```

## Logging Implementation

Keep the configuration logic centralized in:

```text
core/helper/logger_config_helper.py
```

The helper should:

- resolve `DEBUGGING` precedence
- normalize standard named and numeric levels
- normalize `WARN` and `WARM` to `WARNING`
- fall back to `INFO` for invalid nonblank levels
- keep logging off when both environment variables are blank or missing
- configure only the requested named logger
- avoid `logging.basicConfig()` and root-logger mutation
- add at most one stream handler
- update the logger and every attached handler to the effective level
- remain idempotent across repeated service and proxy construction

Store environment-variable names in the constant layer with descriptive type
suffixes:

```python
LOGGER_LEVEL_ENV_STR = "LOGGER"
DEBUGGING_ENV_STR = "DEBUGGING"
```

Use the shared helper from the service and every proxy that configures package
logging. The verbose service must use the same normalization logic when it
prints the effective log level and when it decides whether to mute duplicate
INFO output.

Do not add warning, error, or critical messages merely to demonstrate that the
levels exist. Emit each severity only when an actual event matches its meaning.

## Documentation

Update the README diagnostics section with:

- `DEBUGGING=true` and `DEBUGGING=false` commands
- `LOGGER=INFO` and `LOGGER=DEBUG` commands
- the `DEBUGGING` precedence rule
- quiet behavior when both variables are unset
- the standard named and numeric logger-level table
- `WARN` and `WARM` compatibility aliases
- invalid-value fallback behavior
- a statement that credentials and tokens are never logged

Document the offline test command:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Keep repository logging skills and prompt guidance aligned with the implemented
contract so future work does not restore the old `LOGGER`-only behavior.

## Tests

Keep all tests offline and credential-free.

Cover at least:

- both variables missing keeps the logger at its default
- `DEBUGGING=true` selects `DEBUG`
- `DEBUGGING=false` selects `INFO`
- both precedence directions against conflicting `LOGGER` values
- blank `DEBUGGING` falls back to `LOGGER`
- every standard named `LOGGER` level
- numeric values `0`, `10`, `20`, `30`, `40`, and `50`
- `WARN` and `WARM` normalize to `WARNING`
- `CRITICAL` resolves correctly
- invalid nonblank values fall back to `INFO`
- the verbose runner displays normalized and precedence-resolved names
- repeated configuration does not duplicate handlers
- service and proxy tests remain offline

## Completion Checklist

Before finishing, verify:

- the runner exists under `app/` and no active reference uses the old path
- N-layer boundaries remain unchanged
- package metadata and runtime identification use version `1.0.1`
- raw proxy request examples use the same package version
- `DEBUGGING` dominates `LOGGER` when both are nonblank
- named and numeric standard logging levels resolve correctly
- no credentials, tokens, raw authorization headers, or unsafe URLs are logged
- README commands match the actual implementation
- the full offline test suite passes
- the package wheel builds successfully with version `1.0.1`
