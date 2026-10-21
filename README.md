<div align="right">

**English** | [简体中文](README.zh-CN.md)

</div>

# Project Craft

**A collection of agent skills for turning an uncertain idea into a well-framed, well-structured, and continuously maintainable project.**

Project Craft separates four kinds of work that are often mixed together: defining the problem, designing the system, preparing the engineering foundation, and preserving project continuity. Each skill can be installed and used independently. Everyday technical responsibility belongs in working agreements, not a mandatory per-turn skill.

## Skills

| Skill | Responsibility | Use it when |
| --- | --- | --- |
| [`project-framing`](skills/project-framing/SKILL.md) | Clarify outcomes, form a genuinely feasible direction set, and choose the next useful move | The idea or request is still ambiguous. |
| [`system-architecture`](skills/system-architecture/SKILL.md) | Design responsibilities, boundaries, information flow, operating feedback, and lifecycle | A system or subsystem needs a coherent structure that can evolve. |
| [`project-foundation`](skills/project-foundation/SKILL.md) | Prepare a verifiable foundation before long-term software development begins | An empty or early repository needs durable engineering conventions. |
| [`project-continuity`](skills/project-continuity/SKILL.md) | Recover valid state, propagate confirmed changes, and preserve necessary resumption points | An existing project needs resumption, handoff, or a confirmed change carried into subsequent work—not ordinary discussion or execution. |

These are not mandatory stages. An experimental subsystem may need architecture without a new foundation; routine work may need none of these skills. The collection is organized by decision boundary, not by ceremony.

[`goal-discipline`](skills/goal-discipline/SKILL.md) is retained as legacy source, but is no longer recommended for default installation or per-turn invocation.

## Install

Using the Skills CLI:

```bash
npx skills add hunterhigh/project-craft
```

Select the skills you need from the four above; do not include the legacy skill by default. To install manually, copy the selected complete directories under [`skills/`](skills/) into your personal or project-level Skills directory. Keep each directory intact: some skills include references, scripts, assets, tests, or version files.

## Use

```text
Use $project-framing to turn this idea into a genuinely feasible, testable project direction.
Use $system-architecture to define responsibilities, feedback loops, and lifecycle conditions.
Use $project-foundation to prepare this repository before product code is written.
Use $project-continuity to resume this project from its verified state and remaining authorized work.
```

[`AGENTS.example.md`](AGENTS.example.md) is an optional working-agreement template covering technical ownership, end-to-end delivery, decision boundaries, corrections, and narrow continuity triggers. Review and merge applicable clauses into your existing agreements; do not overwrite permission or project rules. Skill installation does not install this template. It does not require per-turn naming, goal checks, or new management documents.

## Design principles

- **Distinct responsibilities.** Framing, architecture, foundation, and continuity remain separate so each can be invoked for the job it actually owns. Continuity is not a permanent management layer.
- **Real-world boundaries.** The skills account for people, evidence, operating constraints, and changing conditions—not only idealized technical structure.
- **Composable, not procedural.** Skills can cooperate without creating a compulsory multi-step workflow.
- **Artifacts only when useful.** Documents, plans, tests, and delegation must contribute to an observable outcome rather than merely display process.
- **Portable packages.** Every skill is maintained as a self-contained directory with explicit entry points and dependencies.

## Repository structure

```text
skills/
├── goal-discipline/
├── project-continuity/
├── project-foundation/
├── project-framing/
└── system-architecture/
```

## Validation

Validate an individual skill with the official skill validator:

```bash
python /path/to/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

`project-foundation` also includes executable tests:

```bash
python -m unittest discover -s skills/project-foundation/tests -v
```

`project-foundation` is currently versioned at `0.2.0`. Other skills are maintained from this repository as independently installable packages.
