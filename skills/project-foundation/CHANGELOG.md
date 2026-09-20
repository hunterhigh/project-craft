# Changelog

All notable changes to Project Foundation follow Semantic Versioning.

## Unreleased

## [0.2.0] - 2026-09-03

### Added

- Deterministic patch, minor, and major classification from categorized Unreleased notes.
- Version tools for generated TypeScript/Node, Python, and Codex Skill projects.
- GitHub workflow templates that prepare a version commit after successful main CI and fall back to a release pull request under branch protection.
- Production stage gates requiring a new version before non-production verification and immutable tag/Release evidence after successful promotion.

### Changed

- Generated changelogs, release guidance, Agent rules, and adapter verification now enforce version-before-staging ordering.
- Unsupported and docs-only adapters report documented versioning without claiming executable automation.

## [0.1.0] - 2026-09-03

### Added

- Initial four-phase project-foundation workflow.
- Adaptive intake, risk classification, project profiles, and stage gates.
- Transactional local generator and verifier contract.
- TypeScript/Node, Python, and Codex Skill adapters with real temporary-project verification.
- Conditional GitHub, environment, release, operations, payment, multi-tenant, mobile, and product-profile rules.
- Machine-readable manifest, file ownership, drift detection, secret scanning, and plain-language readiness reporting.
