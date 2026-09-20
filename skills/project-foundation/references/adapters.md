# Technical adapters

## Selection rule

Choose the least operationally demanding adapter that satisfies the approved first release. Do not choose a stack because it is fashionable or because one earlier project used it.

If no adapter is suitable, select `docs-only`. The universal foundation may be ready while technical setup remains unverified.

## TypeScript/Node

Suitable for Web applications, APIs, and internal tools when a JavaScript/TypeScript ecosystem materially reduces delivery and maintenance cost.

Provides a pinned Node major version, npm lockfile, TypeScript configuration, minimal source/test layout, `check`, `test`, `build`, and `verify` scripts. It also provides a Node version classifier; with `github` and `release`, GitHub CI and automatic version preparation are generated.

Cloudflare is an optional deployment profile. Do not generate Cloudflare bindings, resources, account identifiers, or deployment workflows during local project start.

## Python

Suitable for automation, data processing, scheduled tasks, and simple services where Python libraries or readable scripts are the main advantage.

Provides a pinned Python major/minor line, `pyproject.toml`, src layout, standard-library tests, syntax/import checks, and a Python version classifier. With `github` and `release`, GitHub CI and automatic version preparation are generated. A no-dependency starter does not fabricate a lockfile; the first external dependency triggers a documented lock strategy.

## Codex Skill

Suitable when the output is a reusable Codex workflow rather than an application.

Provides `SKILL.md`, `agents/openai.yaml`, `VERSION`, focused supporting-resource directories, a Python version classifier, and a quick-validation entry. Generated instructions remain a bounded starting point; they do not invent domain methodology.

## Version automation evidence

Executable automation is verified only for the matching supported adapter. `docs-only` and unsupported stacks receive the changelog taxonomy and release contract as documented follow-ups; they must not be described as automatically versioned.

## Adapter evidence

An adapter is marked verified only after a generated temporary project passes its declared local commands. Missing runtimes or network access produce `unverified`, not success.
