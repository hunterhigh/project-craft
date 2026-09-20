# Project profiles

Read only the profiles triggered by the project.

## Internal multi-user system

Evaluate roles and permissions, administrator actions, audit history, data import/export/correction, joining and leaving staff, concurrent edits, backup/recovery, status visibility, confirmation for consequential actions, and maintainer handoff.

Default additions: `auth`, `data-lifecycle`, `security`, `environments`, `release`, `operations`, and `backup-recovery` when data is important.

## Consumer Web product

Evaluate registration, account recovery, privacy and deletion, abuse and rate limits, browser/device coverage, peak load, understandable error states, analytics consent, feedback/support, rollback, and third-party identity/payment/notification failures.

Default additions: `auth`, `security`, `accessibility`, `data-lifecycle`, `environments`, `release`, `operations`, and `cost-capacity`.

## Automation or data system

Evaluate idempotency, checkpoint/resume, duplicate writes, source provenance and freshness, external limits, stop controls, failure history, retry policy, manual correction, and data-quality assertions.

Default additions when unattended: `scheduled-jobs`, `external-api` as applicable, `operations`, and `cost-capacity`.

## Public API

Evaluate contract, authentication, authorization, rate limits, idempotency, compatibility, deprecation, error semantics, consumer migration, and observable dependency failures.

Default additions: `public-api`, `security`, `release`, `operations`, `cost-capacity`, and `environments`.

## AI-enabled product

Evaluate model/provider version, representative evaluations, prompt and policy changes, unsafe or incorrect output, human review, data handling, spend limits, provider failure, and reproducible comparison between versions.

Default addition: `ai`; also enable `data-lifecycle`, `security`, or `cost-capacity` when their triggers apply.

## Payment flow

Evaluate provider-hosted versus self-handled payment data, sandbox isolation, webhook authenticity and duplicate delivery, order/payment state reconciliation, refunds and disputes, receipts, provider outage, support access, and financial records. Add `payments`; never use real charges as development or automated-test fixtures.

## Multi-tenant product

Evaluate tenant identity, membership and administrator boundaries, per-tenant data access, support impersonation, exports/deletion, noisy-neighbor capacity, tenant-aware logs, and migration safety. Add `multi-tenant`; isolation must exist in authorization and tests rather than only in screen filters.

## Mobile application

Evaluate app-store review and signing ownership, supported OS/app versions, offline and interrupted work, deep links and notifications, permissions, device storage, accessibility, observability, API compatibility with old clients, and an update path when an installed release cannot be instantly rolled back. Add `mobile`; use `docs-only` if no verified mobile adapter fits.

## Codex Skill

Evaluate the exact trigger boundary, the reusable decision process, progressive disclosure, instruction versus deterministic script responsibilities, supporting resources, observable validation, realistic prompts, and version compatibility.

Do not create domain rules before the owner approves the Skill's intended job and boundaries.
