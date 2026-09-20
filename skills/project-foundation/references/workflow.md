# Start and stage workflow

## New-project start

### Capture the idea

Restate the idea as facts, assumptions, owner decisions, and technical decisions. Confirm that the target is a new long-term project rather than a one-off task or an arbitrary existing repository.

### Ask only consequential questions

Cover these decision areas, stopping when additional answers would not change the route:

1. Who will use it and what job must become easier?
2. What must the first usable release do, and what is explicitly excluded?
3. What observable outcome would count as success?
4. What information is stored, and what happens if it is lost, duplicated, exposed, or wrong?
5. Will real users, payments, personal data, scheduled jobs, or external writes exist?
6. Will it be local, occasionally run, scheduled, or continuously online?
7. How many people maintain it, and how long should it live?
8. What cost, outage, or vendor limits would be unacceptable?

Ask in business language. For example, ask whether real users can safely experience a bad release before asking about staging.

### Build the recommendation card

Show:

- project type, user shape, run shape, collaboration shape, stage, and risk level;
- recommended route and one meaningful alternative;
- selected modules and why each is needed;
- now/internal-use/production/later horizons;
- controls intentionally omitted;
- assumptions and their review stages.

### Obtain the start contract

The owner approves the problem and users, first-release scope and exclusions, success criteria, technical route, risk level, selected modules, assumptions, and accepted risk.

Approval authorizes local generation only. It does not authorize GitHub, cloud, secrets, purchases, deployment, or production data access.

## Stage advancement

Supported target stages are `prototype`, `internal`, `production`, and `critical`.

Compare manifest state with the target stage:

1. Identify new users, data, writes, dependencies, costs, and outage consequences.
2. Add only newly triggered modules.
3. Preserve decisions that remain valid.
4. Move assumptions whose review stage has arrived into blocking decisions.
5. Produce a delta report before modifying shared files.

## Interaction rules

- Recommend rather than presenting a wall of equal choices.
- Define a technical term on first use.
- Let the owner ask for explanation, alternatives, or a lighter safe route.
- Record accepted risk; do not repeatedly relitigate it before its review stage.
- Do not show raw validation logs first. Lead with status, consequences, and the next action.
