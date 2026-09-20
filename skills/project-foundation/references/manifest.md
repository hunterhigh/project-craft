# Manifest contract

The schema-v1 JSON manifest is the source of truth for deterministic generation. Use UTF-8 and do not include comments or secrets.

## Required top-level fields

- `schemaVersion`: integer `1`
- `foundationVersion`: the source package version
- `project`: identity, summary, problem, users, first release, exclusions, success criteria
- `classification`: product type, user shape, run shape, collaboration shape, stage, risk level, and risk dimensions
- `technology`: adapter and optional deployment profile
- `modules`: unique selected module identifiers
- `assumptions`: unresolved statements with review stages
- `decisions`: approved significant decisions
- `externalActions`: all false for local generation

The machine-readable schema lives at `manifest-schema.json` in this directory. Use `manifest-example.json` only as a shape example; never copy its project facts into a real manifest.

## Invariants

- `foundationVersion` must equal the installed package `VERSION`.
- The adapter is `docs-only`, `typescript-node`, `python`, or `codex-skill`.
- Stage is `idea`, `prototype`, `internal`, `production`, or `critical`.
- Risk is `low`, `standard`, or `critical`.
- Module dependencies in `risk-and-modules.md` must be satisfied.
- All external action flags are false during this version's generation.
- Each assumption names its latest review stage.
- Each decision includes context, choice, rationale, consequences, and review condition.
- User-provided text containing a possible secret must be removed or replaced before generation.
