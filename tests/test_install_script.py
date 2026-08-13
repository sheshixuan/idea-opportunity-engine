import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
SOURCE_SKILL = ROOT / "skills" / "idea-opportunity-engine"


class InstallScriptTests(unittest.TestCase):
    def run_installer(self, destination, *arguments):
        environment = os.environ.copy()
        environment.pop("CODEX_HOME", None)
        return subprocess.run(
            [str(INSTALLER), *arguments, "--dest", str(destination)],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_fresh_install_copies_only_nested_skill(self):
        """Removing the copy step must leave the exact skill destination absent."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            result = self.run_installer(destination, "install")
            installed = destination / "idea-opportunity-engine"
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertFalse((installed / "idea-opportunity-engine").exists())
            self.assertEqual((SOURCE_SKILL / "SKILL.md").read_text(), (installed / "SKILL.md").read_text())

    def test_install_refuses_existing_destination(self):
        """Removing the existing-destination guard must overwrite this sentinel."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            sentinel = installed / "sentinel.txt"
            sentinel.write_text("keep me")
            result = self.run_installer(destination, "install")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Refusing to overwrite", result.stderr)
            self.assertEqual("keep me", sentinel.read_text())

    def test_update_replaces_existing_skill(self):
        """Removing staged replacement must leave this old marker behind."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("old skill")
            result = self.run_installer(destination, "--update")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual((SOURCE_SKILL / "SKILL.md").read_text(), (installed / "SKILL.md").read_text())
            self.assertFalse((installed / "idea-opportunity-engine").exists())

    def test_dry_run_makes_no_writes(self):
        """Removing dry-run handling must create this destination directory."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "not-created"
            result = self.run_installer(destination, "install", "--dry-run")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Dry run", result.stdout)
            self.assertFalse(destination.exists())

    def test_dry_run_update_requires_an_existing_skill(self):
        """Skipping update preconditions in dry-run would claim an impossible update succeeds."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "not-created"
            result = self.run_installer(destination, "--update", "--dry-run")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("No installed skill", result.stderr)
            self.assertFalse(destination.exists())

    def test_uninstall_removes_only_exact_skill_destination(self):
        """Broad deletion would remove the sibling sentinel and must be caught."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("installed")
            sibling = destination / "another-skill"
            sibling.mkdir()
            (sibling / "sentinel.txt").write_text("keep")
            result = self.run_installer(destination, "--uninstall")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(installed.exists())
            self.assertEqual("keep", (sibling / "sentinel.txt").read_text())

    def test_destination_override_is_used(self):
        """Ignoring --dest would write outside this isolated test location."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "custom destination"
            result = self.run_installer(destination, "install")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((destination / "idea-opportunity-engine" / "SKILL.md").is_file())

    def test_interrupt_after_backup_preserves_recovery_copy(self):
        """Deleting the stage on TERM after backup move would lose the only installed copy."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("old skill")
            fake_bin = Path(temporary) / "fake-bin"
            fake_bin.mkdir()
            fake_mv = fake_bin / "mv"
            fake_mv.write_text(
                "#!/bin/sh\n"
                "/bin/mv \"$@\"\n"
                "case \"$2\" in\n"
                "  */previous) kill -TERM \"$PPID\" ;;\n"
                "esac\n"
            )
            fake_mv.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            result = subprocess.run(
                [str(INSTALLER), "--update", "--dest", str(destination)],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            recovery_dirs = list(destination.glob(".idea-opportunity-engine-install.*"))
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(installed.exists())
            self.assertEqual(1, len(recovery_dirs), result.stderr)
            self.assertEqual("old skill", (recovery_dirs[0] / "previous" / "SKILL.md").read_text())

    def test_interrupt_before_backup_keeps_existing_install_without_false_recovery_claim(self):
        """A pre-move signal must not claim that a nonexistent previous backup is recoverable."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("old skill")
            fake_bin = Path(temporary) / "fake-bin"
            fake_bin.mkdir()
            fake_mv = fake_bin / "mv"
            fake_mv.write_text(
                "#!/bin/sh\n"
                "case \"$2\" in\n"
                "  */previous) kill -TERM \"$PPID\"; exit 143 ;;\n"
                "esac\n"
                "/bin/mv \"$@\"\n"
            )
            fake_mv.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            result = subprocess.run(
                [str(INSTALLER), "--update", "--dest", str(destination)],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("old skill", (installed / "SKILL.md").read_text())
            self.assertIn("existing install remains", result.stderr)
            self.assertNotIn("Recovery copy retained", result.stderr)
            self.assertEqual([], list(destination.glob(".idea-opportunity-engine-install.*")))

    def test_interrupt_during_fresh_install_does_not_claim_update_or_retain_staging(self):
        """A fresh-install signal must not invent an update recovery state."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            fake_bin = Path(temporary) / "fake-bin"
            fake_bin.mkdir()
            fake_cp = fake_bin / "cp"
            fake_cp.write_text(
                "#!/bin/sh\n"
                "/bin/cp \"$@\"\n"
                "kill -TERM \"$PPID\"\n"
            )
            fake_cp.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            result = subprocess.run(
                [str(INSTALLER), "install", "--dest", str(destination)],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Install interrupted", result.stderr)
            self.assertNotIn("Update interrupted", result.stderr)
            self.assertEqual([], list(destination.glob(".idea-opportunity-engine-install.*")))

    def test_failed_staged_install_and_removal_failure_preserve_backup(self):
        """An rm failure after backup movement must not let EXIT cleanup destroy recovery."""
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installed = destination / "idea-opportunity-engine"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text("old skill")
            fake_bin = Path(temporary) / "fake-bin"
            fake_bin.mkdir()
            (fake_bin / "mv").write_text(
                "#!/bin/sh\n"
                "case \"$2\" in\n"
                "  */idea-opportunity-engine) case \"$1\" in */.idea-opportunity-engine-install.*/*) exit 1 ;; esac ;;\n"
                "esac\n"
                "/bin/mv \"$@\"\n"
            )
            (fake_bin / "rm").write_text(
                "#!/bin/sh\n"
                "for argument in \"$@\"; do\n"
                "  case \"$argument\" in */skills/idea-opportunity-engine) exit 1 ;; esac\n"
                "done\n"
                "/bin/rm \"$@\"\n"
            )
            for command in fake_bin.iterdir():
                command.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            result = subprocess.run(
                [str(INSTALLER), "--update", "--dest", str(destination)],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            recovery_dirs = list(destination.glob(".idea-opportunity-engine-install.*"))
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(1, len(recovery_dirs), result.stderr)
            self.assertEqual("old skill", (recovery_dirs[0] / "previous" / "SKILL.md").read_text())
            self.assertIn("Recovery copy retained", result.stderr)


if __name__ == "__main__":
    unittest.main()
