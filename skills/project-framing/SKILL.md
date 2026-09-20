---
name: project-framing
description: "Frame early-stage projects and unclear feature directions by clarifying the outcome, mapping the wider system, exploring meaningful alternatives and trade-offs, shaping a provisional scope and architecture, and identifying the best next move. Use for 0-to-0.1 project work, competing approaches, or requests to clarify requirements or architecture. Do not use for clear mechanical changes, routine fixes, factual questions, or work whose requirements and direction are already settled."
---

# Project Framing

Help move an early idea from 0 to 0.1: from vague intent to a coherent project frame that is clear enough to guide the next useful action.

This is an exploratory reasoning skill, not a design stage gate. Do not require approval, a design document, an implementation plan, task creation, or a commit. Do not block implementation merely because a formal design has not been produced.

## Working Principle

Adapt the depth of framing to uncertainty, impact, and reversibility. Start with the whole situation, then zoom into requirements or architecture only where a decision depends on them.

- Ask only questions whose answers could materially change the outcome, scope, architecture, or next action.
- If the available context is sufficient, state important assumptions and continue instead of asking ceremonial questions.
- Ask one high-leverage question at a time when each answer determines the next question. Otherwise, a small group of independent questions is acceptable.
- Distinguish known facts, working assumptions, choices, and unresolved unknowns when that distinction affects the recommendation.
- Inspect an existing project's files, documentation, and recent changes only when they could change the framing. Follow relevant existing patterns and avoid unrelated refactoring.

## Frame

Determine what change the user is actually trying to create before treating a proposed feature or implementation as the project itself.

Consider only what is relevant:

- the desired outcome and why it matters;
- the current state, target state, users, operators, or stakeholders;
- constraints, dependencies, and the surrounding product, technical, or operational system;
- whether the request is one coherent project or several coupled initiatives;
- which apparent requirements are facts and which are untested solution assumptions.

When the scope contains multiple subsystems, first show how they relate at the project level. Then identify a useful starting slice instead of immediately designing every subsystem.

## Explore

Surface genuinely different ways to approach the project when meaningful alternatives exist.

- Lead with the recommended direction and explain why it best serves the user's outcome.
- For each credible alternative, explain what it optimizes, what it gives up, its important assumptions, and how difficult it would be to reverse.
- Separate decisions that must be made now from decisions that can safely remain open.
- Do not manufacture a fixed number of options. If only one credible path exists, say so; if uncertainty is more important than choice, propose a way to learn instead.
- Remove features, abstractions, and process that do not yet serve the project's outcome.

## Shape

Turn the current understanding into a provisional project model. Include only the dimensions needed to make the project intelligible or actionable, such as:

- scope and deliberate non-scope;
- core use cases or operating scenarios;
- system boundaries and responsibilities;
- critical user, information, control, or data flows;
- major components, interfaces, and dependencies;
- consequential risks, assumptions, and validation needs;
- a smallest useful starting point.

This is a working frame, not a complete specification. Do not force every project into software architecture, or automatically add testing, error handling, milestones, and deliverables when they do not affect the current decision.

## Orient

Recommend the next action that creates the most useful progress or reduces the most important uncertainty. Depending on the situation, that may be implementation, a prototype, research, a focused experiment, an architectural decision, decomposition into a first subproject, or simply a concise synthesis.

Default to delivering the useful result in the conversation. Create a durable brief, specification, plan, diagram, or repository artifact only when the user requests it. Do not ask for approval as a procedural gate; ask for a choice only when different answers would lead to materially different work.

Framing is sufficient when the intended outcome, current direction, useful boundaries, main unknowns, and next action are clear enough for the user's purpose. Stop there rather than completing an imagined full design.

## Working With Skill Design

When the project being framed is itself a Codex skill, combine this skill with `skill-design-principles` without duplicating responsibilities:

- `project-framing` clarifies the user's job-to-be-done, surrounding context, possible directions, trade-offs, and desired starting point.
- `skill-design-principles` derives the skill's minimal decision process, MECE phases, abstraction boundaries, and pruning criteria.
- Use `skill-creator` only when the user wants the skill files created or changed; it governs packaging and validation rather than exploration.

## Avoid Process Substitution

Do not confuse evidence of process with progress toward the project. In particular, avoid mandatory checklists, generic option sets, repeated confirmation, exhaustive architecture, unsolicited documentation, or questions the user has already answered. Preserve uncertainty when it is real, but do not treat every uncertainty as a blocker.
