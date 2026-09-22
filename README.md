<div align="right">

**English** | [简体中文](README.zh-CN.md)

</div>

# Project Craft

**A collection of agent skills for turning an uncertain idea into a well-framed, well-structured, and continuously maintainable project.**

Project Craft separates five kinds of work that are often mixed together: defining the problem, designing the system, preparing the engineering foundation, preserving project continuity, and keeping execution aligned with the real goal. Each skill can be installed and used independently.

## Skills

| Skill | Responsibility | Use it when |
| --- | --- | --- |
| [`project-framing`](skills/project-framing/SKILL.md) | Clarify outcomes, form a genuinely feasible direction set, and choose the next useful move | The idea or request is still ambiguous. |
| [`system-architecture`](skills/system-architecture/SKILL.md) | Design responsibilities, boundaries, information flow, operating feedback, and lifecycle | A system or subsystem needs a coherent structure that can evolve. |
| [`project-foundation`](skills/project-foundation/SKILL.md) | Prepare a verifiable foundation before long-term software development begins | An empty or early repository needs durable engineering conventions. |
| [`project-continuity`](skills/project-continuity/SKILL.md) | Carry project meetings and decisions into the effective design, work queue, and discoverable project context | An existing project needs sustained discussion, change coordination, or context maintenance with Codex. |
| [`goal-discipline`](skills/goal-discipline/SKILL.md) | Keep work on the actual task and suppress completeness-driven expansion | Adjacent questions, process, or visible activity risk being mistaken for the task. |

These are not five mandatory stages. A mature project may need only continuity; an experimental subsystem may need architecture without a new foundation. The collection is organized by decision boundary, not by ceremony.

## Install

Using the Skills CLI:

```bash
npx skills add hunterhigh/project-craft
```

To install manually, copy any complete directory under [`skills/`](skills/) into your personal or project-level Skills directory. Keep each directory intact: some skills include references, scripts, assets, tests, or version files.

## Use

```text
Use $project-framing to turn this idea into a genuinely feasible, testable project direction.
Use $system-architecture to define responsibilities, feedback loops, and lifecycle conditions.
Use $project-foundation to prepare this repository before product code is written.
Use $project-continuity to continue our project meeting from the most important current issue.
Use $goal-discipline to prevent completeness-driven expansion and stop when the requested result is complete.
```

## Design principles

- **Distinct responsibilities.** Framing, architecture, foundation, continuity, and execution discipline remain separate so each can be invoked for the job it actually owns.
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
