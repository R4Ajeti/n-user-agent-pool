---
name: maintain-readme
description: Create, simplify, modernize, review, and maintain project README files using clear reader-first structure and verified repository facts. Use when a README is requested or when code, public APIs, installation, commands, configuration, environment variables, dependencies, integrations, compatibility, diagnostics, security behavior, or architecture changes may require README updates. Evaluate documentation impact after every implementation change and update the README only when reader-facing information changed.
---

# Maintain README

## Goal

Keep the README simple, current, easy to scan, and accurate enough that a new user can understand the project and run its main workflow without reading the source code.

Treat “modern” as clear structure, concise language, copyable examples, and low maintenance cost. Do not treat it as decorative badges, excessive icons, or marketing language.

## Read Before Writing

Inspect the repository instead of relying on memory. Read the files that define the documentation contract, including:

- `AGENTS.md` and other repository instructions
- the current `README.md`
- package or application metadata such as `pyproject.toml`, `package.json`, or equivalent
- public exports and entry points
- configuration and environment-variable definitions
- representative examples
- test and build configuration
- license files
- the current diff when maintaining documentation after a change

Follow repository-specific README requirements over this general guidance. Honor any instruction to update only one file.

Never document planned behavior as if it already exists. Verify every command, import path, option, default, version requirement, and feature claim from code or tests.

## Run the Documentation-Impact Check

After every implementation change, decide whether the README needs an update.

Update it when the change affects something a user, integrator, contributor, or operator needs to know:

- project purpose, scope, or limitations
- installation or supported runtime versions
- required or optional dependencies
- public classes, methods, functions, CLI commands, or return values
- default behavior, fallback behavior, errors, or important edge cases
- environment variables, configuration keys, defaults, or secrets handling
- external integrations or provider setup
- logging, diagnostics, monitoring, or troubleshooting commands
- architecture that contributors must follow
- test, build, release, or local-development commands
- security, privacy, safety, or credential expectations
- repository URLs, package names, licensing, or support links

Usually leave it unchanged for:

- internal refactors with identical observable behavior
- test-only changes that do not establish a new supported contract
- formatting, comments, or type-only maintenance
- private implementation details readers do not need

When an update is needed, edit the smallest relevant section and remove any now-stale statement nearby. Do not append a duplicate section merely because it is easier.

When no update is needed, do not touch the README just to create documentation churn.

## Use a Reader-First Order

Prefer this reading path, adapting or omitting sections that do not help the project:

1. Project name and one-sentence value statement
2. Quick start
3. Installation
4. Core usage or public API
5. Configuration and optional integrations
6. Important behavior, limitations, or security notes
7. Diagnostics and troubleshooting
8. Testing and development
9. Architecture or contributor guidance
10. License and support links

Put the shortest successful path near the top. Move contributor details and internal architecture below user-facing usage.

Do not add empty sections, a table of contents for a short README, or every conventional heading by default.

## Write for Fast Understanding

Use plain, direct language.

- Open with what the project does, who it helps, and its most important constraint.
- Use short paragraphs with one idea each.
- Prefer active voice and concrete verbs.
- Define necessary domain terms once.
- Keep headings descriptive and consistent.
- Use bullets for short sets and tables for repeated mappings such as options or environment variables.
- Use fenced code blocks with the correct language tag.
- Make commands copyable from the documented working directory.
- Show the smallest useful example before advanced variants.
- Explain what an example returns or changes when that is not obvious.
- Keep warnings close to the step they affect.
- Link to authoritative detail instead of copying large external documents.

Avoid:

- hype, vague claims, and filler such as “powerful,” “seamless,” or “revolutionary”
- long walls of text
- repeating the same setup or example in several sections
- exposing internal implementation before explaining basic use
- unexplained acronyms and project-specific jargon
- decorative emoji, badge walls, or screenshots that will quickly become stale
- manual “last updated” dates that create maintenance work without proving accuracy
- generated output or version numbers that will become misleading unless they are part of the contract

## Keep the Quick Start Minimal

Make the quick start prove the main value with the fewest steps possible.

Include only:

1. the shortest supported installation command when installation is required
2. the canonical public import or command
3. one main operation
4. a brief explanation or compact stable output example

Move advanced filtering, alternate providers, persistence, debugging, and contributor setup into later sections.

Use examples that are safe to copy. Replace credentials and private endpoints with obvious placeholders.

## Document APIs and Configuration Precisely

Use public names exactly as implemented, including capitalization. Prefer examples over exhaustive prose for small APIs. Use a compact table when several parameters or options share the same fields.

For public behavior, document:

- accepted inputs when they are not self-evident
- return shape
- defaults that materially affect results
- important errors or fallback behavior
- state or external side effects

For configuration, document only supported settings. Include the name, purpose, requirement status, safe default, and secret status when useful.

Never include real credentials, tokens, cookies, private URLs, or production data. State how secrets are supplied and whether they may appear in logs or persisted state.

## Keep Commands and Examples True

Cross-check README content against the repository:

- installation commands against package metadata and repository URLs
- imports against actual public exports
- API examples against current signatures
- environment variables against constants and runtime lookups
- defaults against code rather than assumptions
- test and build commands against the current tool configuration
- supported runtime versions against package metadata and CI when present
- license text against the license file

Run documented commands when practical and safe. Use offline tests or mocked workflows when live providers, credentials, cost, or production state would otherwise be required.

Do not claim a command was verified if it was not run. If an output is variable, describe its shape or label it as an example rather than promising the exact value.

## Simplify an Existing README Carefully

Preserve required facts while reducing cognitive load.

1. Identify the primary audience and first successful task.
2. Find duplicated, stale, overly internal, or misplaced content.
3. Move the quick path upward.
4. Merge overlapping sections.
5. Convert repeated option descriptions into a compact table when clearer.
6. Shorten sentences without removing behavioral guarantees or safety notes.
7. Keep advanced details only when readers need them to operate or contribute.
8. Verify links, commands, examples, and claims after restructuring.

Do not remove important fallback, security, compatibility, or credential guidance merely to make the file shorter.

## Keep the README Current During Changes

At the end of an implementation task:

1. Review the diff for user-facing changes.
2. Map each affected contract to an existing README section.
3. Update the relevant text, command, code example, option table, or warning.
4. Search the whole README for old names and contradictory statements.
5. Check nearby examples that depend on the changed behavior.
6. Keep terminology consistent with code and package metadata.
7. Mention in the final handoff whether the README was updated or did not need an update when that information is useful.

Do not use the README as a changelog. Describe the current supported state, not the sequence of edits that produced it.

## Review the Result

Before completing README work, verify:

- a new reader understands the project from the opening paragraph
- the quick start reaches the main value with minimal steps
- installation, imports, commands, APIs, options, and defaults match the repository
- user-facing changes from the current diff are documented where needed
- stale or contradictory statements were removed
- headings form a clear scan path
- examples are concise, copyable, and credential-free
- advanced details do not bury basic use
- security and limitation notes remain clear
- Markdown renders cleanly and links resolve
- the README contains no secret, private data, or unsupported promise
