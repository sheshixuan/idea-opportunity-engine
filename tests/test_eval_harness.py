import json
import tempfile
import unittest
from pathlib import Path

from evals.run_harness import score_response, validate_cases


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"


class EvalHarnessTests(unittest.TestCase):
    def test_rejects_case_missing_required_behavior_groups(self):
        """Removing required behavior groups must invalidate a malformed case."""
        with tempfile.TemporaryDirectory() as temporary:
            case = {
                "id": "001",
                "mode": "validation",
                "prompt": "Evaluate this idea.",
                "should_trigger": True,
                "allowed_decisions": ["TEST"],
                "forbidden_phrases": [],
                "semantic_judge_notes": "Judge the evidence quality.",
            }
            (Path(temporary) / "001-bad.json").write_text(json.dumps(case))
            with self.assertRaises(ValueError):
                validate_cases(Path(temporary))

    def test_exactly_ten_shipped_cases_are_valid(self):
        """Removing or duplicating a shipped eval case must fail release validation."""
        cases = validate_cases(CASES)
        self.assertEqual(10, len(cases))
        self.assertEqual([f"{number:03d}" for number in range(1, 11)], [case["id"] for case in cases])

    def test_compliant_response_passes(self):
        """Dropping any required group from this response must make scoring fail."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: TEST the workflow handoff idea.\n"
            "Evidence: two teams reported missed handoffs.\n"
            "Contradiction: the sample may be unusually frustrated.\n"
            "Unknown: whether a buyer will pay.\n"
            "Alternatives include spreadsheets and doing nothing.\n"
            "Willingness to pay is unproven.\n"
            "Score: 58/100; confidence: low.\n"
            "Experiment: ask 10 qualified teams for a paid pilot; promote to GO if 3 pay, otherwise KILL."
        )
        result = score_response(case, response)
        self.assertTrue(result["passed"], result["failures"])

    def test_missing_required_behavior_fails(self):
        """A response without alternatives must not satisfy the confirmation-bias case."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: TEST the workflow handoff idea. Evidence is limited. "
            "Unknown: willingness to pay. Score: 58/100. "
            "Experiment: run a paid pilot with a failure threshold."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("required behavior group" in failure for failure in result["failures"]))

    def test_forbidden_behavior_fails(self):
        """Adding the forbidden certainty claim must make the case fail."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: TEST. Evidence and unknowns are explicit. Alternatives include doing nothing. "
            "Willingness to pay is unproven. Score: 58/100. Experiment has a failure threshold. "
            "This is guaranteed to succeed."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("forbidden phrase" in failure for failure in result["failures"]))

    def test_wrong_decision_fails(self):
        """Changing TEST to GO must violate the case decision contract."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: GO. Evidence and unknowns are explicit. Alternatives include doing nothing. "
            "Willingness to pay is unproven. Score: 58/100. Experiment has a failure threshold."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("decision" in failure for failure in result["failures"]))

    def test_conflicting_labeled_decisions_fail(self):
        """Adding a second decision label must violate the one-decision contract."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: TEST. Decision: WATCH. Evidence and unknowns are explicit. "
            "Alternatives include doing nothing. Willingness to pay is unproven. "
            "Score: 58/100. Experiment has a failure threshold."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exactly one" in failure for failure in result["failures"]))

    def test_sql_boundary_rejects_opportunity_analysis(self):
        """Giving a SQL request a GO/TEST/WATCH/KILL analysis must fail the boundary case."""
        case = validate_cases(CASES)[-1]
        analysis = "Verdict: TEST. Score: 65/100. Run a paid pilot for this SQL query."
        result = score_response(case, analysis)
        self.assertFalse(result["passed"])
        self.assertTrue(any("must not trigger" in failure for failure in result["failures"]))

        boundary_response = "Go ahead and run this SQL query; it is outside the opportunity-analysis boundary."
        self.assertTrue(score_response(case, boundary_response)["passed"])


if __name__ == "__main__":
    unittest.main()
