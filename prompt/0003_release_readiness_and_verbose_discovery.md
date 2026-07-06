Continue the Chrome user-agent pool package from the debug logging work in
`prompt/002_add_debug_logging_for_user_agent_pool.md`.

Goal:

Polish the package toward release readiness by adding a clear verbose discovery
workflow, channel-aware helpers, timing metadata, safer Keyval behavior, and
README/package cleanup while preserving the N-layer architecture.

Keep the existing project rules from `AGENTS.md`:

- Service owns business behavior.
- Repo owns local or in-memory state.
- Proxy owns external API behavior.
- Helper owns generic reusable utilities.
- Constant owns application constants only.
- Chrome for Testing calls must stay inside the Chrome proxy.
- Keyval calls must stay inside the Keyval proxy.
- Tests must stay offline and credential-free.
- Raw proxy examples must be updated whenever proxy contracts change.
- No secrets, credentials, tokens, cookies, private keys, or production request
  dumps may be committed.

Implementation requirements:

1. Add release-channel support without replacing the required `latest()` and
   `random()` methods.
   - Support Stable, Beta, Dev, and Canary.
   - Add service helpers for channel-aware latest user agents, latest version,
     and channel version map access.
   - Fetch channel data through the official Chrome for Testing
     `last-known-good-versions.json` endpoint in the proxy layer only.
   - Cache valid channel version maps through the existing repo and Keyval
     flow.

2. Add timing metadata for public service operations.
   - Track operation name, duration in seconds, duration in milliseconds,
     success state, error type, and completion timestamp.
   - Store timing history in the repo.
   - Add helpers that return normal results together with the latest timing
     payload.
   - Use seconds rounded to two decimals for README examples and INFO logs.

3. Improve Keyval persistence safety and compatibility.
   - Keep Keyval optional.
   - Default to public `https://api.keyval.org` behavior when no custom base URL
     is provided.
   - Support public KeyVal GET and SET URL shapes.
   - Support custom Keyval-compatible providers without logging query secrets.
   - Hash descriptive keys before building URLs.
   - Add safe logging URLs that redact stored values.
   - For public KeyVal value-size limits, support chunking and reconstruction
     for large plain values where useful.
   - Never log `KEY_VAL_AUTH_TOKEN` or authorization headers.

4. Add a logger configuration helper.
   - Configure the package logger from the `LOGGER` environment variable.
   - Keep the package quiet by default.
   - Support `LOGGER=INFO` and `LOGGER=DEBUG`.
   - Add tests for default and DEBUG configuration.

5. Add a verbose discovery service.
   - Create `VerboseChromeUserAgentPoolService`.
   - It should wrap `ChromeUserAgentPoolService` rather than duplicating core
     generation logic.
   - It should print a clear run summary with:
     - hashed storage key
     - selected log level
     - Keyval safety note
     - cache check result
     - final selected user-agent
     - elapsed seconds
   - Store the final selected user-agent on `finalValueStr`.
   - Store a small ranked list of selected and nearby generated user agents on
     `rankedUserAgentList`.
   - Keep the output deterministic in tests through injected output and clock
     functions.

6. Simplify the example runner.
   - Update `testUserAgentPool.py` so it uses
     `VerboseChromeUserAgentPoolService`.
   - It should print the final selected user-agent and ranked user-agent list.
   - It should work with:

```bash
. ./activate
LOGGER=INFO python testUserAgentPool.py
LOGGER=DEBUG python testUserAgentPool.py
```

7. Prepare packaging for public repository use.
   - Keep package metadata in `pyproject.toml`.
   - Set the version to `1.0.0` when the package is ready for this milestone.
   - Ensure editable local install works.
   - Keep runtime dependencies empty unless a dependency is truly required.
   - Remove unused duplicate package wrappers if the public import path is
     intentionally exported through `core`.
   - Keep `requirements.txt` aligned with local development installation.

8. Rewrite and tighten the README.
   - Explain what the package does.
   - Show Quick Start usage with the verbose discovery service.
   - Include install commands.
   - Include basic `ChromeUserAgentPoolService` examples.
   - Document `latest()`, `latest(count)`, and `random()`.
   - Document channel-aware helpers.
   - Document timing helpers.
   - Document Chrome for Testing source endpoints.
   - Document optional Keyval environment variables.
   - Document `LOGGER=INFO` and `LOGGER=DEBUG`.
   - Mention that credentials and tokens are not logged.
   - Include the offline test command.
   - Keep safety language clear: this package is for legitimate browser
     compatibility testing and test-data generation, not evasion or abuse.

Testing requirements:

- Add or update tests for channel version map behavior.
- Add or update tests for timing metadata and failure timing.
- Add or update tests for Keyval safe URL construction.
- Add or update tests for public KeyVal URL shapes.
- Add or update tests for chunk URL generation.
- Add or update tests for logger configuration.
- Add or update tests for the verbose discovery service output.
- Keep all tests offline with fakes, mocks, or local fixtures.
- Do not require live Chrome for Testing calls or real Keyval credentials.

Raw example requirements:

- Update `raw/proxy/key_val_store_proxy/` if Keyval request or response shapes
  change.
- Update `raw/proxy/chrome_for_testing_version_proxy/` if Chrome for Testing
  request or response shapes change.
- Keep raw JSON valid.
- Use realistic but safe sample data.
- Do not include secrets or production request dumps.

Acceptance criteria:

- `latest()` and `random()` still work as the core public API.
- Channel-aware helpers work for Stable, Beta, Dev, and Canary.
- `random()` still avoids returning the exact same full user-agent twice in a
  row when alternatives exist.
- Service methods still call proxies for external APIs and repos for local
  state.
- Keyval values and URLs are logged safely.
- `LOGGER=DEBUG` provides useful operational detail.
- `LOGGER=INFO python testUserAgentPool.py` gives a compact readable run.
- README reflects the current API and example workflow.
- The test suite passes with:

```bash
python -m unittest discover -s test -p "test_*.py"
```
