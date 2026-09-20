from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_VERSION = (SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip()

ADAPTERS = {"docs-only", "typescript-node", "python", "codex-skill"}
STAGES = {"idea", "prototype", "internal", "production", "critical"}
REVIEW_STAGES = {"prototype", "internal", "production", "critical"}
RISK_LEVELS = {"low", "standard", "critical"}
RISK_VALUES = {"none", "low", "standard", "critical", "unknown"}
PRODUCT_TYPES = {"web", "internal-tool", "api", "automation", "data", "mobile", "skill"}
USER_SHAPES = {"owner-only", "internal-multi-user", "business-customer", "consumer-public"}
RUN_SHAPES = {"local", "on-demand", "scheduled", "continuous"}
COLLABORATION_SHAPES = {"solo", "ai-assisted", "team", "company"}

UNIVERSAL_MODULES = {
    "project-brief",
    "decisions",
    "git",
    "versioning",
    "stage-gates",
    "testing",
    "secrets",
    "continuity",
}

ALLOWED_MODULES = UNIVERSAL_MODULES | {
    "github",
    "environments",
    "release",
    "database",
    "data-lifecycle",
    "backup-recovery",
    "external-api",
    "scheduled-jobs",
    "auth",
    "security",
    "operations",
    "cost-capacity",
    "accessibility",
    "public-api",
    "ai",
    "open-source",
    "payments",
    "multi-tenant",
    "mobile",
}

MODULE_DEPENDENCIES = {
    "github": {"git", "testing"},
    "environments": {"testing", "secrets"},
    "release": {"versioning", "testing"},
    "database": {"data-lifecycle"},
    "backup-recovery": {"operations"},
    "external-api": {"cost-capacity"},
    "scheduled-jobs": {"operations"},
    "auth": {"data-lifecycle", "security"},
    "security": {"testing"},
    "operations": {"release"},
    "accessibility": {"testing"},
    "public-api": {"release", "security"},
    "ai": {"cost-capacity"},
    "open-source": {"github", "release"},
    "payments": {"external-api", "security", "data-lifecycle", "operations"},
    "multi-tenant": {"auth", "data-lifecycle", "security"},
    "mobile": {"release", "testing"},
}

MODULE_TITLES_ZH = {
    "project-brief": "项目范围",
    "decisions": "重要决定记录",
    "git": "Git 变更历史",
    "github": "GitHub 协作",
    "versioning": "版本管理",
    "stage-gates": "阶段门",
    "testing": "最低自动验证",
    "secrets": "敏感配置保护",
    "continuity": "交接与退出",
    "environments": "环境隔离",
    "release": "发布与回退",
    "database": "数据库变更",
    "data-lifecycle": "数据生命周期",
    "backup-recovery": "备份与恢复",
    "external-api": "外部 API",
    "scheduled-jobs": "定时任务",
    "auth": "身份与权限",
    "security": "安全基线",
    "operations": "长期运行",
    "cost-capacity": "成本与容量",
    "accessibility": "无障碍",
    "public-api": "公共 API 契约",
    "ai": "AI 评测与供应商风险",
    "open-source": "开源发布",
    "payments": "支付与对账",
    "multi-tenant": "多租户隔离",
    "mobile": "移动应用发布",
}

MODULE_TITLES_EN = {module: module.replace("-", " ").title() for module in ALLOWED_MODULES}

SECRET_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
]

PLACEHOLDER_PATTERN = re.compile(r"(?i)\b(?:TODO|TBD|FIXME)\b|\{\{|\}\}|<insert\b|\[placeholder\]")
GITHUB_EXPRESSION_PATTERN = re.compile(r"\$\{\{.*?\}\}")


class FoundationError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileSpec:
    content: str
    owner: str
    module: str


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FoundationError(f"FILE_NOT_FOUND: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FoundationError(f"INVALID_JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FoundationError(f"JSON_ROOT_MUST_BE_OBJECT: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def contains_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.search(GITHUB_EXPRESSION_PATTERN.sub("", text)))


def _require_string(errors: list[str], obj: Any, key: str, path: str) -> None:
    if not isinstance(obj, dict) or not isinstance(obj.get(key), str) or not obj[key].strip():
        errors.append(f"{path}.{key} must be a non-empty string")


def _require_string_list(errors: list[str], obj: Any, key: str, path: str, *, minimum: int = 0) -> None:
    value = obj.get(key) if isinstance(obj, dict) else None
    if not isinstance(value, list) or len(value) < minimum or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path}.{key} must be a string list with at least {minimum} item(s)")


def _require_exact_keys(errors: list[str], obj: Any, expected: set[str], path: str) -> None:
    if not isinstance(obj, dict):
        return
    missing = expected - set(obj)
    extra = set(obj) - expected
    if missing:
        errors.append(f"{path} is missing keys {sorted(missing)}")
    if extra:
        errors.append(f"{path} contains unsupported keys {sorted(extra)}")


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require_exact_keys(
        errors,
        manifest,
        {"schemaVersion", "foundationVersion", "language", "project", "classification", "technology", "modules", "assumptions", "decisions", "externalActions"},
        "manifest",
    )
    if manifest.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if manifest.get("foundationVersion") != FOUNDATION_VERSION:
        errors.append(f"foundationVersion must equal installed version {FOUNDATION_VERSION}")
    _require_string(errors, manifest, "language", "manifest")

    project = manifest.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        _require_exact_keys(errors, project, {"name", "slug", "summary", "problem", "users", "firstRelease", "notInScope", "successCriteria"}, "project")
        for key in ("name", "slug", "summary", "problem"):
            _require_string(errors, project, key, "project")
        if isinstance(project.get("slug"), str) and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project["slug"]):
            errors.append("project.slug must use lowercase kebab-case")
        _require_string_list(errors, project, "users", "project", minimum=1)
        _require_string_list(errors, project, "firstRelease", "project", minimum=1)
        _require_string_list(errors, project, "notInScope", "project")
        _require_string_list(errors, project, "successCriteria", "project", minimum=1)

    classification = manifest.get("classification")
    if not isinstance(classification, dict):
        errors.append("classification must be an object")
    else:
        _require_exact_keys(errors, classification, {"productType", "userShape", "runShape", "collaborationShape", "stage", "riskLevel", "riskDimensions"}, "classification")
        enums = {
            "productType": PRODUCT_TYPES,
            "userShape": USER_SHAPES,
            "runShape": RUN_SHAPES,
            "collaborationShape": COLLABORATION_SHAPES,
            "stage": STAGES,
            "riskLevel": RISK_LEVELS,
        }
        for key, allowed in enums.items():
            if classification.get(key) not in allowed:
                errors.append(f"classification.{key} must be one of {sorted(allowed)}")
        dimensions = classification.get("riskDimensions")
        dimension_names = {"data", "identity", "money", "privacy", "externalSystems", "automation", "businessDependency"}
        if not isinstance(dimensions, dict) or set(dimensions) != dimension_names:
            errors.append(f"classification.riskDimensions must contain exactly {sorted(dimension_names)}")
        else:
            for key, value in dimensions.items():
                if value not in RISK_VALUES:
                    errors.append(f"classification.riskDimensions.{key} must be one of {sorted(RISK_VALUES)}")
            if "critical" in dimensions.values() and classification.get("riskLevel") != "critical":
                errors.append("a critical risk dimension requires riskLevel critical")

    technology = manifest.get("technology")
    if not isinstance(technology, dict):
        errors.append("technology must be an object")
    else:
        _require_exact_keys(errors, technology, {"adapter", "deploymentProfile", "rationale"}, "technology")
        if technology.get("adapter") not in ADAPTERS:
            errors.append(f"technology.adapter must be one of {sorted(ADAPTERS)}")
        if technology.get("deploymentProfile", "none") not in {"none", "cloudflare", "generic"}:
            errors.append("technology.deploymentProfile must be none, cloudflare, or generic")
        _require_string(errors, technology, "rationale", "technology")

    modules_raw = manifest.get("modules")
    modules: set[str] = set()
    if not isinstance(modules_raw, list) or any(not isinstance(item, str) for item in modules_raw):
        errors.append("modules must be a string list")
    else:
        modules = set(modules_raw)
        if len(modules) != len(modules_raw):
            errors.append("modules must not contain duplicates")
        unknown = modules - ALLOWED_MODULES
        if unknown:
            errors.append(f"unknown modules: {sorted(unknown)}")
        missing_universal = UNIVERSAL_MODULES - modules
        if missing_universal:
            errors.append(f"missing universal modules: {sorted(missing_universal)}")
        for module, dependencies in MODULE_DEPENDENCIES.items():
            if module in modules and not dependencies.issubset(modules):
                errors.append(f"module {module} requires {sorted(dependencies - modules)}")

    if isinstance(classification, dict) and isinstance(classification.get("riskDimensions"), dict):
        dims = classification["riskDimensions"]
        stage = classification.get("stage")
        if dims.get("identity") in {"standard", "critical"} and "auth" not in modules:
            errors.append("standard or critical identity risk requires auth")
        if dims.get("privacy") in {"standard", "critical"} and not {"data-lifecycle", "security"}.issubset(modules):
            errors.append("standard or critical privacy risk requires data-lifecycle and security")
        if dims.get("externalSystems") in {"standard", "critical"} and "external-api" not in modules:
            errors.append("standard or critical external-system risk requires external-api")
        if dims.get("money") in {"standard", "critical"} and "payments" not in modules:
            errors.append("standard or critical money risk requires payments")
        if classification.get("runShape") == "scheduled" and "scheduled-jobs" not in modules:
            errors.append("scheduled run shape requires scheduled-jobs")
        if stage in {"production", "critical"} and not {"environments", "release", "operations"}.issubset(modules):
            errors.append("production or critical stage requires environments, release, and operations")
        if "database" in modules and stage in {"production", "critical"} and "backup-recovery" not in modules:
            errors.append("a production database requires backup-recovery")

    assumptions = manifest.get("assumptions")
    if not isinstance(assumptions, list):
        errors.append("assumptions must be a list")
    else:
        for index, assumption in enumerate(assumptions):
            if not isinstance(assumption, dict):
                errors.append(f"assumptions[{index}] must be an object")
                continue
            _require_exact_keys(errors, assumption, {"text", "reviewByStage"}, f"assumptions[{index}]")
            _require_string(errors, assumption, "text", f"assumptions[{index}]")
            if assumption.get("reviewByStage") not in REVIEW_STAGES:
                errors.append(f"assumptions[{index}].reviewByStage must be one of {sorted(REVIEW_STAGES)}")

    decisions = manifest.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        errors.append("decisions must contain at least one decision")
    else:
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                errors.append(f"decisions[{index}] must be an object")
                continue
            _require_exact_keys(errors, decision, {"title", "context", "choice", "rationale", "alternatives", "consequences", "reviewWhen"}, f"decisions[{index}]")
            for key in ("title", "context", "choice", "rationale", "reviewWhen"):
                _require_string(errors, decision, key, f"decisions[{index}]")
            _require_string_list(errors, decision, "alternatives", f"decisions[{index}]")
            _require_string_list(errors, decision, "consequences", f"decisions[{index}]", minimum=1)

    external = manifest.get("externalActions")
    expected_external = {"createRepository", "configureRemote", "provisionCloud", "setSecrets", "deploy"}
    if not isinstance(external, dict) or set(external) != expected_external:
        errors.append(f"externalActions must contain exactly {sorted(expected_external)}")
    elif any(value is not False for value in external.values()):
        errors.append("all externalActions must be false for local generation")

    if any(contains_secret(text) for text in _strings(manifest)):
        errors.append("manifest contains a possible secret")
    if any(contains_placeholder(text) for text in _strings(manifest)):
        errors.append("manifest contains an unfinished placeholder")
    return errors


def _bullets(values: Iterable[str], *, empty: str) -> str:
    values_list = list(values)
    if not values_list:
        return f"- {empty}\n"
    return "".join(f"- {value}\n" for value in values_list)


def _is_zh(manifest: dict[str, Any]) -> bool:
    return str(manifest.get("language", "")).lower().startswith("zh")


def _module_titles(manifest: dict[str, Any]) -> list[str]:
    titles = MODULE_TITLES_ZH if _is_zh(manifest) else MODULE_TITLES_EN
    return [titles[module] for module in manifest["modules"]]


def _version_asset(name: str) -> str:
    return (SKILL_ROOT / "assets" / "versioning" / name).read_text(encoding="utf-8")


def _render_changelog(manifest: dict[str, Any]) -> str:
    if _is_zh(manifest):
        return (
            "# Changelog\n\n所有重要变化遵循语义化版本。\n\n"
            "## Unreleased\n\n"
            "使用 `重大迭代`/`不兼容变更`、`新增`、`修复`/`维护`/`优化`/`安全与运维` 分类。\n\n"
            "## [0.1.0] - 2026-09-03\n\n### 新增\n\n- 建立经过验证的项目基础。\n"
        )
    return (
        "# Changelog\n\nAll notable changes follow Semantic Versioning.\n\n"
        "## Unreleased\n\n"
        "Use `Breaking`, `Added`, `Fixed`, `Maintenance`, or `Security` categories.\n\n"
        "## [0.1.0] - 2026-09-03\n\n### Added\n\n- Established the initial verified project foundation.\n"
    )


def _render_version_workflow(adapter: str) -> str:
    if adapter == "typescript-node":
        setup = (
            "      - uses: actions/setup-node@v6\n"
            "        with:\n"
            "          node-version-file: .node-version\n"
            "          cache: npm\n"
            "      - run: npm ci\n"
        )
        impact = "npm run --silent version:impact"
        prepare = "npm run version:prepare"
        check = "npm run version:check"
        files = "package.json package-lock.json CHANGELOG.md"
    else:
        setup = (
            "      - uses: actions/setup-python@v6\n"
            "        with:\n"
            "          python-version-file: .python-version\n"
        ) if adapter == "python" else "      - uses: actions/setup-python@v6\n        with:\n          python-version: '3.12'\n"
        impact = "python scripts/version.py impact"
        prepare = "python scripts/version.py prepare"
        check = "python scripts/version.py check"
        files = "pyproject.toml CHANGELOG.md" if adapter == "python" else "VERSION CHANGELOG.md"
    return (
        "name: Prepare semantic version\n\n"
        "on:\n  workflow_run:\n    workflows: [CI]\n    types: [completed]\n    branches: [main]\n\n"
        "permissions:\n  contents: write\n  pull-requests: write\n  actions: read\n\n"
        "concurrency:\n  group: semantic-version-main\n  cancel-in-progress: false\n\n"
        "jobs:\n  prepare:\n"
        "    if: github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.head_branch == 'main'\n"
        "    runs-on: ubuntu-latest\n"
        "    env:\n"
        "      VERSION_BOT_TOKEN: ${{ secrets.VERSION_BOT_TOKEN }}\n"
        "      GH_TOKEN: ${{ secrets.VERSION_BOT_TOKEN }}\n"
        "      SOURCE_SHA: ${{ github.event.workflow_run.head_sha }}\n"
        "    steps:\n"
        "      - name: Guard version bot token\n"
        "        run: test -n \"$VERSION_BOT_TOKEN\" || (echo 'VERSION_BOT_TOKEN is required' && exit 1)\n"
        "      - uses: actions/checkout@v6\n"
        "        with:\n"
        "          ref: ${{ github.event.workflow_run.head_sha }}\n"
        "          fetch-depth: 0\n"
        "          token: ${{ secrets.VERSION_BOT_TOKEN }}\n"
        + setup
        + "      - name: Determine release impact\n"
        "        id: impact\n"
        "        shell: bash\n"
        "        run: |\n"
        "          if [[ \"$(git log -1 --pretty=%s)\" == chore\\(release\\):\\ prepare\\ v* ]]; then echo 'release=false' >> \"$GITHUB_OUTPUT\"; exit 0; fi\n"
        "          git fetch origin main\n"
        "          test \"$(git rev-parse origin/main)\" = \"$SOURCE_SHA\" || { echo 'release=false' >> \"$GITHUB_OUTPUT\"; exit 0; }\n"
        f"          impact_line=$({impact})\n"
        "          if [[ \"$impact_line\" == none ]]; then echo 'release=false' >> \"$GITHUB_OUTPUT\"; exit 0; fi\n"
        "          [[ \"$impact_line\" =~ ^(patch|minor|major)\\ ([0-9]+\\.[0-9]+\\.[0-9]+)$ ]] || exit 1\n"
        "          echo \"version=${BASH_REMATCH[2]}\" >> \"$GITHUB_OUTPUT\"\n"
        "          echo 'release=true' >> \"$GITHUB_OUTPUT\"\n"
        "      - name: Prepare version\n"
        "        if: steps.impact.outputs.release == 'true'\n"
        f"        run: {prepare}\n"
        "      - name: Verify and commit version\n"
        "        if: steps.impact.outputs.release == 'true'\n"
        "        shell: bash\n"
        "        run: |\n"
        f"          {check}\n"
        "          git config user.name 'project-version-bot'\n"
        "          git config user.email 'project-version-bot@users.noreply.github.com'\n"
        f"          git add -- {files}\n"
        "          git commit -m \"chore(release): prepare v${{ steps.impact.outputs.version }}\"\n"
        "          git fetch origin main\n"
        "          test \"$(git rev-parse origin/main)\" = \"$SOURCE_SHA\" || exit 1\n"
        "          if git push origin HEAD:main; then exit 0; fi\n"
        "          branch=automation/release-v${{ steps.impact.outputs.version }}\n"
        "          git push origin HEAD:refs/heads/$branch\n"
        "          gh pr create --base main --head \"$branch\" --title \"chore(release): prepare v${{ steps.impact.outputs.version }}\" --body 'Automated semantic version preparation; merge to run CI on the exact version commit.'\n"
    )


def _status_label(status: str, zh: bool) -> str:
    labels = {
        "ready": ("可以开工", "Ready to build"),
        "ready-with-followups": ("可以开工，但有已记录的后续事项", "Ready with recorded follow-ups"),
        "not-ready": ("暂不可开工", "Not ready"),
    }
    pair = labels.get(status, ("尚未验证", "Not yet verified"))
    return pair[0] if zh else pair[1]


def _render_start_here(manifest: dict[str, Any], status: str) -> str:
    project = manifest["project"]
    assumptions = manifest["assumptions"]
    zh = _is_zh(manifest)
    if zh:
        return (
            f"# {project['name']}：项目地图\n\n"
            f"开工状态：**{_status_label(status, True)}**\n\n"
            "## 我们正在做什么\n\n"
            f"{project['summary']}\n\n"
            f"要解决的问题：{project['problem']}\n\n"
            "## 第一阶段\n\n"
            + _bullets(project["firstRelease"], empty="尚无")
            + "\n## 当前不做\n\n"
            + _bullets(project["notInScope"], empty="没有额外排除项")
            + "\n## 已启用的工程保护\n\n"
            + _bullets(_module_titles(manifest), empty="尚无")
            + "\n## 已记录的后续确认\n\n"
            + _bullets((f"{item['text']}（最迟：{item['reviewByStage']}）" for item in assumptions), empty="当前没有未决假设")
            + "\n## 下一步\n\n让 Codex 基于 `docs/project/brief.md` 共同设计第一阶段；设计获得确认前不要编写产品代码。\n"
        )
    return (
        f"# {project['name']}: Project Map\n\n"
        f"Start status: **{_status_label(status, False)}**\n\n"
        "## What we are building\n\n"
        f"{project['summary']}\n\nProblem: {project['problem']}\n\n"
        "## First release\n\n"
        + _bullets(project["firstRelease"], empty="None")
        + "\n## Explicitly excluded\n\n"
        + _bullets(project["notInScope"], empty="No additional exclusions")
        + "\n## Foundation modules\n\n"
        + _bullets(_module_titles(manifest), empty="None")
        + "\n## Recorded follow-ups\n\n"
        + _bullets((f"{item['text']} (review by {item['reviewByStage']})" for item in assumptions), empty="No unresolved assumptions")
        + "\n## Next step\n\nAsk Codex to design the first release from `docs/project/brief.md`; do not write product code before the design is approved.\n"
    )


def _render_agents(manifest: dict[str, Any]) -> str:
    project = manifest["project"]
    modules = set(manifest["modules"])
    environment_rule = "- Never test changes against production resources; preserve environment isolation.\n" if "environments" in modules else ""
    release_rule = "- Classify shipped behavior in the changelog; prepare a higher semantic version before non-production verification, and never deploy production without a new version.\n" if "release" in modules else ""
    data_rule = "- Treat data migrations, code rollback, and data restoration as separate decisions.\n" if "database" in modules else ""
    payment_rule = "- Never use real charges in development or automated tests; verify webhooks, reconciliation, refunds, and duplicate-event handling.\n" if "payments" in modules else ""
    tenant_rule = "- Prove tenant isolation in authorization rules and tests; never rely only on a user-interface filter.\n" if "multi-tenant" in modules else ""
    mobile_rule = "- Record supported app/OS versions and make server and data changes compatible with clients that update late.\n" if "mobile" in modules else ""
    return (
        f"# Project instructions: {project['name']}\n\n"
        "## Start every task\n\n"
        "- Read `START-HERE.md`, `docs/project/brief.md`, and the current stage gates.\n"
        "- Restate the requested outcome and its acceptance criteria before changing behavior.\n"
        "- Preserve the approved first-release boundary; propose scope changes explicitly.\n"
        "- Explain decisions and results to the project owner in plain language.\n\n"
        "## Engineering agreements\n\n"
        "- Keep changes small, independently testable, and visible in Git.\n"
        "- Run the project's verification command after relevant changes.\n"
        "- Add or update tests when behavior changes or a defect is fixed.\n"
        "- Do not add a dependency without explaining its purpose and maintenance cost.\n"
        "- Never commit real secrets, tokens, customer data, production exports, or local credentials.\n"
        "- Record architecture-significant or difficult-to-reverse decisions in `docs/project/decisions/`.\n"
        f"{environment_rule}{release_rule}{data_rule}{payment_rule}{tenant_rule}{mobile_rule}"
        "- External actions such as repository changes, cloud provisioning, secret setting, deployment, or production access require an explicit user request.\n\n"
        "## Stage changes\n\n"
        "When real users, production data, payments, scheduled writes, new vendors, or business-critical use are introduced, reassess `.project-start/manifest.json` before proceeding.\n"
    )


def _render_common(manifest: dict[str, Any], status: str) -> dict[str, FileSpec]:
    project = manifest["project"]
    classification = manifest["classification"]
    technology = manifest["technology"]
    modules = set(manifest["modules"])
    decision = manifest["decisions"][0]
    zh = _is_zh(manifest)
    empty = "无" if zh else "None"
    files: dict[str, FileSpec] = {
        "START-HERE.md": FileSpec(_render_start_here(manifest, status), "shared", "project-brief"),
        "AGENTS.md": FileSpec(_render_agents(manifest), "shared", "continuity"),
        "CHANGELOG.md": FileSpec(_render_changelog(manifest), "shared", "versioning"),
        ".gitignore": FileSpec(
            ".env\n.env.*\n!.env.example\n.dev.vars\n*.pem\n*.key\nnode_modules/\ndist/\ncoverage/\n.venv/\n__pycache__/\n*.py[cod]\n.pytest_cache/\n.DS_Store\nThumbs.db\nbackups/\nartifacts/\n",
            "shared",
            "git",
        ),
        "docs/project/brief.md": FileSpec(
            f"# {'项目简报' if zh else 'Project brief'}\n\n"
            f"## {'问题' if zh else 'Problem'}\n\n{project['problem']}\n\n"
            f"## {'使用者' if zh else 'Users'}\n\n{_bullets(project['users'], empty=empty)}\n"
            f"## {'第一阶段' if zh else 'First release'}\n\n{_bullets(project['firstRelease'], empty=empty)}\n"
            f"## {'明确不做' if zh else 'Not in scope'}\n\n{_bullets(project['notInScope'], empty=empty)}\n"
            f"## {'成功标准' if zh else 'Success criteria'}\n\n{_bullets(project['successCriteria'], empty=empty)}",
            "shared",
            "project-brief",
        ),
        "docs/project/architecture.md": FileSpec(
            f"# {'初始架构' if zh else 'Initial architecture'}\n\n"
            f"- {'产品类型' if zh else 'Product type'}: `{classification['productType']}`\n"
            f"- {'运行方式' if zh else 'Run shape'}: `{classification['runShape']}`\n"
            f"- {'技术适配器' if zh else 'Adapter'}: `{technology['adapter']}`\n"
            f"- {'部署画像' if zh else 'Deployment profile'}: `{technology.get('deploymentProfile', 'none')}`\n"
            f"- {'风险等级' if zh else 'Risk level'}: `{classification['riskLevel']}`\n\n"
            f"## {'选择理由' if zh else 'Rationale'}\n\n{technology['rationale']}\n\n"
            f"## {'边界' if zh else 'Boundary'}\n\n"
            f"{'本文件记录已批准的项目起点。具体产品架构应在第一阶段设计获批后补充。' if zh else 'This records the approved starting point. Add product architecture only after first-release design approval.'}\n",
            "shared",
            "decisions",
        ),
        "docs/project/roadmap.md": FileSpec(
            f"# {'阶段路线' if zh else 'Stage roadmap'}\n\n"
            f"## {'现在' if zh else 'Now'}\n\n- {'完成第一阶段设计并通过最低验证。' if zh else 'Complete first-release design and pass minimum verification.'}\n\n"
            f"## {'内部试用前' if zh else 'Before internal use'}\n\n- {'重新检查真实身份、隔离测试数据、错误记录与恢复要求。' if zh else 'Reassess identity, isolated test data, failure visibility, and recovery.'}\n\n"
            f"## {'正式上线前' if zh else 'Before production'}\n\n- {'完成版本化发布、非生产验证、备份恢复、运行检查、费用边界与回退。' if zh else 'Complete versioned release, non-production validation, recovery, operations, cost limits, and rollback.'}\n\n"
            f"## {'关键基础设施前' if zh else 'Before critical status'}\n\n- {'完成恢复演练、权限审计、容量降级、事故处理与交接。' if zh else 'Complete recovery drills, permission audit, capacity degradation, incident handling, and handoff.'}\n",
            "shared",
            "stage-gates",
        ),
        "docs/project/stage-gates.md": FileSpec(_render_stage_gates(manifest), "shared", "stage-gates"),
        "docs/project/decisions/0001-initial-foundation.md": FileSpec(
            f"# 0001: {decision['title']}\n\n"
            f"## Context\n\n{decision['context']}\n\n"
            f"## Decision\n\n{decision['choice']}\n\n"
            f"## Rationale\n\n{decision['rationale']}\n\n"
            f"## Alternatives\n\n{_bullets(decision['alternatives'], empty='None recorded')}\n"
            f"## Consequences\n\n{_bullets(decision['consequences'], empty='None recorded')}\n"
            f"## Review when\n\n{decision['reviewWhen']}\n",
            "shared",
            "decisions",
        ),
    }
    if modules & {"operations", "backup-recovery", "scheduled-jobs", "cost-capacity"}:
        files["docs/project/operations.md"] = FileSpec(_render_operations(manifest), "shared", "operations")
    if "release" in modules:
        files["docs/project/release-process.md"] = FileSpec(_render_release(manifest), "shared", "release")
    if modules & {"database", "external-api", "auth", "ai", "environments"}:
        env_names = ["APP_ENV=local"]
        if "database" in modules:
            env_names.append("DATABASE_URL=")
        if "auth" in modules:
            env_names.append("SESSION_SECRET=")
        if "external-api" in modules:
            env_names.append("EXTERNAL_API_KEY=")
        if "ai" in modules:
            env_names.append("AI_PROVIDER_API_KEY=")
        if "payments" in modules:
            env_names.append("PAYMENT_PROVIDER_SECRET=")
        files[".env.example"] = FileSpec("\n".join(env_names) + "\n", "shared", "secrets")
    return files


def _render_stage_gates(manifest: dict[str, Any]) -> str:
    modules = set(manifest["modules"])
    zh = _is_zh(manifest)
    build = ["范围、成功标准和重要决定已经确认", "Git 与敏感配置边界存在", "最低验证通过"] if zh else ["Scope, success criteria, and significant decisions are approved", "Git and secret boundaries exist", "Minimum verification passes"]
    internal = ["真实身份和权限边界已验证", "测试数据与生产数据隔离", "失败可被发现并有基本恢复路径"] if zh else ["Real identity and permission boundaries are verified", "Test and production data are isolated", "Failures are visible and a basic recovery path exists"]
    production = ["高于现有正式版本的新版本已经准备完成", "同一版本先在非生产环境验证", "生产成功后固化标签和发布记录，失败不占用版本标签", "正式发布可追溯且可以回退", "发布后检查、费用和运行边界明确"] if zh else ["A new version higher than the latest production release is prepared", "The same version is verified outside production", "Success creates an immutable tag and release while failure leaves the tag unused", "The production release is traceable and reversible", "Post-release checks, cost, and operating limits are explicit"]
    if "database" in modules:
        production.append("备份已经通过恢复验证" if zh else "A backup has passed recovery validation")
    if "payments" in modules:
        production.append("支付沙箱、重复事件、退款、对账和供应商故障路径已验证" if zh else "Payment sandbox, duplicate events, refunds, reconciliation, and provider failure paths are verified")
    if "multi-tenant" in modules:
        internal.append("租户隔离已在权限规则和自动测试中验证" if zh else "Tenant isolation is verified in authorization rules and automated tests")
    if "mobile" in modules:
        production.append("商店发布、旧客户端兼容和无法即时回退的应对方案明确" if zh else "Store release, old-client compatibility, and the no-instant-rollback response are explicit")
    critical = ["恢复演练最近完成", "权限、容量、降级和事故处理已审查", "其他人能够恢复关键访问并接手"] if zh else ["A recovery drill was completed recently", "Permissions, capacity, degradation, and incident handling were reviewed", "Another person can recover critical access and take over"]
    return (
        f"# {'项目阶段门' if zh else 'Project stage gates'}\n\n"
        f"## {'允许开始开发' if zh else 'Ready to build'}\n\n{_bullets(build, empty='None')}\n"
        f"## {'允许内部试用' if zh else 'Ready for internal use'}\n\n{_bullets(internal, empty='None')}\n"
        f"## {'允许正式上线' if zh else 'Ready for production'}\n\n{_bullets(production, empty='None')}\n"
        f"## {'允许成为关键基础设施' if zh else 'Ready for critical status'}\n\n{_bullets(critical, empty='None')}"
    )


def _render_operations(manifest: dict[str, Any]) -> str:
    modules = set(manifest["modules"])
    zh = _is_zh(manifest)
    items = [
        "定义怎样判断系统可用与异常" if zh else "Define how to distinguish healthy, degraded, and failed service",
        "保留足以解释失败的结构化记录" if zh else "Keep structured evidence sufficient to explain failures",
        "明确停止、降级和人工接管方式" if zh else "Define stop, degradation, and manual-takeover paths",
    ]
    if "backup-recovery" in modules:
        items.append("记录备份对象、频率、保留、恢复凭据和最近演练" if zh else "Record backup scope, frequency, retention, recovery access, and latest drill")
    if "cost-capacity" in modules:
        items.append("记录预算、配额、昂贵操作和接近上限时的降级顺序" if zh else "Record budget, quotas, expensive operations, and degradation near limits")
    if "scheduled-jobs" in modules:
        items.append("定时任务必须能停止、重复执行安全并记录断点" if zh else "Scheduled work must be stoppable, idempotent, and checkpointed")
    return f"# {'运行约定' if zh else 'Operating agreements'}\n\n{_bullets(items, empty='None')}"


def _render_release(manifest: dict[str, Any]) -> str:
    zh = _is_zh(manifest)
    if zh:
        return (
            "# 版本与发布流程\n\n"
            "1. 在短期分支完成一项独立变更。\n"
            "2. 更新测试，并在 `CHANGELOG.md > Unreleased` 分类：重大/不兼容为 major，新增为 minor，修复/维护/优化/安全为 patch；混合内容取最高级别。\n"
            "3. 自动准备更高的三段式版本；major 必须明确声明，系统不得猜测。\n"
            "4. 本地验证通过后进入 Pull Request 和自动检查，再在非生产环境验证完全相同的 commit/构建。\n"
            "5. 生产只允许晋升这个未发布的新版本；成功后必须创建 Git tag 与 Release，失败时不创建标签。\n"
            "6. 执行只读 smoke 并记录业务版本、commit 与运行标识。\n"
            "7. 失败时先判断代码回退还是数据修复，绝不把两者混为一体。\n\n"
            "自动版本工作流需要最小权限的 `VERSION_BOT_TOKEN`。若分支保护拒绝直接提交，工作流应创建 release PR，而不是绕过保护。\n"
        )
    return (
        "# Version and release process\n\n"
        "1. Complete one independent change on a short-lived branch.\n"
        "2. Update tests and classify `CHANGELOG.md > Unreleased`: Breaking is major, Added is minor, and Fixed/Maintenance/Security is patch; mixed changes use the highest impact.\n"
        "3. Automatically prepare a higher three-part version; major must be explicitly declared.\n"
        "4. Pass local, pull-request, and automated checks, then verify the exact same commit/build outside production.\n"
        "5. Production may promote only that unpublished version; success must create a Git tag and Release, while failure creates neither.\n"
        "6. Run a read-only smoke check and record business version, commit, and runtime identity.\n"
        "7. On failure, decide separately between code rollback and data repair.\n\n"
        "The automatic version workflow needs a least-privilege `VERSION_BOT_TOKEN`. If branch protection rejects a direct commit, create a release PR instead of bypassing protection.\n"
    )


def _typescript_files(manifest: dict[str, Any]) -> dict[str, FileSpec]:
    slug = manifest["project"]["slug"]
    github = "github" in manifest["modules"]
    package = {
        "name": slug,
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "engines": {"node": ">=24 <25"},
        "scripts": {
            "check": "tsc --noEmit",
            "build": "tsc",
            "test": "npm run build && node --test dist/test/index.test.js",
            "version:check": "node scripts/version.mjs check",
            "version:impact": "node scripts/version.mjs impact",
            "version:prepare": "node scripts/version.mjs prepare",
            "verify": "npm run version:check && npm run check && npm test"
        },
        "devDependencies": {"@types/node": "24.3.0", "typescript": "6.0.3"}
    }
    files = {
        "package.json": FileSpec(json.dumps(package, indent=2) + "\n", "shared", "testing"),
        ".node-version": FileSpec("24\n", "shared", "testing"),
        "tsconfig.json": FileSpec(
            json.dumps({
                "compilerOptions": {
                    "target": "ES2023", "module": "NodeNext", "moduleResolution": "NodeNext", "strict": True,
                    "declaration": True, "outDir": "dist", "rootDir": ".", "noUncheckedIndexedAccess": True,
                    "exactOptionalPropertyTypes": True, "skipLibCheck": True, "types": ["node"]
                },
                "include": ["src/**/*.ts", "test/**/*.ts"]
            }, indent=2) + "\n",
            "shared",
            "testing",
        ),
        "src/index.ts": FileSpec(
            "export function foundationStatus(): string {\n  return \"project foundation ready\";\n}\n",
            "project",
            "testing",
        ),
        "test/index.test.ts": FileSpec(
            "import assert from \"node:assert/strict\";\nimport test from \"node:test\";\n\nimport { foundationStatus } from \"../src/index.js\";\n\ntest(\"starter is executable\", () => {\n  assert.equal(foundationStatus(), \"project foundation ready\");\n});\n",
            "project",
            "testing",
        ),
        "scripts/version.mjs": FileSpec(_version_asset("version.mjs"), "shared", "versioning"),
    }
    if github:
        files[".github/workflows/ci.yml"] = FileSpec(
            "name: CI\n\non:\n  pull_request:\n  push:\n    branches: [main]\n\npermissions:\n  contents: read\n\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v6\n      - uses: actions/setup-node@v6\n        with:\n          node-version-file: .node-version\n          cache: npm\n      - run: npm ci\n      - run: npm run verify\n",
            "shared",
            "github",
        )
        if "release" in manifest["modules"]:
            files[".github/workflows/version.yml"] = FileSpec(
                _render_version_workflow("typescript-node"), "shared", "release"
            )
    return files


def _python_files(manifest: dict[str, Any]) -> dict[str, FileSpec]:
    slug = manifest["project"]["slug"]
    module_name = slug.replace("-", "_")
    github = "github" in manifest["modules"]
    files = {
        ".python-version": FileSpec("3.12\n", "shared", "testing"),
        "pyproject.toml": FileSpec(
            f"[build-system]\nrequires = [\"setuptools>=75\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"{slug}\"\nversion = \"0.1.0\"\nrequires-python = \">=3.12\"\ndependencies = []\n\n[tool.setuptools.packages.find]\nwhere = [\"src\"]\n",
            "shared",
            "testing",
        ),
        f"src/{module_name}/__init__.py": FileSpec(
            "def foundation_status() -> str:\n    return \"project foundation ready\"\n",
            "project",
            "testing",
        ),
        "tests/test_app.py": FileSpec(
            f"import sys\nimport unittest\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / \"src\"))\n\nfrom {module_name} import foundation_status\n\n\nclass StarterTest(unittest.TestCase):\n    def test_starter_is_executable(self) -> None:\n        self.assertEqual(foundation_status(), \"project foundation ready\")\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n",
            "project",
            "testing",
        ),
        "scripts/verify.py": FileSpec(
            "from __future__ import annotations\n\nimport compileall\nimport subprocess\nimport sys\n\nif subprocess.call([sys.executable, \"scripts/version.py\", \"check\"]):\n    raise SystemExit(1)\nif not compileall.compile_dir(\"src\", quiet=1):\n    raise SystemExit(1)\nraise SystemExit(subprocess.call([sys.executable, \"-m\", \"unittest\", \"discover\", \"-s\", \"tests\", \"-v\"]))\n",
            "shared",
            "testing",
        ),
        "scripts/version.py": FileSpec(_version_asset("version.py"), "shared", "versioning"),
    }
    if github:
        files[".github/workflows/ci.yml"] = FileSpec(
            "name: CI\n\non:\n  pull_request:\n  push:\n    branches: [main]\n\npermissions:\n  contents: read\n\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v6\n      - uses: actions/setup-python@v6\n        with:\n          python-version-file: .python-version\n      - run: python scripts/verify.py\n",
            "shared",
            "github",
        )
        if "release" in manifest["modules"]:
            files[".github/workflows/version.yml"] = FileSpec(
                _render_version_workflow("python"), "shared", "release"
            )
    return files


def _skill_files(manifest: dict[str, Any]) -> dict[str, FileSpec]:
    project = manifest["project"]
    description = project["summary"].replace("\n", " ").strip()
    if not description.endswith("."):
        description += "."
    description += " Use when the user explicitly requests this bounded workflow."
    skill_text = (
        "---\n"
        f"name: {project['slug']}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {project['name']}\n\n"
        f"Purpose: {project['problem']}\n\n"
        "## Workflow\n\n"
        "1. Confirm that the request matches the approved purpose and boundary.\n"
        "2. Apply only the approved domain method and preserve user choices.\n"
        "3. Validate observable outputs before reporting completion.\n\n"
        "Read `docs/project/brief.md` before adding domain-specific instructions. Keep deterministic logic in scripts and conditional detail in references.\n"
    )
    openai_yaml = (
        "interface:\n"
        f"  display_name: \"{project['name'].replace(chr(34), '')}\"\n"
        "  short_description: \"A bounded, verified workflow skill starter\"\n"
        f"  default_prompt: \"Use ${project['slug']} for its approved workflow.\"\n\n"
        "policy:\n  allow_implicit_invocation: true\n"
    )
    validator = (
        "from __future__ import annotations\n\n"
        "import re\nimport subprocess\nimport sys\nfrom pathlib import Path\n\n"
        "root = Path(sys.argv[1] if len(sys.argv) > 1 else \".\").resolve()\n"
        "path = root / \"SKILL.md\"\n"
        "if not path.is_file():\n    raise SystemExit(\"SKILL.md is missing\")\n"
        "text = path.read_text(encoding=\"utf-8\")\n"
        "if not re.match(r\"^---\\n(?s:.*?)\\n---\\n\", text):\n    raise SystemExit(\"SKILL.md frontmatter is invalid\")\n"
        "if \"name:\" not in text or \"description:\" not in text:\n    raise SystemExit(\"name or description is missing\")\n"
        "if subprocess.call([sys.executable, str(root / \"scripts/version.py\"), \"check\", \"--root\", str(root)]):\n    raise SystemExit(\"version metadata is invalid\")\n"
        "print(\"Skill starter is structurally valid\")\n"
    )
    return {
        "SKILL.md": FileSpec(skill_text, "shared", "testing"),
        "agents/openai.yaml": FileSpec(openai_yaml, "shared", "testing"),
        "scripts/validate_skill.py": FileSpec(validator, "shared", "testing"),
        "scripts/version.py": FileSpec(_version_asset("version.py"), "shared", "versioning"),
        "VERSION": FileSpec("0.1.0\n", "shared", "versioning"),
    }


def render_files(manifest: dict[str, Any], status: str = "not-ready") -> dict[str, FileSpec]:
    files = _render_common(manifest, status)
    adapter = manifest["technology"]["adapter"]
    if adapter == "typescript-node":
        files.update(_typescript_files(manifest))
    elif adapter == "python":
        files.update(_python_files(manifest))
    elif adapter == "codex-skill":
        files.update(_skill_files(manifest))
        if "github" in manifest["modules"] and "release" in manifest["modules"]:
            files[".github/workflows/ci.yml"] = FileSpec(
                "name: CI\n\non:\n  pull_request:\n  push:\n    branches: [main]\n\npermissions:\n  contents: read\n\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v6\n      - uses: actions/setup-python@v6\n        with:\n          python-version: '3.12'\n      - run: python scripts/validate_skill.py .\n",
                "shared",
                "github",
            )
            files[".github/workflows/version.yml"] = FileSpec(
                _render_version_workflow("codex-skill"), "shared", "release"
            )
    return files


def _write_specs(root: Path, specs: dict[str, FileSpec]) -> None:
    for relative, spec in specs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(spec.content.rstrip("\r\n") + "\n", encoding="utf-8")


def _run_command(root: Path, command: list[str], check_id: str, timeout: int = 240) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"id": check_id, "status": "fail", "detail": str(exc)}
    output = (result.stdout + "\n" + result.stderr).strip()
    if len(output) > 4000:
        output = output[-4000:]
    return {
        "id": check_id,
        "status": "pass" if result.returncode == 0 else "fail",
        "detail": output or f"exit code {result.returncode}",
    }


def run_adapter_tools(root: Path, adapter: str, *, prepare: bool) -> list[dict[str, Any]]:
    if adapter == "docs-only":
        return [{"id": "adapter", "status": "unverified", "detail": "No technical adapter was selected."}]
    if adapter == "typescript-node":
        npm = shutil.which("npm")
        if not npm:
            return [{"id": "node-toolchain", "status": "unverified", "detail": "npm is not installed."}]
        checks: list[dict[str, Any]] = []
        if prepare:
            checks.append(_run_command(root, [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund"], "npm-install"))
            if checks[-1]["status"] == "fail":
                return checks
        elif not (root / "package-lock.json").is_file():
            return [{"id": "package-lock", "status": "fail", "detail": "package-lock.json is missing."}]
        else:
            checks.append(_run_command(root, [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"], "npm-ci"))
            if checks[-1]["status"] == "fail":
                return checks
        checks.append(_run_command(root, [npm, "run", "verify"], "typescript-verify"))
        if prepare and (root / "node_modules").exists():
            shutil.rmtree(root / "node_modules")
        return checks
    if adapter == "python":
        return [_run_command(root, [sys.executable, "scripts/verify.py"], "python-verify")]
    if adapter == "codex-skill":
        return [_run_command(root, [sys.executable, "scripts/validate_skill.py", "."], "skill-verify")]
    return [{"id": "adapter", "status": "fail", "detail": f"Unsupported adapter: {adapter}"}]


def _scan_generated(root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    excluded_parts = {"node_modules", ".git", "dist", "coverage", "__pycache__"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if any(part in excluded_parts for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if relative == ".project-start/verification.json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if contains_secret(text):
            checks.append({"id": f"secret:{relative}", "status": "fail", "detail": "Possible secret detected."})
        if contains_placeholder(text):
            checks.append({"id": f"placeholder:{relative}", "status": "fail", "detail": "Unfinished placeholder detected."})
    if not checks:
        checks.append({"id": "content-scan", "status": "pass", "detail": "No secrets or unfinished placeholders detected."})
    return checks


def _status_from_checks(checks: list[dict[str, Any]], assumptions: list[dict[str, Any]], adapter: str) -> str:
    if any(check["status"] == "fail" for check in checks):
        return "not-ready"
    if adapter != "docs-only" and any(check["status"] == "unverified" for check in checks):
        return "not-ready"
    if assumptions or any(check["status"] in {"warn", "unverified"} for check in checks):
        return "ready-with-followups"
    return "ready"


def _recorded_path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise FoundationError("generated file record contains an invalid path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise FoundationError("generated file record contains a path outside the project") from exc
    return path


def _ownership_for(relative: str, specs: dict[str, FileSpec]) -> tuple[str, str]:
    if relative in specs:
        spec = specs[relative]
        return spec.owner, spec.module
    if relative == ".project-start/manifest.json":
        return "system", "project-brief"
    if relative == "package-lock.json":
        return "shared", "testing"
    return "project", "testing"


def build_generated_record(root: Path, specs: dict[str, FileSpec]) -> dict[str, Any]:
    records = []
    excluded = {".project-start/generated-files.json", ".project-start/verification.json"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded or "node_modules" in path.parts or "__pycache__" in path.parts or "dist" in path.parts:
            continue
        owner, module = _ownership_for(relative, specs)
        records.append({"path": relative, "owner": owner, "module": module, "sha256": sha256_path(path)})
    return {
        "schemaVersion": 1,
        "foundationVersion": FOUNDATION_VERSION,
        "files": records,
        "mutableSystemFiles": [".project-start/generated-files.json", ".project-start/verification.json"],
    }


def verify_project(root: Path, *, run_tools: bool = False, prepare_tools: bool = False) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    manifest_path = root / ".project-start/manifest.json"
    if not manifest_path.is_file():
        return _verification("not-ready", "unknown", [{"id": "manifest", "status": "fail", "detail": "Manifest is missing."}])
    try:
        manifest = load_json(manifest_path)
    except FoundationError as exc:
        return _verification("not-ready", "unknown", [{"id": "manifest", "status": "fail", "detail": str(exc)}])
    errors = validate_manifest(manifest)
    checks.append({"id": "manifest", "status": "pass" if not errors else "fail", "detail": "; ".join(errors) if errors else "Manifest is valid."})

    record_path = root / ".project-start/generated-files.json"
    if record_path.is_file():
        try:
            record = load_json(record_path)
            for entry in record.get("files", []):
                path = _recorded_path(root, entry["path"])
                if not path.is_file():
                    checks.append({"id": f"file:{entry['path']}", "status": "fail", "detail": "Generated file is missing."})
                    continue
                actual = sha256_path(path)
                if entry.get("owner") == "system" and actual != entry.get("sha256"):
                    checks.append({"id": f"system-hash:{entry['path']}", "status": "fail", "detail": "System-managed file changed."})
                elif entry.get("owner") == "shared" and actual != entry.get("sha256"):
                    checks.append({"id": f"shared-hash:{entry['path']}", "status": "warn", "detail": "Shared file changed; review before a foundation update."})
            checks.append({"id": "file-record", "status": "pass", "detail": "Generated file record was checked."})
        except (FoundationError, KeyError, TypeError) as exc:
            checks.append({"id": "file-record", "status": "fail", "detail": str(exc)})
    else:
        checks.append({"id": "file-record", "status": "fail", "detail": "Generated file record is missing."})

    checks.extend(_scan_generated(root))
    adapter = manifest.get("technology", {}).get("adapter", "unknown")
    if run_tools:
        checks.extend(run_adapter_tools(root, adapter, prepare=prepare_tools))
    else:
        checks.append({"id": "adapter-tools", "status": "unverified", "detail": "Local adapter commands were not run in this verification."})
    status = _status_from_checks(checks, manifest.get("assumptions", []), adapter)
    return _verification(status, adapter, checks)


def _verification(status: str, adapter: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "foundationVersion": FOUNDATION_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "adapter": adapter,
        "checks": checks,
    }


def generate_project(manifest: dict[str, Any], target: Path, *, run_tools: bool = False) -> dict[str, Any]:
    errors = validate_manifest(manifest)
    if errors:
        raise FoundationError("INVALID_MANIFEST: " + "; ".join(errors))
    target = target.resolve()
    if target.exists():
        if not target.is_dir():
            raise FoundationError(f"TARGET_NOT_DIRECTORY: {target}")
        if target.is_symlink():
            raise FoundationError(f"TARGET_SYMLINK_NOT_ALLOWED: {target}")
        if any(target.iterdir()):
            raise FoundationError(f"TARGET_NOT_EMPTY: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.foundation-", dir=target.parent))
    try:
        specs = render_files(manifest, "not-ready")
        _write_specs(staging, specs)
        write_json(staging / ".project-start/manifest.json", manifest)

        tool_checks = run_adapter_tools(staging, manifest["technology"]["adapter"], prepare=True) if run_tools else [
            {"id": "adapter-tools", "status": "unverified", "detail": "Adapter commands were not run during generation."}
        ]
        scan_checks = _scan_generated(staging)
        adapter = manifest["technology"]["adapter"]
        status = _status_from_checks(scan_checks + tool_checks, manifest["assumptions"], adapter)
        specs["START-HERE.md"] = FileSpec(_render_start_here(manifest, status), "shared", "project-brief")
        _write_specs(staging, {"START-HERE.md": specs["START-HERE.md"]})

        record = build_generated_record(staging, specs)
        write_json(staging / ".project-start/generated-files.json", record)
        verification = _verification(status, manifest["technology"]["adapter"], scan_checks + tool_checks)
        write_json(staging / ".project-start/verification.json", verification)

        final_static = verify_project(staging, run_tools=False)
        static_failures = [check for check in final_static["checks"] if check["status"] == "fail"]
        if static_failures:
            verification = _verification("not-ready", manifest["technology"]["adapter"], verification["checks"] + static_failures)
            write_json(staging / ".project-start/verification.json", verification)
            specs["START-HERE.md"] = FileSpec(_render_start_here(manifest, "not-ready"), "shared", "project-brief")
            _write_specs(staging, {"START-HERE.md": specs["START-HERE.md"]})
            record = build_generated_record(staging, specs)
            write_json(staging / ".project-start/generated-files.json", record)

        if target.exists():
            target.rmdir()
        os.replace(staging, target)
        return verification
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def save_verification(root: Path, verification: dict[str, Any]) -> None:
    write_json(root / ".project-start/verification.json", verification)


def status_text(root: Path) -> str:
    verification_path = root / ".project-start/verification.json"
    if not verification_path.is_file():
        raise FoundationError("VERIFICATION_NOT_FOUND")
    verification = load_json(verification_path)
    manifest = load_json(root / ".project-start/manifest.json")
    zh = _is_zh(manifest)
    status = verification.get("status", "not-ready")
    failures = [check for check in verification.get("checks", []) if check.get("status") == "fail"]
    followups = [check for check in verification.get("checks", []) if check.get("status") in {"warn", "unverified"}]
    if zh:
        lines = [f"开工状态：{_status_label(status, True)}", f"技术适配器：{verification.get('adapter', 'unknown')}"]
        if failures:
            lines.append("失败项：")
            lines.extend(f"- {item['id']}: {item['detail']}" for item in failures)
        if followups:
            lines.append("待确认或未验证：")
            lines.extend(f"- {item['id']}: {item['detail']}" for item in followups)
        return "\n".join(lines)
    lines = [f"Start status: {_status_label(status, False)}", f"Adapter: {verification.get('adapter', 'unknown')}"]
    if failures:
        lines.append("Failures:")
        lines.extend(f"- {item['id']}: {item['detail']}" for item in failures)
    if followups:
        lines.append("Follow-ups or unverified checks:")
        lines.extend(f"- {item['id']}: {item['detail']}" for item in followups)
    return "\n".join(lines)
