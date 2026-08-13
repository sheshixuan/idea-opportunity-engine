#!/usr/bin/env python3
"""Validate the required standalone-skill package structure without third-party libraries."""

import argparse
import json
import re
import sys
from pathlib import Path


SKILL_NAME = "idea-opportunity-engine"
PLUGIN_VERSION = "0.1.0"
PUBLIC_TARGET = "https://github.com/sheshixuan/idea-opportunity-engine"
REFERENCE_FILES = {
    "evidence-policy.md",
    "experiment-framework.md",
    "report-template.md",
    "scoring-model.md",
}
REQUIRED_PATHS = (
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "README.md",
    "LICENSE",
    "install.sh",
    "evals/run_harness.py",
    "scripts/security_scan.py",
    f"skills/{SKILL_NAME}/SKILL.md",
    f"skills/{SKILL_NAME}/agents/openai.yaml",
    f"skills/{SKILL_NAME}/references/evidence-policy.md",
    f"skills/{SKILL_NAME}/references/experiment-framework.md",
    f"skills/{SKILL_NAME}/references/report-template.md",
    f"skills/{SKILL_NAME}/references/scoring-model.md",
)
NAME_LINE = re.compile(r"^name:\s*([^\s#]+)\s*$", re.MULTILINE)


def _skill_name(path):
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        return None, str(error)
    if not content.startswith("---\n"):
        return None, "missing YAML frontmatter"
    frontmatter = content.split("---", 2)[1]
    match = NAME_LINE.search(frontmatter)
    if not match:
        return None, "frontmatter has no name"
    return match.group(1).strip('"\''), None


def validate_repository(root):
    """Return package-structure errors; an empty list means the repository is valid."""
    root = Path(root)
    errors = []
    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    plugin_path = root / ".codex-plugin" / "plugin.json"
    plugin = None
    if plugin_path.is_file():
        try:
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid plugin manifest: {error}")
        else:
            if plugin.get("name") != SKILL_NAME:
                errors.append(f"plugin name {plugin.get('name')!r} does not match {SKILL_NAME!r}")
            if plugin.get("skills") != "./skills/":
                errors.append("plugin skills path must be './skills/'")
            if plugin.get("version") != PLUGIN_VERSION:
                errors.append(f"plugin version must be {PLUGIN_VERSION!r}")
            if plugin.get("license") != "MIT":
                errors.append("plugin license must be 'MIT'")
            if plugin.get("homepage") != PUBLIC_TARGET:
                errors.append(f"plugin homepage must be {PUBLIC_TARGET!r}")
            if plugin.get("repository") != PUBLIC_TARGET:
                errors.append(f"plugin repository must be {PUBLIC_TARGET!r}")

    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if marketplace_path.is_file():
        try:
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid marketplace manifest: {error}")
        else:
            entries = marketplace.get("plugins") if isinstance(marketplace, dict) else None
            expected_entry = {
                "name": SKILL_NAME,
                "source": {"source": "local", "path": "./"},
            }
            if not isinstance(entries, list) or not any(
                isinstance(entry, dict)
                and entry.get("name") == expected_entry["name"]
                and entry.get("source") == expected_entry["source"]
                for entry in entries
            ):
                errors.append("marketplace manifest must expose idea-opportunity-engine at './'")

    skill_path = root / "skills" / SKILL_NAME / "SKILL.md"
    if skill_path.is_file():
        skill_name, problem = _skill_name(skill_path)
        if problem:
            errors.append(f"invalid SKILL.md: {problem}")
        elif skill_name != SKILL_NAME:
            errors.append(f"skill name {skill_name!r} does not match plugin name {SKILL_NAME!r}")
    references_path = root / "skills" / SKILL_NAME / "references"
    if references_path.is_dir():
        entries = list(references_path.iterdir())
        actual_references = {entry.name for entry in entries if entry.is_file()}
        if actual_references != REFERENCE_FILES or any(not entry.is_file() for entry in entries):
            errors.append("reference directory must contain exactly the four approved Markdown reference files")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args(argv)
    errors = validate_repository(arguments.root)
    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
