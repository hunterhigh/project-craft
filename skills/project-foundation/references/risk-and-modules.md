# Risk and module selection

## Risk levels

### Low

Local or disposable work using synthetic data, without real users, payments, sensitive information, scheduled external writes, or meaningful outage consequences.

### Standard

A long-lived project with persistent data, external APIs, continuous operation, internal users, or meaningful maintenance and recovery needs.

### Critical

Sensitive data, payments, irreversible automation, high-impact access, regulatory exposure, or a company process that cannot operate safely without the system.

A single critical dimension makes the project critical. Unknown consequential dimensions stay unresolved and may block the stage that depends on them.

## Universal modules

Every long-term project enables:

- `project-brief`
- `decisions`
- `git`
- `versioning`
- `stage-gates`
- `testing`
- `secrets`
- `continuity`

`versioning` classifies explicit changelog categories: Breaking/重大迭代/不兼容变更 is major, Added/新增 is minor, and Fixed/Maintenance/Security/修复/维护/优化/安全与运维 is patch. Mixed releases take the highest impact; major is never inferred from commit size.

## Conditional modules

| Module | Trigger | Required companion |
|---|---|---|
| `github` | Remote source of truth or collaboration | `git`, `testing` |
| `environments` | Real users, persistent production data, external writes, scheduled work, or important uptime | `testing`, `secrets` |
| `release` | Deployable or distributable versions | `versioning`, `testing` |
| `database` | Persistent structured data | `data-lifecycle`; `backup-recovery` before production |
| `data-lifecycle` | Personal, customer, business, logged, backed-up, or retained data | `secrets` when access is restricted |
| `backup-recovery` | Important persistent data | `operations` before production |
| `external-api` | Third-party reads/writes or paid calls | `cost-capacity` |
| `scheduled-jobs` | Timed or unattended execution | `operations`; evaluate idempotency and stop control |
| `auth` | Real identities or different permissions | `data-lifecycle`, `security` |
| `security` | Network exposure, identity, sensitive data, payment, or high-impact operations | `testing` |
| `operations` | Scheduled or continuously running system | `release` before production |
| `cost-capacity` | Metered service, meaningful traffic, quota, or vendor limit | none |
| `accessibility` | Public or employee-facing Web UI | `testing` |
| `public-api` | External API consumers | `release`, `security` |
| `ai` | Model-generated output or model/vendor dependency | `cost-capacity`; `data-lifecycle` as applicable |
| `open-source` | Public code or distributed package | `github`, `release`, license decision |
| `payments` | Charges, refunds, stored payment references, or financial reconciliation | `external-api`, `security`, `data-lifecycle`, `operations` |
| `multi-tenant` | One service stores or processes data for separate customer organizations | `auth`, `data-lifecycle`, `security`; prove isolation in tests |
| `mobile` | An installed mobile app with delayed client updates or app-store distribution | `release`, `testing`; define supported versions and compatibility |

## Stage horizons

### Now

Only what is necessary to begin development safely: scope, decisions, Git, secrets boundary, toolchain, minimum checks, and the next stage's triggers.

### Before internal use

Real identity boundaries, isolated test data, observable failures, basic recovery, user feedback, and internal-use acceptance.

### Before production

A candidate version higher than the latest production release, verification of that exact commit outside production, production configuration, backup/recovery validation, health and failure detection, cost boundaries, rollback, smoke checks, and immutable tag/Release evidence after success. A failed promotion must not create the tag.

### Before critical status

Recovery drills, permission audit, capacity and degradation, incident handling, access recovery, and handoff.

## Minimality test

For every selected module, state:

1. What concrete failure does it prevent?
2. Why is it needed at this stage?
3. What is the latest safe stage to defer it to?
4. What understanding and maintenance cost does it add?

Remove a module that cannot answer these questions.
