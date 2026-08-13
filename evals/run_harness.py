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
    r"\b(?P<label>verdict|decision)(?:\*\*)?\s*:\s*[\*`]*\s*(?P<decision>GO|TEST|WATCH|KILL)\b",
    re.IGNORECASE,
)
CANDIDATE_HEADING = re.compile(
    r"(?im)^\s*#{1,6}\s+candidate(?:\s*:\s*|\s+)(?P<name>.+?)\s*$"
)
ADJUSTED_SCORE = re.compile(
    r"\badjusted score(?:\*\*)?\s*:\s*[\*`]*(?P<score>100|[1-9]?\d)\s*/\s*100\b",
    re.IGNORECASE,
)
LEAD_VERDICT = re.compile(
    r"^\s*(?:\*\*)?verdict(?:\*\*)?\s*:\s*[\*`]*(?P<decision>GO|TEST|WATCH|KILL)\b[\*`]*"
    r"\s+[—-]\s+(?:lead|portfolio lead)\s*:\s*(?P<lead>[^.\n]+)",
    re.IGNORECASE,
)
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
    "target user",
    "alternatives",
    "experiment",
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


def _candidate_table(text):
    """Return structured candidate rows and table offset, or None."""
    lines = text.splitlines()
    offset = 0
    for index, line in enumerate(lines[:-1]):
        if "|" not in line:
            offset += len(line) + 1
            continue
        header = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        name_header = next((name for name in ("candidate", "opportunity") if name in header), None)
        if name_header is None or "adjusted score" not in header or "decision" not in header:
            offset += len(line) + 1
            continue
        divider = [cell.strip() for cell in lines[index + 1].strip().strip("|").split("|")]
        if len(divider) != len(header) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in divider):
            offset += len(line) + 1
            continue
        rows = []
        for row in lines[index + 2 :]:
            if "|" not in row:
                break
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) != len(header):
                break
            rows.append(
                {
                    "name": cells[header.index(name_header)],
                    "score": cells[header.index("adjusted score")],
                    "decision": cells[header.index("decision")],
                }
            )
        return rows, offset
    return None


def _expected_decision(score):
    if score >= 90:
        return "GO"
    if score >= 70:
        return "TEST"
    if score >= 50:
        return "WATCH"
    return "KILL"


def _parse_score(value):
    match = re.fullmatch(r"\s*[\*`]*(100|[1-9]?\d)\s*/\s*100[\*`]*\s*", value)
    return int(match.group(1)) if match else None


def _plain_name(value):
    return " ".join(re.sub(r"[\*`_]", "", value).strip().lower().split())


def _score_decision_failure(score, decision, subject):
    expected = _expected_decision(score)
    if decision != expected:
        return f"{subject} adjusted score {score}/100 maps to {expected}, not {decision}"
    return None


def score_response(case, text):
    """Score only observable response rules; semantic quality still needs a human/LLM judge."""
    normalized = text.lower().translate(str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-"}))
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
        elif case["mode"] == "validation":
            scores = list(ADJUSTED_SCORE.finditer(text))
            if len(scores) != 1:
                failures.append("validation response must state exactly one adjusted score")
            else:
                failure = _score_decision_failure(
                    int(scores[0].group("score")), decisions[0], "validation verdict"
                )
                if failure:
                    failures.append(failure)
        elif case["mode"] in {"discovery", "portfolio"}:
            headings = list(CANDIDATE_HEADING.finditer(text))
            table = _candidate_table(text)
            table_rows = table[0] if table is not None else None
            verdicts = [match for match in matches if match.group("label").lower() == "verdict"]
            lead_match = LEAD_VERDICT.match(text)
            if len(verdicts) != 1:
                failures.append("response must state exactly one overall verdict")
            elif matches[0] is not verdicts[0]:
                failures.append("overall verdict must be the first labeled decision")
            if lead_match is None:
                failures.append("overall verdict must name one explicit lead candidate")
            lead_name = _plain_name(lead_match.group("lead")) if lead_match else None
            lead_decision = lead_match.group("decision").upper() if lead_match else None
            candidates = []
            if headings:
                if table_rows is not None:
                    failures.append("response must use either candidate headings or a candidate decision table")
                candidate_match_ranges = []
                for index, heading in enumerate(headings):
                    end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
                    candidate_matches = list(DECISION_LABEL.finditer(text, heading.end(), end))
                    candidate_scores = list(ADJUSTED_SCORE.finditer(text, heading.end(), end))
                    candidate_match_ranges.extend((match.start(), match.end()) for match in candidate_matches)
                    if len(candidate_matches) != 1:
                        failures.append("each candidate must state exactly one labeled decision")
                    if len(candidate_scores) != 1:
                        failures.append("each candidate must state exactly one adjusted score")
                    if len(candidate_matches) == 1 and len(candidate_scores) == 1:
                        decision = candidate_matches[0].group("decision").upper()
                        score = int(candidate_scores[0].group("score"))
                        candidates.append((_plain_name(heading.group("name")), decision))
                        failure = _score_decision_failure(score, decision, f"candidate {heading.group('name')}")
                        if failure:
                            failures.append(failure)
                for match in matches:
                    in_candidate = any(start <= match.start() < end for start, end in candidate_match_ranges)
                    if match.group("label").lower() == "decision" and not in_candidate:
                        failures.append("candidate decisions must appear under a candidate heading")
                        break
                if verdicts and verdicts[0].start() >= headings[0].start():
                    failures.append("candidate sections must not contain a Verdict label")
            elif table_rows is not None:
                if verdicts and verdicts[0].start() >= table[1]:
                    failures.append("overall verdict must appear before the candidate decision table")
                if not table_rows:
                    failures.append("candidate decision table must contain at least one candidate row")
                for row in table_rows:
                    decision = re.fullmatch(r"\s*[\*`]*(GO|TEST|WATCH|KILL)[\*`]*\s*", row["decision"], re.IGNORECASE)
                    if not decision:
                        failures.append("each candidate decision table row must contain exactly one decision")
                        continue
                    decision_value = decision.group(1).upper()
                    if decision_value not in case["allowed_decisions"]:
                        failures.append("response decision is not allowed for this case")
                    score = _parse_score(row["score"])
                    if score is None:
                        failures.append("each candidate decision table row must contain one adjusted score out of 100")
                        continue
                    candidates.append((_plain_name(row["name"]), decision_value))
                    failure = _score_decision_failure(score, decision_value, f"candidate {row['name']}")
                    if failure:
                        failures.append(failure)
                if any(match.group("label").lower() == "decision" for match in matches):
                    failures.append("candidate decisions must use the decision table cells")
            else:
                failures.append("discovery or portfolio response must use candidate headings or a candidate table")
            if lead_name is not None:
                lead_candidates = [decision for name, decision in candidates if name == lead_name]
                if len(lead_candidates) != 1:
                    failures.append("named lead must identify exactly one candidate")
                elif lead_candidates[0] != lead_decision:
                    failures.append("overall verdict must equal the named lead candidate decision")
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
