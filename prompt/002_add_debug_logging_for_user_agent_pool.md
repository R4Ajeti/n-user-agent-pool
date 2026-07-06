Add debug logging for the Chrome user-agent pool package.

Goal:

When running a script such as:

```bash
LOGGER=DEBUG python testUserAgentPool.py
```

the package should print useful DEBUG logs that explain what is happening inside
the user-agent generation flow.

Logging requirements:

1. Keep normal package usage quiet by default.
2. Enable verbose logs when `LOGGER=DEBUG` is set.
3. Log the public service operation being called:
   - `latest`
   - `random`
   - `latestByChannel`
   - `latestVersion`
   - `channelVersionMap`
4. Log Chrome for Testing version fetch behavior:
   - source endpoint
   - number of raw versions found
   - number of valid versions kept
   - newest version selected
   - channel version map when available
5. Log user-agent generation behavior:
   - number of Chrome versions used
   - number of desktop platform fragments used
   - number of generated user agents
   - whether invalid versions or invalid user agents were skipped
6. Log random selection behavior:
   - candidate pool size
   - last random user-agent status
   - whether the previous full user-agent was excluded
   - selected desktop platform family
   - selected Chrome version
7. Log Keyval behavior:
   - whether Keyval is configured
   - descriptive Keyval key being read or written
   - hashed Keyval key used in the URL
   - whether the value was found, missed, saved, or skipped
   - value type and safe byte counts
8. Log fallback behavior:
   - remote Chrome for Testing failure
   - fallback to cached Keyval user-agent list
   - fallback to in-memory repo state
   - no-cache failure case
9. Log timing:
   - operation name
   - duration in milliseconds
   - success/failure
   - error type on failure

Safety requirements:

- Do not log `KEY_VAL_AUTH_TOKEN`.
- Do not log API keys, secrets, cookies, private keys, or credentials.
- Do not log full provider secrets in URLs.
- It is safe to log public Chrome for Testing URLs.
- It is safe to log descriptive Keyval keys and their hashed keys.
- It is safe to log generated public user-agent strings in example scripts, but
  internal package logs should prefer counts, selected Chrome version, and
  selected platform family.

README requirements:

- Document how to enable debug logs with `LOGGER=DEBUG`.
- Show example command:

```bash
LOGGER=DEBUG python testUserAgentPool.py
```

- Mention that logs are quiet unless `LOGGER` is set.
- Explain that tokens and credentials are not logged.

Testing requirements:

- Add tests that verify `LOGGER=DEBUG` configures the project logger.
- Add tests or safe checks for Keyval logging behavior without real credentials
  or live Keyval calls.
- Keep tests offline and credential-free.
