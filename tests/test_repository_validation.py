import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_repository import validate_repository


class RepositoryValidationTests(unittest.TestCase):
    def make_valid_tree(self, root):
        root = Path(root)
        (root / ".codex-plugin").mkdir()
        (root / "skills" / "idea-opportunity-engine").mkdir(parents=True)
        (root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"name": "idea-opportunity-engine", "skills": "./skills/"})
        )
        (root / "skills" / "idea-opportunity-engine" / "SKILL.md").write_text(
            "---\nname: idea-opportunity-engine\ndescription: Use when evaluating opportunities.\n---\n"
        )
        for name in ("evidence-policy.md", "experiment-framework.md", "report-template.md", "scoring-model.md"):
            (root / "skills" / "idea-opportunity-engine" / "references").mkdir(exist_ok=True)
            (root / "skills" / "idea-opportunity-engine" / "references" / name).write_text("reference")
        (root / ".agents" / "plugins").mkdir(parents=True)
        (root / ".agents" / "plugins" / "marketplace.json").write_text("{}")
        (root / "README.md").write_text("documentation")
        (root / "LICENSE").write_text("MIT")
        (root / "install.sh").write_text("#!/bin/sh\n")
        (root / "evals" / "cases").mkdir(parents=True)
        (root / "evals" / "run_harness.py").write_text("harness")
        (root / "scripts").mkdir()
        (root / "scripts" / "security_scan.py").write_text("scanner")

    def test_missing_required_file_is_reported(self):
        """Removing the scoring reference must produce a repository validation error."""
        with tempfile.TemporaryDirectory() as temporary:
            self.make_valid_tree(temporary)
            (Path(temporary) / "skills" / "idea-opportunity-engine" / "references" / "scoring-model.md").unlink()
            errors = validate_repository(Path(temporary))
            self.assertTrue(any("scoring-model.md" in error for error in errors), errors)

    def test_mismatched_plugin_and_skill_names_are_reported(self):
        """Changing the skill frontmatter name must invalidate package identity."""
        with tempfile.TemporaryDirectory() as temporary:
            self.make_valid_tree(temporary)
            skill = Path(temporary) / "skills" / "idea-opportunity-engine" / "SKILL.md"
            skill.write_text("---\nname: a-different-skill\ndescription: Use when evaluating opportunities.\n---\n")
            errors = validate_repository(Path(temporary))
            self.assertTrue(any("does not match" in error for error in errors), errors)

    def test_invalid_marketplace_entry_is_reported(self):
        """Removing the marketplace plugin/source checks must accept this empty manifest."""
        with tempfile.TemporaryDirectory() as temporary:
            self.make_valid_tree(temporary)
            errors = validate_repository(Path(temporary))
            self.assertTrue(any("marketplace" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
