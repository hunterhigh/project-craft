# Generated output contract

## Universal files

- `START-HERE.md`: one-page owner map and next action
- `AGENTS.md`: future agent working agreements
- `CHANGELOG.md`: versioned human change record
- `.gitignore`: secrets, dependencies, builds, caches, and local artifacts
- `docs/project/brief.md`: users, problem, first release, exclusions, success
- `docs/project/architecture.md`: approved route, boundaries, dependencies
- `docs/project/roadmap.md`: stage horizons and triggers
- `docs/project/stage-gates.md`: build/internal/production/critical requirements
- `docs/project/decisions/0001-initial-foundation.md`: initial significant decision
- `.project-start/manifest.json`: generation source of truth
- `.project-start/generated-files.json`: ownership and content hashes
- `.project-start/verification.json`: latest deterministic result

Generate `docs/project/operations.md`, `docs/project/release-process.md`, and `.env.example` only when selected modules require them.

Supported technical adapters also generate an executable version classifier. When both `github` and `release` are selected, generate a post-CI version workflow that:

- derives patch, minor, or major from categorized `Unreleased` entries;
- creates the version commit before non-production verification;
- prevents its own release commit from creating a loop;
- uses a dedicated least-privilege `VERSION_BOT_TOKEN`;
- falls back to a release pull request when branch protection rejects direct main updates.

Production integration must reject a candidate that is not higher than the latest formal tag, and success must create immutable tag/Release evidence. Generating this contract does not authorize remote configuration or deployment.

## Owner-first status

Lead with:

1. `Ready to build`, `Ready with recorded follow-ups`, or `Not ready`.
2. What is being built and what the first release excludes.
3. Protections already present.
4. Unverified or deferred items and their review stages.
5. The next natural-language task for Codex.

Detailed command output belongs in verification evidence, not at the top of the owner report.

## File ownership

- `system`: machine evidence that may be regenerated.
- `shared`: owner/agent documents that require a diff before update.
- `project`: product code and human decisions that are never overwritten automatically.

The generator records path, owner class, module, and SHA-256 for each generated file.

## Language

Human documents use the owner's language. Technical identifiers, filenames, commands, and stable enum values remain in English. Define technical terms the first time they appear.
