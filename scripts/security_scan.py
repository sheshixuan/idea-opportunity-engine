#!/usr/bin/env python3
"""Scan repository text files for common credential and private-data patterns."""

import argparse
import re
import sys
from pathlib import Path


CREDENTIAL_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _is_public_documentation(relative):
    return relative == Path("README.md") or relative.parts[:1] == ("docs",)


def scan_paths(paths, root):
    """Return findings for supplied files, allowing email addresses only in public documentation."""
    root = Path(root).resolve()
    issues = []
    for path in paths:
        path = Path(path)
        try:
            relative = path.resolve().relative_to(root)
        except ValueError:
            relative = path
        display = relative.as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append(f"{display}: could not scan as UTF-8 text")
            continue
        except OSError:
            continue
        if any(pattern.search(content) for pattern in CREDENTIAL_PATTERNS):
            issues.append(f"{display}: credential-like value detected")
        if PRIVATE_KEY.search(content):
            issues.append(f"{display}: private key marker detected")
        if not _is_public_documentation(relative) and EMAIL.search(content):
            issues.append(f"{display}: email-like value outside allowed public documentation")
    return issues


def repository_files(root):
    """Yield files intended for release, excluding Git internals and local task artifacts."""
    ignored_parts = {".git", ".superpowers", "__pycache__"}
    for path in root.rglob("*"):
        if path.is_file() and not any(part in ignored_parts for part in path.relative_to(root).parts):
            yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    issues = scan_paths(repository_files(root), root)
    if issues:
        print("Security scan failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("Security scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
