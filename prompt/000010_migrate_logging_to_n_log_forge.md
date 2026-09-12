# Migrate logging to n-log-forge

## Outcome and scope

Migrate `n-user-agent` to `n-log-forge` as its centralized logging solution.
Preserve the existing quiet-by-default library contract, `DEBUGGING`/`LOGGER`
precedence, concise INFO versus detailed DEBUG behavior, safe provider
diagnostics, operation timing, exception tracebacks, and the separate injected
verbose report.

Use the shared package's public facade and configuration features instead of
reimplementing handlers, formatting, timing context, or Sentry transport.
Prefer automatic module/package attribution; hardcode `n-user-agent` only if
needed to correct the display label after verification.

## Baseline

- Baseline revision: `66a0c9d` on `main`; the working tree was clean before this
  prompt was created.
- Previous prompt: [`0009_optional_sentry_logs.md`](0009_optional_sentry_logs.md).
- Existing prompt filenames use a legacy four-digit sequence. This prompt uses
  the next numeric value in the required six-digit format, `000010`.
- Applicable repository workflow: `skill/design-logging-system/SKILL.md`.
- Shared logger reference: sibling repository `../n-log-forge` at revision
  `2b425c4`.

## Coverage

| Change / requirement | Evidence | Current state | Next action |
| --- | --- | --- | --- |
| Centralize operational logging | Service/proxy logger calls | Implemented | Named shared facades now cover all operational modules |
| Preserve quiet default and env precedence | Logging skill; logger helper tests | Verified | Compatibility helper delegates configuration and keeps the quiet default |
| Preserve structured context/timing/tracebacks | Service/proxy logs and `runTimedOperation` | Verified | Shared facade/timer paths are covered by the passing suite |
| Preserve verbose injected output | Verbose service tests | Verified | Deterministic `outputFunc` reporting remains separate from operational logging |
| Remove local Sentry implementation | Removed proxy/constants/raw/tests | Implemented | Optional Sentry is owned by `n-log-forge[sentry]` |
| Required dependency and compatibility | `pyproject.toml`, `requirements.txt` | Verified | Required dependency and Python 3.14 metadata are present; wheel build passed |

## Implementation plan

1. Follow `AGENTS.md` and `skill/design-logging-system/SKILL.md`. Inventory every
   logger definition/call, constructor configuration hook, test assertion,
   diagnostics document, sample environment setting, and Sentry artifact.
2. Introduce a small repository-appropriate configuration boundary only if one
   is needed to preserve quiet-by-default behavior and current env semantics;
   delegate all handler/provider/format/timing work to `n-log-forge`.
3. Use module-named facades for service and proxy records so SOURCE remains
   meaningful. Preserve message wording and safe fields, convert stable context
   to structured metadata where this does not break the supported diagnostics
   contract, and retain lazy interpolation.
4. Replace manual operation timing with `n-log-forge` timing where behavior and
   tests remain equivalent. Preserve exception types and traceback capture.
5. Keep the verbose report deterministic and independently injectable. Remove
   custom logger formatting/configuration and Sentry code only once unused, then
   update README/environment docs and tests.
6. Add the required dependency in project metadata and the editable-install
   requirements workflow; reconcile the project's Python floor/classifiers with
   `n-log-forge`.

## Acceptance and verification

- Operational records use `n-log-forge`, identify `n-user-agent`, retain module
  sources, and remain silent by default when both controls are absent.
- DEBUG/INFO behavior, safe URLs/booleans/counts, timing records, exceptions,
  and the injected verbose report remain covered by offline tests.
- No secret values, raw provider credentials, duplicate handlers, custom Sentry
  transport, or redundant formatter/configuration helper remains.
- The deterministic test suite and package build pass, dependency metadata is
  correct, and `git diff --check` is clean.

## Implementation result

The migration is complete. Service and provider records use module-qualified
`n-log-forge` facades under the `n-user-agent` hierarchy, configuration keeps
the existing environment contract and quiet library default, and operation
timing uses the shared timer. The injected verbose report remains plain and
deterministic. Local formatting/Sentry transport was removed, docs and env
examples were updated, and all 85 tests plus the wheel metadata check pass.
