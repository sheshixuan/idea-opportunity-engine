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

    def test_validation_accepts_markdown_verdict_and_requires_one_decision(self):
        """Breaking Markdown verdict parsing or one-validation-decision enforcement must fail here."""
        case = validate_cases(CASES)[0]
        response = (
            "**Verdict:** TEST. Evidence, contradiction, and unknowns are explicit. Alternatives include doing nothing. "
            "Willingness to pay is unproven. Score: 58/100. Experiment has a failure threshold."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_validation_accepts_inline_code_decision(self):
        """A clearly labeled decision must not fail only because Markdown renders it as code."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: `KILL` the broad idea. Evidence, contradiction, and unknowns are explicit. "
            "Alternatives include doing nothing. Willingness to pay is unproven. "
            "Score: 10/100. Experiment has a failure threshold."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_accepts_one_valid_decision_per_candidate(self):
        """Rejecting multi-candidate discovery or losing candidate decisions must fail this contract."""
        case = validate_cases(CASES)[1]
        response = (
            "**Verdict:** TEST the accessibility lead.\n"
            "Target user: small ecommerce teams. Accessibility is the market change. "
            "Alternatives and willingness to pay are unknown. Experiment: test a paid offer.\n"
            "## Candidate A: remediation audit\n**Decision:** TEST\n"
            "## Candidate B: training service\n**Decision:** WATCH"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_rejects_conflicting_candidate_decisions(self):
        """Adding a second decision under one candidate must fail rather than be silently accepted."""
        case = validate_cases(CASES)[1]
        response = (
            "**Verdict:** TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n## Candidate A\n**Decision:** TEST\n**Decision:** WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("candidate" in failure for failure in result["failures"]))

    def test_discovery_rejects_unstructured_conflicting_decisions(self):
        """Ambiguous candidate prose without headings or a table must not hide conflicting labels."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer. Candidate A: Decision: TEST. Decision: WATCH."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("unstructured" in failure for failure in result["failures"]))

    def test_discovery_accepts_one_decision_per_candidate_table_row(self):
        """Breaking decision-table parsing must reject this two-candidate discovery response."""
        case = validate_cases(CASES)[1]
        response = (
            "**Verdict:** TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Decision |\n| --- | --- |\n"
            "| remediation audit | TEST |\n| training service | WATCH |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_accepts_inline_code_decisions_in_table(self):
        """Markdown code styling around exact decision cells must preserve their meaning."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: `TEST` the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Decision |\n| --- | --- |\n"
            "| remediation audit | `TEST` |\n| training service | `WATCH` |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_common_unicode_hyphen_preserves_constraint_match(self):
        """Typography must not hide an otherwise explicit 30-day constraint from scoring."""
        case = validate_cases(CASES)[5]
        response = (
            "Verdict: TEST the lead. A two-person team can run a 30‑day experiment within a $2,000 budget. "
            "The cost is capped and the success threshold is two deposits."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_rejects_decision_label_before_candidate_table(self):
        """An overall Decision before a valid table must not supplement the lead Verdict."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead.\nDecision: WATCH\n"
            "Target user: small ecommerce teams. Accessibility is the market change. "
            "Alternatives and willingness to pay are unknown. Experiment: test a paid offer.\n"
            "| Opportunity | Decision |\n| --- | --- |\n"
            "| remediation audit | TEST |\n| training service | WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("decision table cells" in failure for failure in result["failures"]))

    def test_portfolio_rejects_decision_label_after_candidate_table(self):
        """An overall Decision after a valid table must not add another labeled decision."""
        case = validate_cases(CASES)[8]
        response = (
            "Verdict: TEST the renewal-backed opportunity. Conflicting survey evidence is weaker "
            "than paid renewal behavior. Confidence: medium. Score: 72. Experiment: expand the paid pilot.\n"
            "| Opportunity | Decision |\n| --- | --- |\n"
            "| survey-backed concept | WATCH |\n| renewal-backed concept | TEST |\n"
            "Decision: WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("decision table cells" in failure for failure in result["failures"]))

    def test_discovery_rejects_verdict_inside_candidate_table(self):
        """A Verdict in a candidate row must not masquerade as table commentary."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Decision | Notes |\n| --- | --- | --- |\n"
            "| remediation audit | TEST | Verdict: WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overall verdict" in failure for failure in result["failures"]))

    def test_discovery_rejects_conflicting_decision_table_row(self):
        """A table row with two decision cells must fail instead of being treated as one candidate decision."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Decision |\n| --- | --- |\n"
            "| remediation audit | TEST / WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("table row" in failure for failure in result["failures"]))

    def test_discovery_rejects_multiple_verdicts_with_candidate_headings(self):
        """A second overall Verdict in a heading response must not be mistaken for a candidate decision."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n## Candidate A\nDecision: TEST\nVerdict: WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overall verdict" in failure for failure in result["failures"]))

    def test_discovery_rejects_multiple_verdicts_with_candidate_table(self):
        """A table must not allow a contradictory second lead Verdict after its rows."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n| Opportunity | Decision |\n| --- | --- |\n"
            "| remediation audit | TEST |\nVerdict: WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overall verdict" in failure for failure in result["failures"]))

    def test_discovery_requires_lead_verdict_before_candidate_decisions(self):
        """A Verdict after candidate labels violates the verdict-first report contract."""
        case = validate_cases(CASES)[1]
        response = (
            "Target user: small ecommerce teams. Accessibility is the market change. "
            "Alternatives and willingness to pay are unknown. Experiment: test a paid offer.\n"
            "## Candidate A\nDecision: TEST\nVerdict: TEST the accessibility lead."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("first labeled decision" in failure for failure in result["failures"]))

    def test_discovery_accepts_lead_first_unstructured_verdict(self):
        """A single lead-first Verdict remains valid when no candidate structure is used."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST the accessibility lead. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_sql_boundary_rejects_opportunity_analysis(self):
        """Giving a SQL request a GO/TEST/WATCH/KILL analysis must fail the boundary case."""
        case = validate_cases(CASES)[-1]
        analysis = "Verdict: TEST. Score: 65/100. Run a paid pilot for this SQL query."
        result = score_response(case, analysis)
        self.assertFalse(result["passed"])
        self.assertTrue(any("must not trigger" in failure for failure in result["failures"]))

        boundary_response = "SELECT plan_tier, COUNT(DISTINCT user_id) FROM events GROUP BY plan_tier;"
        self.assertTrue(score_response(case, boundary_response)["passed"])

    def test_sql_boundary_rejects_unlabeled_analysis_with_boundary_language(self):
        """Removing broad analysis markers would let this disguised opportunity analysis pass."""
        case = validate_cases(CASES)[-1]
        response = (
            "This is outside the opportunity-analysis boundary, but here is an evidence ledger, "
            "alternatives, willingness to pay, and a paid pilot experiment."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("must not trigger" in failure for failure in result["failures"]))

    def test_sql_boundary_rejects_unlabeled_target_user_analysis(self):
        """Missing common report markers would let this boundary-disguised analysis pass."""
        case = validate_cases(CASES)[-1]
        response = (
            "This is outside the opportunity-analysis boundary, but the target user is finance, "
            "alternatives are spreadsheets, and the experiment is a concierge test."
        )
        self.assertFalse(score_response(case, response)["passed"])


if __name__ == "__main__":
    unittest.main()
