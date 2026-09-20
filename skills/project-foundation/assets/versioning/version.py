from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path


STABLE_VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
RELEASE_HEADING = re.compile(r"^## \[((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
IMPACTS = {
    "修复": "patch",
    "维护": "patch",
    "优化": "patch",
    "安全与运维": "patch",
    "fixed": "patch",
    "maintenance": "patch",
    "security": "patch",
    "新增": "minor",
    "added": "minor",
    "重大迭代": "major",
    "不兼容变更": "major",
    "breaking": "major",
}
IMPACT_ORDER = {"patch": 0, "minor": 1, "major": 2}


def fail(code: str, detail: str = "") -> None:
    raise SystemExit(f"{code}: {detail}" if detail else code)


def parse_version(value: str) -> tuple[int, int, int]:
    match = STABLE_VERSION.fullmatch(value)
    if not match:
        fail("INVALID_STABLE_VERSION", value)
    return tuple(int(part) for part in match.groups())


def increment(version: str, impact: str) -> str:
    major, minor, patch = parse_version(version)
    if impact == "major":
        return f"{major + 1}.0.0"
    if impact == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def unreleased_body(changelog: str) -> str:
    match = re.search(r"^## Unreleased\s*$", changelog, re.MULTILINE)
    if not match:
        fail("CHANGELOG_UNRELEASED_MISSING")
    following = re.search(r"^## ", changelog[match.end():], re.MULTILINE)
    end = match.end() + following.start() if following else len(changelog)
    return changelog[match.end():end].strip()


def detect_impact(changelog: str) -> str | None:
    body = unreleased_body(changelog)
    if not body:
        return None
    category: str | None = None
    detected: str | None = None
    for line in body.splitlines():
        heading = re.fullmatch(r"###\s+(.+?)\s*", line)
        if heading:
            category = heading.group(1).strip()
            continue
        if not re.match(r"^\s*-\s+\S", line):
            continue
        if category is None:
            fail("CHANGELOG_UNRELEASED_ITEM_WITHOUT_CATEGORY", line.strip())
        item_impact = IMPACTS.get(category.casefold())
        if item_impact is None:
            fail("CHANGELOG_UNRELEASED_CATEGORY_UNKNOWN", category)
        if detected is None or IMPACT_ORDER[item_impact] > IMPACT_ORDER[detected]:
            detected = item_impact
    return detected


def read_version(root: Path) -> tuple[str, str]:
    version_path = root / "VERSION"
    if version_path.is_file():
        version = version_path.read_text(encoding="utf-8").strip()
        parse_version(version)
        return version, "VERSION"
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.is_file():
        text = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', text, re.MULTILINE)
        if not match:
            fail("PYPROJECT_VERSION_MISSING")
        parse_version(match.group(1))
        return match.group(1), "pyproject.toml"
    fail("VERSION_SOURCE_MISSING")


def write_version(root: Path, source: str, version: str) -> None:
    if source == "VERSION":
        (root / source).write_text(version + "\n", encoding="utf-8")
        return
    path = root / source
    text = path.read_text(encoding="utf-8")
    replaced, count = re.subn(r'(?m)^version\s*=\s*"[^"]+"\s*$', f'version = "{version}"', text, count=1)
    if count != 1:
        fail("PYPROJECT_VERSION_UPDATE_FAILED")
    path.write_text(replaced, encoding="utf-8")


def validate(root: Path) -> tuple[str, str]:
    version, source = read_version(root)
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        fail("CHANGELOG_MISSING")
    changelog = changelog_path.read_text(encoding="utf-8")
    versions = RELEASE_HEADING.findall(changelog)
    if versions.count(version) != 1:
        fail("CURRENT_VERSION_CHANGELOG_COUNT", f"{version}={versions.count(version)}")
    if not versions or versions[0] != version:
        fail("CURRENT_VERSION_NOT_LATEST_CHANGELOG", version)
    detect_impact(changelog)
    return version, source


def assert_clean(root: Path) -> None:
    if not (root / ".git").exists():
        return
    result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        fail("GIT_STATUS_FAILED", result.stderr.strip())
    if result.stdout.strip():
        fail("VERSION_PREPARE_REQUIRES_CLEAN_WORKTREE")


def prepare(root: Path) -> str:
    assert_clean(root)
    current, source = validate(root)
    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    impact = detect_impact(changelog)
    if impact is None:
        fail("CHANGELOG_UNRELEASED_EMPTY")
    target = increment(current, impact)
    body = unreleased_body(changelog)
    marker = re.search(r"^## Unreleased\s*$", changelog, re.MULTILINE)
    assert marker is not None
    following = re.search(r"^## ", changelog[marker.end():], re.MULTILINE)
    end = marker.end() + following.start() if following else len(changelog)
    prefix = changelog[:marker.start()].rstrip()
    suffix = changelog[end:].strip()
    parts = [prefix, "", "## Unreleased", "", f"## [{target}] - {date.today().isoformat()}", "", body]
    if suffix:
        parts.extend(["", suffix])
    write_version(root, source, target)
    changelog_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    validate(root)
    return f"{impact} {target}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "impact", "prepare"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    version, _ = validate(root)
    if args.command == "check":
        print(f"Version v{version} is consistent.")
    elif args.command == "impact":
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        impact = detect_impact(changelog)
        print("none" if impact is None else f"{impact} {increment(version, impact)}")
    else:
        print(prepare(root))


if __name__ == "__main__":
    main()
