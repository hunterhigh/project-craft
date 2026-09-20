from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from foundation_lib import (  # noqa: E402
    FoundationError,
    contains_secret,
    generate_project,
    load_json,
    sha256_path,
    status_text,
    validate_manifest,
    verify_project,
)


EXAMPLE_PATH = SKILL_ROOT / "references" / "manifest-example.json"
SCENARIOS_PATH = Path(__file__).resolve().parent / "fixtures" / "scenarios.json"


def base_manifest() -> dict:
    manifest = load_json(EXAMPLE_PATH)
    manifest["assumptions"] = []
    return manifest


def scenario_manifest(scenario: dict) -> dict:
    manifest = base_manifest()
    manifest["project"]["name"] = scenario["id"].replace("-", " ").title()
    manifest["project"]["slug"] = scenario["id"]
    manifest["classification"] = copy.deepcopy(scenario["classification"])
    manifest["technology"]["adapter"] = scenario["adapter"]
    manifest["modules"] = list(scenario["modules"])
    return manifest


class ManifestTests(unittest.TestCase):
    def test_example_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(load_json(EXAMPLE_PATH)), [])

    def test_critical_dimension_requires_critical_risk(self) -> None:
        manifest = base_manifest()
        manifest["classification"]["riskDimensions"]["money"] = "critical"
        errors = validate_manifest(manifest)
        self.assertTrue(any("critical risk dimension" in error for error in errors))

    def test_module_dependencies_are_enforced(self) -> None:
        manifest = base_manifest()
        manifest["modules"].remove("security")
        errors = validate_manifest(manifest)
        self.assertTrue(any("module auth requires" in error for error in errors))

    def test_unknown_fields_and_payment_gaps_are_rejected(self) -> None:
        extra_field_manifest = base_manifest()
        extra_field_manifest["project"]["mystery"] = True
        self.assertTrue(any("project contains unsupported keys" in error for error in validate_manifest(extra_field_manifest)))
        payment_manifest = base_manifest()
        payment_manifest["classification"]["riskDimensions"]["money"] = "standard"
        self.assertTrue(any("money risk requires payments" in error for error in validate_manifest(payment_manifest)))

    def test_secret_and_placeholder_are_rejected(self) -> None:
        secret_manifest = base_manifest()
        secret_manifest["project"]["summary"] = "sk-abcdefghijklmnopqrstuvwxyz123456"
        self.assertTrue(any("possible secret" in error for error in validate_manifest(secret_manifest)))
        placeholder_manifest = base_manifest()
        placeholder_manifest["project"]["summary"] = "TBD"
        self.assertTrue(any("unfinished placeholder" in error for error in validate_manifest(placeholder_manifest)))
        self.assertTrue(contains_secret("api_key=abcdefghijklmnop1234"))

    def test_scenario_rules_and_outputs(self) -> None:
        scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        for scenario in scenarios:
            with self.subTest(scenario=scenario["id"]):
                manifest = scenario_manifest(scenario)
                errors = validate_manifest(manifest)
                self.assertEqual(not errors, scenario["valid"], errors)
                if not scenario["valid"]:
                    continue
                with tempfile.TemporaryDirectory() as temp:
                    target = Path(temp) / "project"
                    generate_project(manifest, target, run_tools=False)
                    for relative in scenario.get("requiredOutputs", []):
                        self.assertTrue((target / relative).is_file(), relative)
                    for relative in scenario.get("forbiddenOutputs", []):
                        self.assertFalse((target / relative).exists(), relative)


class GenerationTests(unittest.TestCase):
    def test_docs_only_generation_is_transactional_and_stable(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "docs-only"
        manifest["classification"] = {
            "productType": "web",
            "userShape": "owner-only",
            "runShape": "local",
            "collaborationShape": "ai-assisted",
            "stage": "idea",
            "riskLevel": "low",
            "riskDimensions": {
                "data": "low", "identity": "none", "money": "none", "privacy": "none",
                "externalSystems": "none", "automation": "none", "businessDependency": "low"
            },
        }
        manifest["modules"] = [
            "project-brief", "decisions", "git", "versioning", "stage-gates", "testing", "secrets", "continuity"
        ]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            result = generate_project(manifest, target, run_tools=False)
            self.assertEqual(result["status"], "ready-with-followups")
            self.assertTrue((target / ".project-start/manifest.json").is_file())
            self.assertTrue((target / ".project-start/generated-files.json").is_file())
            self.assertIn("可以开工", (target / "START-HERE.md").read_text(encoding="utf-8"))
            digest = sha256_path(target / "docs/project/brief.md")
            self.assertEqual(digest, sha256_path(target / "docs/project/brief.md"))
            self.assertIn("可以开工", status_text(target))

    def test_technical_adapter_is_not_ready_without_tool_verification(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "python"
        with tempfile.TemporaryDirectory() as temp:
            result = generate_project(manifest, Path(temp) / "project", run_tools=False)
            self.assertEqual(result["status"], "not-ready")

    def test_nonempty_target_is_rejected_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            target.mkdir()
            marker = target / "owner-file.txt"
            marker.write_text("preserve me\n", encoding="utf-8")
            with self.assertRaisesRegex(FoundationError, "TARGET_NOT_EMPTY"):
                generate_project(base_manifest(), target)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve me\n")
            self.assertEqual(list(target.iterdir()), [marker])

    def test_invalid_manifest_leaves_no_target(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "unsupported"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            with self.assertRaisesRegex(FoundationError, "INVALID_MANIFEST"):
                generate_project(manifest, target)
            self.assertFalse(target.exists())

    def test_python_adapter_runs_its_real_verification(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "python"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            result = generate_project(manifest, target, run_tools=True)
            self.assertEqual(result["status"], "ready")
            verification = verify_project(target, run_tools=True)
            self.assertEqual(verification["status"], "ready")
            self.assertTrue(any(check["id"] == "python-verify" and check["status"] == "pass" for check in verification["checks"]))

    def test_python_adapter_prepares_a_minor_version_from_added_notes(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "python"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            generate_project(manifest, target, run_tools=False)
            changelog_path = target / "CHANGELOG.md"
            changelog = changelog_path.read_text(encoding="utf-8")
            changelog_path.write_text(
                changelog.replace("## Unreleased\n", "## Unreleased\n\n### Added\n\n- Added a small module.\n", 1),
                encoding="utf-8",
            )
            impact = subprocess.run(
                [sys.executable, "scripts/version.py", "impact"], cwd=target, capture_output=True, text=True, check=False
            )
            self.assertEqual(impact.returncode, 0, impact.stderr)
            self.assertEqual(impact.stdout.strip(), "minor 0.2.0")
            prepared = subprocess.run(
                [sys.executable, "scripts/version.py", "prepare"], cwd=target, capture_output=True, text=True, check=False
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertIn('version = "0.2.0"', (target / "pyproject.toml").read_text(encoding="utf-8"))
            self.assertIn("## [0.2.0]", changelog_path.read_text(encoding="utf-8"))

    def test_generated_release_automation_uses_version_before_ci_promotion(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "typescript-node"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            generate_project(manifest, target, run_tools=False)
            workflow = (target / ".github/workflows/version.yml").read_text(encoding="utf-8")
            package = json.loads((target / "package.json").read_text(encoding="utf-8"))
            self.assertEqual(package["scripts"]["version:prepare"], "node scripts/version.mjs prepare")
            self.assertIn("VERSION_BOT_TOKEN", workflow)
            self.assertIn("chore\\(release\\):\\ prepare\\ v*", workflow)
            self.assertLess(workflow.index("version:check"), workflow.index("git push origin HEAD:main"))
            self.assertIn("gh pr create", workflow)

    @unittest.skipUnless(shutil.which("npm"), "npm is required for the TypeScript adapter test")
    def test_typescript_adapter_installs_and_runs_its_real_verification(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "typescript-node"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            result = generate_project(manifest, target, run_tools=True)
            self.assertEqual(result["status"], "ready")
            self.assertTrue((target / "package-lock.json").is_file())
            self.assertFalse((target / "node_modules").exists())
            self.assertTrue(any(check["id"] == "typescript-verify" and check["status"] == "pass" for check in result["checks"]))
            changelog_path = target / "CHANGELOG.md"
            changelog_path.write_text(
                changelog_path.read_text(encoding="utf-8").replace(
                    "## Unreleased\n", "## Unreleased\n\n### 新增\n\n- 新增一个小模块。\n", 1
                ),
                encoding="utf-8",
            )
            impact = subprocess.run(
                ["node", "scripts/version.mjs", "impact"], cwd=target, capture_output=True, text=True, check=False
            )
            self.assertEqual(impact.returncode, 0, impact.stderr)
            self.assertEqual(impact.stdout.strip(), "minor 0.2.0")
            prepared = subprocess.run(
                ["node", "scripts/version.mjs", "prepare"], cwd=target, capture_output=True, text=True, check=False
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertEqual(json.loads((target / "package.json").read_text(encoding="utf-8"))["version"], "0.2.0")
            self.assertEqual(json.loads((target / "package-lock.json").read_text(encoding="utf-8"))["version"], "0.2.0")

    def test_codex_skill_adapter_runs_its_real_verification(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "codex-skill"
        manifest["classification"]["productType"] = "skill"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            result = generate_project(manifest, target, run_tools=True)
            self.assertEqual(result["status"], "ready")
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0")
            self.assertTrue((target / "scripts/version.py").is_file())
            self.assertTrue(any(check["id"] == "skill-verify" and check["status"] == "pass" for check in result["checks"]))

    def test_project_foundation_version_metadata_is_consistent(self) -> None:
        result = subprocess.run(
            [sys.executable, "assets/versioning/version.py", "check"],
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("v0.2.0", result.stdout)

    def test_version_asset_classifies_patch_minor_major_and_mixed_changes(self) -> None:
        cases = {
            "Fixed": "patch 1.2.4",
            "Added": "minor 1.3.0",
            "Breaking": "major 2.0.0",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            for category, expected in cases.items():
                (root / "CHANGELOG.md").write_text(
                    f"# Changelog\n\n## Unreleased\n\n### {category}\n\n- Change.\n\n## [1.2.3] - 2026-09-03\n\n### Added\n\n- Existing.\n",
                    encoding="utf-8",
                )
                result = subprocess.run(
                    [sys.executable, str(SKILL_ROOT / "assets/versioning/version.py"), "impact", "--root", str(root)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## Unreleased\n\n### Fixed\n\n- Fix.\n\n### Added\n\n- Feature.\n\n### Breaking\n\n- Product generation.\n\n## [1.2.3] - 2026-09-03\n\n### Added\n\n- Existing.\n",
                encoding="utf-8",
            )
            mixed = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "assets/versioning/version.py"), "impact", "--root", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(mixed.stdout.strip(), "major 2.0.0")
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## Unreleased\n\n### Changed\n\n- Ambiguous.\n\n## [1.2.3] - 2026-09-03\n\n### Added\n\n- Existing.\n",
                encoding="utf-8",
            )
            unknown = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "assets/versioning/version.py"), "impact", "--root", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(unknown.returncode, 0)
            self.assertIn("CHANGELOG_UNRELEASED_CATEGORY_UNKNOWN", unknown.stderr)

    def test_shared_drift_warns_and_system_drift_fails(self) -> None:
        manifest = base_manifest()
        manifest["technology"]["adapter"] = "docs-only"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project"
            generate_project(manifest, target)
            (target / "AGENTS.md").write_text("owner update\n", encoding="utf-8")
            shared_result = verify_project(target)
            self.assertTrue(any(check["id"] == "shared-hash:AGENTS.md" and check["status"] == "warn" for check in shared_result["checks"]))
            manifest_path = target / ".project-start/manifest.json"
            manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
            system_result = verify_project(target)
            self.assertTrue(any(check["id"] == "system-hash:.project-start/manifest.json" and check["status"] == "fail" for check in system_result["checks"]))


if __name__ == "__main__":
    unittest.main()
