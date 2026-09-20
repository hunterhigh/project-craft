---
name: project-foundation
description: Prepare a new long-term software project before product code is written by clarifying intent, classifying operational risk, recommending a maintainable stack, and generating a verified local foundation. Use for new web apps, internal tools, APIs, automations, data projects, or Codex Skills, and for stage checks on projects previously initialized by this skill. Do not use for one-off code edits, ordinary feature work, or retrofitting unrelated existing repositories.
---

# Project Foundation

Turn a nontechnical owner's project idea into an approved, locally verified project foundation. Preserve the owner's decision authority while taking responsibility for technical recommendations.

## Modes

- **Start**: prepare a new project in an empty directory.
- **Check**: verify a project already containing `.project-start/manifest.json`.
- **Advance**: reassess an initialized project before internal use, production, or critical-infrastructure status.
- **Explain**: translate the current manifest and verification state into plain language without changing files.

Do not treat an arbitrary existing repository as initialized. A retrofit/audit workflow is outside this version.

## Decision process

### 1. Understand

Establish the user, problem, first-release boundary, success criteria, expected lifetime, data, external systems, runtime, collaboration, cost, and failure consequences.

- Ask one decision-changing question at a time.
- Use business consequences instead of unexplained technical terminology.
- Separate facts, assumptions, owner decisions, and technical decisions.
- Allow "I don't know"; record consequential unknowns instead of treating them as low risk.

For a new project, read [workflow.md](references/workflow.md) and [risk-and-modules.md](references/risk-and-modules.md).

### 2. Decide

Classify the project and recommend one maintainable route plus at most one meaningful alternative. Explain cost, maintenance, important tradeoffs, and why each selected foundation module is needed now.

- Read [profiles.md](references/profiles.md) only for profiles the project triggers.
- Read [adapters.md](references/adapters.md) when selecting a supported technical adapter.
- A single high-consequence risk dimension raises the risk level; never average it away.
- Put requirements into four horizons: now, before internal use, before production, and later trigger.
- List intentionally omitted controls so omission is explicit rather than accidental.

Present a short start contract covering what is being built, for whom, first-release scope, exclusions, route, selected modules, and unresolved assumptions. Do not write product code or generate the project until the owner approves this contract.

### 3. Generate

After approval, create a schema-v1 manifest outside the empty target directory. Read [manifest.md](references/manifest.md) and [output-contract.md](references/output-contract.md).

Validate before generation:

```text
python <skill-dir>/scripts/foundation.py validate-manifest --manifest <manifest.json>
```

Generate transactionally:

```text
python <skill-dir>/scripts/foundation.py generate --manifest <manifest.json> --target <empty-project-directory>
```

For a supported technical adapter, include `--run-tools` when its runtime is available. Without real adapter execution, generation correctly remains **Not ready**. For `docs-only`, an unverified technical setup is an explicit follow-up rather than a false success.

The generator may create local files only. Creating repositories, changing GitHub settings, provisioning services, setting secrets, or deploying requires a later explicit owner request.

### 4. Verify

Run deterministic verification and report its actual result:

```text
python <skill-dir>/scripts/foundation.py verify --target <project-directory>
python <skill-dir>/scripts/foundation.py status --target <project-directory>
```

Add `--run-tools` to `verify` when the project uses a supported technical adapter and its runtime is available. Never infer success from plausible-looking files or downgrade a failing check.

Return one of:

- **Ready to build**: current development-stage requirements passed.
- **Ready with recorded follow-ups**: current stage passed; named later-stage items remain.
- **Not ready**: a current-stage requirement failed or remains unresolved.

"Ready to build" does not mean ready for production.

## Safety invariants

- Generate only into an empty directory; update only a project initialized by this skill.
- Never silently overwrite a user-modified file.
- Never place real secrets, tokens, account IDs, customer data, or production exports in generated files.
- Treat code rollback and data restoration as separate decisions.
- For deployable releases, prepare a higher semantic version before non-production verification; production success must create immutable version evidence, while failure must not consume the tag.
- A production database triggers backup and recovery evaluation.
- Scheduled external writes trigger stop controls and idempotency evaluation.
- Real users trigger identity, permissions, privacy, and isolated test-data evaluation.
- Unsupported stacks receive the universal foundation only and remain technically unverified.
- Preserve explicit user choices and record accepted risk with a review stage.

## Stage changes

For **Advance**, compare the current and target stages rather than rebuilding the project. Explain new risks, required modules, retained decisions, and blocking items. Do not provision or deploy unless the user separately requests those external actions.

For **Check** or **Explain**, do not reopen product discovery unless the manifest is internally contradictory or the user reports a material change.
