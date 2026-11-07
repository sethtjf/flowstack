#!/usr/bin/env bash
# Validate the marketplace and every plugin in it.
#
# 1. `claude plugin validate .` on the marketplace manifest.
# 2. `claude plugin validate plugins/<name>` for each plugin directory.
# 3. Structural checks the CLI does not cover: JSON syntax, `source` paths
#    that exist, marketplace/plugin.json name agreement, license fields,
#    skill names, and plugin directories missing from marketplace.json.
# 4. Shared skills: every shared/skills/<skill>/ must exist, byte for byte,
#    in plugins/code/skills/ and plugins/work/skills/ (scripts/sync-shared.sh).
# 5. OpenAI configs (ChatGPT and Codex): .agents/plugins/marketplace.json and
#    plugins/<name>/plugin.json must match what scripts/build-openai.py
#    generates, and each plugin.json must fit the portable Agent Plugins
#    schema's top-level rules.
# 6. Skill script tests: shared/skills/write/scripts/test_lint.py (fake
#    linters, so it needs only python3).
#
# Exits non-zero if any step fails. If the `claude` CLI is not installed,
# steps 1 and 2 are skipped with a warning and step 3 still runs.
#
# Usage: scripts/validate.sh   (from anywhere inside the repo)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

failed=0
fail() { echo "FAIL: $*" >&2; failed=1; }

if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL: python3 is required for the structural checks" >&2
  exit 1
fi

# --- 1 & 2: claude plugin validate -----------------------------------------
if command -v claude >/dev/null 2>&1; then
  echo "==> claude plugin validate . (marketplace)"
  claude plugin validate . || fail "marketplace manifest failed validation"

  for dir in plugins/*/; do
    [ -d "$dir" ] || continue
    dir="${dir%/}"
    echo
    echo "==> claude plugin validate $dir"
    claude plugin validate "$dir" || fail "$dir failed validation"
  done
else
  echo "WARN: claude CLI not found; skipping 'claude plugin validate'." >&2
  echo "      Install it with: npm i -g @anthropic-ai/claude-code" >&2
fi

# --- 3: structural checks ---------------------------------------------------
echo
echo "==> structural checks"
python3 -I - "$ROOT" <<'PY' || failed=1
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
errors = []

# Reserved marketplace names. `claude plugin validate` accepts these, but
# `claude plugin marketplace add` refuses them. Source:
# https://code.claude.com/docs/en/plugins/marketplace-reference.md#reserved-names
RESERVED = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "anthropic-marketplace", "anthropic-plugins", "agent-skills",
    "anthropic-agent-skills", "life-sciences", "knowledge-work-plugins",
    "claude-for-legal", "claude-for-financial-services",
    "financial-services-plugins", "first-party-plugins", "claude-tag-plugins",
    "claude-community", "claude-plugins-community", "healthcare",
    "anthropic-plugin-directory", "claude-plugin-directory",
    "inline", "builtin", "skills-dir", "synced", "claude-plugin-test",
    "npm", "pip", "uv", "cargo", "github", "gh",
}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_NAME = KEBAB  # Agent Skills spec: lowercase, digits, single hyphens


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path.relative_to(root)}: file not found")
    except json.JSONDecodeError as e:
        errors.append(f"{path.relative_to(root)}: invalid JSON: {e}")
    return None


def frontmatter_name(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k.strip() == "name":
            return v.strip().strip("'\"")
    return None


market = load_json(root / ".claude-plugin" / "marketplace.json")
if market is not None:
    mname = market.get("name", "")
    if not KEBAB.match(mname):
        errors.append(f"marketplace name {mname!r} is not kebab-case")
    if mname.lower() in RESERVED or mname.startswith("claudeai-"):
        errors.append(f"marketplace name {mname!r} is reserved by Claude Code")

    listed_dirs = set()
    seen_names = set()
    for i, entry in enumerate(market.get("plugins", [])):
        name = entry.get("name")
        source = entry.get("source")
        where = f"plugins[{i}] ({name or '?'})"

        if not name:
            errors.append(f"{where}: missing 'name'")
            continue
        if name in seen_names:
            errors.append(f"{where}: duplicate plugin name")
        seen_names.add(name)
        if not entry.get("description"):
            errors.append(f"{where}: missing 'description'")

        if not isinstance(source, str):
            # Remote sources (github, url, ...) are allowed but not checked here.
            continue
        if not source.startswith("./"):
            errors.append(f"{where}: source {source!r} must start with './'")
        if ".." in Path(source).parts:
            errors.append(f"{where}: source {source!r} must not contain '..'")
            continue

        pdir = (root / source).resolve()
        listed_dirs.add(pdir)
        if not pdir.is_dir():
            errors.append(f"{where}: source directory {source} does not exist")
            continue

        manifest = pdir / ".claude-plugin" / "plugin.json"
        plugin = load_json(manifest)
        if plugin is None:
            continue
        rel = manifest.relative_to(root)
        if plugin.get("name") != name:
            errors.append(
                f"{where}: name does not match {rel} name "
                f"{plugin.get('name')!r} (install fails with "
                "'Plugin not found in marketplace')"
            )
        if not plugin.get("license"):
            errors.append(f"{rel}: missing 'license'")
        if not plugin.get("version"):
            errors.append(f"{rel}: missing 'version'")
        if "version" in entry:
            errors.append(
                f"{where}: set 'version' only in {rel}, not in the "
                "marketplace entry (plugin.json wins silently)"
            )

        skills_dir = pdir / "skills"
        if skills_dir.is_dir():
            for sdir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
                srel = sdir.relative_to(root)
                skill_md = sdir / "SKILL.md"
                if not skill_md.is_file():
                    errors.append(f"{srel}: missing SKILL.md")
                    continue
                sname = frontmatter_name(skill_md)
                if not sname:
                    errors.append(f"{srel}/SKILL.md: missing 'name' in frontmatter")
                    continue
                if not SKILL_NAME.match(sname) or len(sname) > 64:
                    errors.append(
                        f"{srel}/SKILL.md: name {sname!r} must be lowercase "
                        "letters, digits, and single hyphens, max 64 chars"
                    )
                if sname != sdir.name:
                    errors.append(
                        f"{srel}/SKILL.md: name {sname!r} does not match "
                        f"folder name {sdir.name!r}"
                    )

    plugins_root = root / "plugins"
    if plugins_root.is_dir():
        for d in sorted(p for p in plugins_root.iterdir() if p.is_dir()):
            if d.resolve() not in listed_dirs:
                errors.append(
                    f"{d.relative_to(root)}: directory has no entry in marketplace.json"
                )

# Shared skill references are copied per skill so each skill stays
# standalone. Every copy of the same file name must match.
SHARED_REFS = ("BACKENDS.md", "LEDGER.md", "SOURCES.md")
for ref in SHARED_REFS:
    copies = sorted((root / "plugins").glob(f"*/skills/*/references/{ref}"))
    texts = {c: c.read_bytes() for c in copies}
    if len(set(texts.values())) > 1:
        first = copies[0]
        for c in copies[1:]:
            if texts[c] != texts[first]:
                errors.append(
                    f"{c.relative_to(root)} differs from {first.relative_to(root)}; "
                    f"copies of {ref} must be identical"
                )

for e in errors:
    print(f"FAIL: {e}", file=sys.stderr)
if errors:
    sys.exit(1)
print("structural checks passed")
PY

# --- 4: shared skills match their source -------------------------------------
echo
echo "==> shared skills"
for src in shared/skills/*/; do
  [ -d "$src" ] || continue
  skill="$(basename "$src")"
  for domain in code work; do
    dest="plugins/$domain/skills/$skill"
    if [ ! -d "$dest" ]; then
      fail "$dest missing; run scripts/sync-shared.sh"
    elif ! diff -r "${src%/}" "$dest" >/dev/null; then
      fail "$dest differs from shared/skills/$skill; edit shared/skills/ and run scripts/sync-shared.sh"
    fi
  done
done
[ "$failed" -eq 0 ] && echo "shared skills match"

# --- 5: OpenAI configs (ChatGPT and Codex) -----------------------------------
echo
echo "==> OpenAI configs"
python3 -I scripts/build-openai.py --check || failed=1
python3 -I - "$ROOT" <<'PY' || failed=1
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
errors = []
# Top-level rules from https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
# (additionalProperties: false; $schema and name required).
ALLOWED = {"$schema", "name", "version", "description", "author", "homepage",
           "repository", "license", "keywords", "extensions"}
NAME = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")

market = json.loads((root / ".agents/plugins/marketplace.json").read_text())
for entry in market.get("plugins", []):
    where = f".agents/plugins/marketplace.json ({entry.get('name', '?')})"
    for key in ("name", "source", "policy", "category"):
        if key not in entry:
            errors.append(f"{where}: missing {key!r}")
    path = entry.get("source", {}).get("path", "")
    pdir = root / path
    manifest = pdir / "plugin.json"
    if not manifest.is_file():
        errors.append(f"{where}: {path}/plugin.json not found")
        continue
    data = json.loads(manifest.read_text())
    rel = manifest.relative_to(root)
    extra = set(data) - ALLOWED
    if extra:
        errors.append(f"{rel}: keys not allowed by the schema: {sorted(extra)}")
    for key in ("$schema", "name"):
        if key not in data:
            errors.append(f"{rel}: missing {key!r}")
    if not NAME.match(data.get("name", "")) or len(data.get("name", "")) > 64:
        errors.append(f"{rel}: name {data.get('name')!r} fails the schema pattern")
    openai = data.get("extensions", {}).get("com.openai", {})
    skill = openai.get("onboardingSkill")
    if skill and (not skill.startswith("./") or not (pdir / skill).is_file()):
        errors.append(f"{rel}: onboardingSkill {skill!r} must be a ./ path that exists")
    if not (pdir / "skills").is_dir():
        errors.append(f"{rel}: no skills/ directory for ChatGPT and Codex to load")

for e in errors:
    print(f"FAIL: {e}", file=sys.stderr)
if errors:
    sys.exit(1)
print("OpenAI manifests pass schema checks")
PY

# --- 6: skill script tests ---------------------------------------------------
echo
echo "==> skill script tests"
if out="$(python3 -I shared/skills/write/scripts/test_lint.py 2>&1)"; then
  echo "$out" | tail -n 1
else
  echo "$out" >&2
  fail "shared/skills/write/scripts/test_lint.py failed"
fi

echo
if [ "$failed" -ne 0 ]; then
  echo "Validation FAILED" >&2
  exit 1
fi
echo "Validation passed"
