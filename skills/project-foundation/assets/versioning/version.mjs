import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const versionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const impacts = new Map([
  ["修复", "patch"], ["维护", "patch"], ["优化", "patch"], ["安全与运维", "patch"],
  ["fixed", "patch"], ["maintenance", "patch"], ["security", "patch"],
  ["新增", "minor"], ["added", "minor"],
  ["重大迭代", "major"], ["不兼容变更", "major"], ["breaking", "major"],
]);
const order = { patch: 0, minor: 1, major: 2 };

function fail(code, detail = "") {
  throw new Error(detail ? `${code}: ${detail}` : code);
}

function parseVersion(version) {
  const match = versionPattern.exec(version);
  if (!match) fail("INVALID_STABLE_VERSION", version);
  return match.slice(1).map(Number);
}

function increment(version, impact) {
  const [major, minor, patch] = parseVersion(version);
  if (impact === "major") return `${major + 1}.0.0`;
  if (impact === "minor") return `${major}.${minor + 1}.0`;
  return `${major}.${minor}.${patch + 1}`;
}

function section(changelog) {
  const match = /^## Unreleased\s*$/m.exec(changelog);
  if (!match) fail("CHANGELOG_UNRELEASED_MISSING");
  const rest = changelog.slice(match.index + match[0].length);
  const next = /^## /m.exec(rest);
  const end = next ? match.index + match[0].length + next.index : changelog.length;
  return { body: changelog.slice(match.index + match[0].length, end).trim(), end, start: match.index };
}

function detectImpact(changelog) {
  const { body } = section(changelog);
  if (!body) return undefined;
  let category;
  let detected;
  for (const line of body.split(/\r?\n/)) {
    const heading = /^###\s+(.+?)\s*$/.exec(line);
    if (heading) {
      category = heading[1].trim();
      continue;
    }
    if (!/^\s*-\s+\S/.test(line)) continue;
    if (!category) fail("CHANGELOG_UNRELEASED_ITEM_WITHOUT_CATEGORY", line.trim());
    const itemImpact = impacts.get(category.toLocaleLowerCase());
    if (!itemImpact) fail("CHANGELOG_UNRELEASED_CATEGORY_UNKNOWN", category);
    if (!detected || order[itemImpact] > order[detected]) detected = itemImpact;
  }
  return detected;
}

function inputs() {
  const manifestPath = path.join(root, "package.json");
  const lockPath = path.join(root, "package-lock.json");
  const changelogPath = path.join(root, "CHANGELOG.md");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const lock = JSON.parse(readFileSync(lockPath, "utf8"));
  const changelog = readFileSync(changelogPath, "utf8");
  parseVersion(manifest.version);
  if (lock.version !== manifest.version || lock.packages?.[""]?.version !== manifest.version) {
    fail("LOCKFILE_VERSION_MISMATCH");
  }
  const headings = [...changelog.matchAll(/^## \[((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))\] - \d{4}-\d{2}-\d{2}$/gm)].map((item) => item[1]);
  if (headings.filter((item) => item === manifest.version).length !== 1 || headings[0] !== manifest.version) {
    fail("CURRENT_VERSION_CHANGELOG_MISMATCH", manifest.version);
  }
  detectImpact(changelog);
  return { manifest, lock, changelog, manifestPath, lockPath, changelogPath };
}

function assertClean() {
  try {
    const status = execFileSync("git", ["status", "--porcelain"], { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    if (status.trim()) fail("VERSION_PREPARE_REQUIRES_CLEAN_WORKTREE");
  } catch (error) {
    if (error instanceof Error && error.message.includes("VERSION_PREPARE_REQUIRES_CLEAN_WORKTREE")) throw error;
  }
}

function prepare() {
  assertClean();
  const state = inputs();
  const impact = detectImpact(state.changelog);
  if (!impact) fail("CHANGELOG_UNRELEASED_EMPTY");
  const target = increment(state.manifest.version, impact);
  const unreleased = section(state.changelog);
  const prefix = state.changelog.slice(0, unreleased.start).trimEnd();
  const suffix = state.changelog.slice(unreleased.end).trim();
  const today = new Date().toISOString().slice(0, 10);
  const parts = [prefix, "", "## Unreleased", "", `## [${target}] - ${today}`, "", unreleased.body];
  if (suffix) parts.push("", suffix);
  state.manifest.version = target;
  state.lock.version = target;
  state.lock.packages[""].version = target;
  writeFileSync(state.manifestPath, `${JSON.stringify(state.manifest, null, 2)}\n`);
  writeFileSync(state.lockPath, `${JSON.stringify(state.lock, null, 2)}\n`);
  writeFileSync(state.changelogPath, `${parts.join("\n").trimEnd()}\n`);
  inputs();
  return `${impact} ${target}`;
}

const command = process.argv[2];
const state = inputs();
if (command === "check") console.log(`Version v${state.manifest.version} is consistent.`);
else if (command === "impact") {
  const impact = detectImpact(state.changelog);
  console.log(impact ? `${impact} ${increment(state.manifest.version, impact)}` : "none");
} else if (command === "prepare") console.log(prepare());
else fail("USAGE", "version.mjs <check|impact|prepare>");
