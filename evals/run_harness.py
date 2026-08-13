#!/usr/bin/env python3
"""Validate deterministic eval cases and score saved responses."""

import argparse
import json
import re
import sys
from pathlib import Path


DECISIONS = {"GO", "TEST", "WATCH", "KILL"}
MODES = {"discovery", "validation", "portfolio", "boundary"}
CASE_ID = re.compile(r"^\d{3}$")
DECISION_LABEL = re.compile(
    r"\b(?P<label>verdict|decision)(?:\*\*)?\s*:\s*\**\s*(?P<decision>GO|TEST|WATCH|KILL)\b",
    re.IGNORECASE,
)
CANDIDATE_HEADING = re.compile(r"(?im)^\s*#{1,6}\s+candidate\b.*$")
ANALYSIS_MARKER = re.compile(r"\b(?:verdict|decision|score)\s*:", re.IGNORECASE)
SEMANTIC_ANALYSIS_MARKERS = (
    "evidence ledger",
    "claim ledger",
    "willingness to pay",
    "paid pilot",
    "failure threshold",
    "success threshold",
    "decision card",
    "adjusted score",
    "100-point",
)


def _case_errors(case, path):
    errors = []
    required = {
        "id": str,
        "mode": str,
        "prompt": str,
        "should_trigger": bool,
        "allowed_decisions": list,
        "required_behavior_groups": list,
        "forbidden_phrases": list,
        "semantic_judge_notes": str,
    }
    if not isinstance(case, dict):
        return [f"{path}: case must be a JSON object"]
    for field, kind in required.items():
        if field not in case:
            errors.append(f"{path}: missing required field {field}")
        elif not isinstance(case[field], kind):
            errors.append(f"{path}: {field} must be a {kind.__name__}")
    if errors:
        return errors
    if not CASE_ID.fullmatch(case["id"]):
        errors.append(f"{path}: id must be a unique three-digit string")
    if case["mode"] not in MODES:
        errors.append(f"{path}: unsupported mode {case['mode']!r}")
    if not case["prompt"].strip() or not case["semantic_judge_notes"].strip():
        errors.append(f"{path}: prompt and semantic_judge_notes must be non-empty")
    if not case["should_trigger"] and case["mode"] != "boundary":
        errors.append(f"{path}: non-trigger cases must use boundary mode")
    if case["should_trigger"] and (not case["allowed_decisions"] or not set(case["allowed_decisions"]).issubset(DECISIONS)):
        errors.append(f"{path}: trigger cases need allowed GO/TEST/WATCH/KILL decisions")
    if not case["should_trigger"] and case["allowed_decisions"]:
        errors.append(f"{path}: non-trigger cases cannot allow decisions")
    if not case["required_behavior_groups"] or any(
        not isinstance(group, list) or not group or any(not isinstance(phrase, str) or not phrase.strip() for phrase in group)
        for group in case["required_behavior_groups"]
    ):
        errors.append(f"{path}: required_behavior_groups must contain non-empty phrase groups")
    if any(not isinstance(phrase, str) or not phrase.strip() for phrase in case["forbidden_phrases"]):
        errors.append(f"{path}: forbidden_phrases must contain non-empty strings")
    return errors


def validate_cases(case_dir):
    """Return the ten well-formed shipped cases or raise ValueError with all errors."""
    case_dir = Path(case_dir)
    errors = []
    cases = []
    for path in sorted(case_dir.glob("*.json")):
        try:
            case = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: invalid JSON ({error})")
            continue
        errors.extend(_case_errors(case, path))
        cases.append(case)
    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(cases) != 10:
        errors.append(f"{case_dir}: expected exactly 10 cases, found {len(cases)}")
    if len(ids) != len(set(ids)):
        errors.append(f"{case_dir}: case IDs must be unique")
    if not errors and set(ids) != {f"{number:03d}" for number in range(1, 11)}:
        errors.append(f"{case_dir}: case IDs must be 001 through 010")
    if errors:
        raise ValueError("\n".join(errors))
    return sorted(cases, key=lambda case: case["id"])


def score_response(case, text):
    """Score only observable response rules; semantic quality still needs a human/LLM judge."""
    normalized = text.lower()
    failures = []
    if not case["should_trigger"]:
        semantic_marker_count = sum(marker in normalized for marker in SEMANTIC_ANALYSIS_MARKERS)
        if ANALYSIS_MARKER.search(text) or semantic_marker_count >= 2:
            failures.append("case must not trigger an opportunity analysis")
    else:
        matches = list(DECISION_LABEL.finditer(text))
        decisions = [match.group("decision").upper() for match in matches]
        if not matches:
            failures.append("response must state a labeled GO/TEST/WATCH/KILL decision")
        elif not set(decisions).issubset(set(case["allowed_decisions"])):
            failures.append("response decision is not allowed for this case")
        elif case["mode"] == "validation" and len(matches) != 1:
            failures.append("response must state exactly one labeled decision")
        elif case["mode"] in {"discovery", "portfolio"}:
            headings = list(CANDIDATE_HEADING.finditer(text))
            if headings:
                candidate_match_ranges = []
                for index, heading in enumerate(headings):
                    end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
                    candidate_matches = list(DECISION_LABEL.finditer(text, heading.end(), end))
                    candidate_match_ranges.extend((match.start(), match.end()) for match in candidate_matches)
                    if len(candidate_matches) != 1:
                        failures.append("each candidate must state exactly one labeled decision")
                for match in matches:
                    in_candidate = any(start <= match.start() < end for start, end in candidate_match_ranges)
                    if match.group("label").lower() == "decision" and not in_candidate:
                        failures.append("candidate decisions must appear under a candidate heading")
                        break
    for group in case["required_behavior_groups"]:
        if not any(phrase.lower() in normalized for phrase in group):
            failures.append(f"missing required behavior group: {' | '.join(group)}")
    for phrase in case["forbidden_phrases"]:
        if phrase.lower() in normalized:
            failures.append(f"forbidden phrase present: {phrase}")
    return {"passed": not failures, "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-cases", action="store_true", help="validate the ten shipped JSON cases")
    parser.add_argument("--responses-dir", type=Path, help="score <id>.txt response fixtures")
    arguments = parser.parse_args(argv)
    if not arguments.validate_cases and arguments.responses_dir is None:
        parser.error("choose --validate-cases or --responses-dir")
    cases = validate_cases(Path(__file__).with_name("cases"))
    if arguments.validate_cases:
        print(f"Valid cases: {len(cases)}")
    if arguments.responses_dir is not None:
        failures = 0
        for case in cases:
            response_path = arguments.responses_dir / f"{case['id']}.txt"
            if not response_path.is_file():
                print(f"{case['id']}: FAIL missing response fixture")
                failures += 1
                continue
            result = score_response(case, response_path.read_text(encoding="utf-8"))
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{case['id']}: {status}" + (f" — {'; '.join(result['failures'])}" if result["failures"] else ""))
            failures += not result["passed"]
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
