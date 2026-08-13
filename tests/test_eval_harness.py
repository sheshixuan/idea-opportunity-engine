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
            "Verdict: TEST — test the workflow handoff idea.\n"
            "Evidence: two teams reported missed handoffs.\n"
            "Contradiction: the sample may be unusually frustrated.\n"
            "Unknown: whether a buyer will pay.\n"
            "Alternatives include spreadsheets and doing nothing.\n"
            "Willingness to pay is unproven.\n"
            "Adjusted score: 75/100; confidence: low.\n"
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
            "Willingness to pay is unproven. Adjusted score: 75/100. Experiment has a failure threshold."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_validation_accepts_inline_code_decision(self):
        """A clearly labeled decision must not fail only because Markdown renders it as code."""
        case = validate_cases(CASES)[0]
        response = (
            "Verdict: `KILL` the broad idea. Evidence, contradiction, and unknowns are explicit. "
            "Alternatives include doing nothing. Willingness to pay is unproven. "
            "Adjusted score: 10/100. Experiment has a failure threshold."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_validation_rejects_adjusted_score_that_conflicts_with_verdict(self):
        """The real 008 pattern must fail when adjusted 0/100 is labeled TEST."""
        case = validate_cases(CASES)[7]
        response = (
            "Verdict: TEST — test price sensitivity. Price and willingness to pay are unknown. "
            "Alternatives exist. Adjusted score: 0/100. Experiment: run a price test. "
            "Success threshold: 3 deposits. Failure threshold: fewer than 2."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("adjusted score" in failure for failure in result["failures"]), result["failures"])

    def test_validation_accepts_matching_adjusted_score_and_verdict(self):
        """A validation verdict must pass when its sole adjusted score maps to that decision."""
        case = validate_cases(CASES)[7]
        response = (
            "Verdict: TEST — test price sensitivity. Price and willingness to pay are unknown. "
            "Alternatives exist. Adjusted score: 75/100. Experiment: run a price test. "
            "Success threshold: 3 deposits. Failure threshold: fewer than 2."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_validation_accepts_matching_decision_card_table_score(self):
        """The real 004 decision-card table must expose its sole adjusted score to the mapping gate."""
        case = validate_cases(CASES)[3]
        response = (
            "Verdict: KILL — retention and payer evidence are weak. Retention is low. "
            "Alternatives and payer evidence are explicit.\n"
            "| Field | Assessment |\n| --- | --- |\n| Adjusted score | 0/100 |\n"
            "Experiment: run a payment test with a decision rule."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_plural_switching_costs_satisfies_alternative_analysis(self):
        """The real 007 wording must not fail only because it uses the natural plural form."""
        case = validate_cases(CASES)[6]
        response = (
            "Verdict: KILL — evidence is weak. Adjusted score: 41/100. Alternatives include spreadsheets, "
            "phone calls, manual work, and doing nothing. Existing suites raise switching and integration costs. "
            "Experiment: run a paid pilot."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_adoption_friction_and_do_nothing_satisfy_alternative_analysis(self):
        """The real final 007 wording genuinely covers status quo and switching friction."""
        case = validate_cases(CASES)[6]
        response = (
            "Verdict: KILL — evidence is weak. Adjusted score: 26/100. Alternatives include spreadsheets, "
            "phone calls, manual work, and **Do nothing**. A separate layer adds adoption, data-entry, "
            "and contractor-compliance costs; switching authority is unknown. Experiment: run a paid pilot."
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_accepts_one_valid_decision_per_candidate(self):
        """Rejecting multi-candidate discovery or losing candidate decisions must fail this contract."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit.\n"
            "Target user: small ecommerce teams. Accessibility is the market change. "
            "Alternatives and willingness to pay are unknown. Experiment: test a paid offer.\n"
            "## Candidate: remediation audit\nAdjusted score: 75/100\n**Decision:** TEST\n"
            "## Candidate: training service\nAdjusted score: 55/100\n**Decision:** WATCH"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_rejects_conflicting_candidate_decisions(self):
        """Adding a second decision under one candidate must fail rather than be silently accepted."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n## Candidate: remediation audit\nAdjusted score: 75/100\n**Decision:** TEST\n**Decision:** WATCH"
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
        self.assertTrue(any("candidate headings or a candidate table" in failure for failure in result["failures"]))

    def test_discovery_accepts_one_decision_per_candidate_table_row(self):
        """Breaking decision-table parsing must reject this two-candidate discovery response."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation audit | 75/100 | TEST |\n| training service | 55/100 | WATCH |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_accepts_inline_code_decisions_in_table(self):
        """Markdown code styling around exact decision cells must preserve their meaning."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: `TEST` — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation audit | `75/100` | `TEST` |\n| training service | `55/100` | `WATCH` |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_rejects_lead_verdict_that_conflicts_with_candidate_decision(self):
        """The real 002 pattern must fail when a TEST lead candidate row says WATCH."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation sprint. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Candidate | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation sprint | 63/100 | WATCH |\n| evidence pack | 35/100 | KILL |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("lead" in failure for failure in result["failures"]), result["failures"])

    def test_discovery_accepts_matching_lead_and_candidate_table_scores(self):
        """A named lead and every candidate table score must map to their decisions."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: WATCH — Lead: remediation sprint. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Candidate | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation sprint | 63/100 | WATCH |\n| evidence pack | 35/100 | KILL |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_portfolio_accepts_matching_heading_candidate_scores(self):
        """Heading-shaped candidates must pair each adjusted score with one decision and the named lead."""
        case = validate_cases(CASES)[8]
        response = (
            "Verdict: TEST — Lead: renewal-backed offer. Conflicting survey evidence is weaker than paid renewal. "
            "Confidence: medium. Score: 75. Experiment: expand the paid pilot.\n"
            "## Candidate: survey-backed offer\nAdjusted score: 55/100\nDecision: WATCH\n"
            "## Candidate: renewal-backed offer\nAdjusted score: 75/100\nDecision: TEST"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_portfolio_rejects_heading_candidate_score_decision_mismatch(self):
        """A heading candidate cannot label a 45/100 adjusted score as TEST."""
        case = validate_cases(CASES)[8]
        response = (
            "Verdict: TEST — Lead: renewal-backed offer. Conflicting survey evidence is weaker than paid renewal. "
            "Confidence: medium. Score: 75. Experiment: expand the paid pilot.\n"
            "## Candidate: survey-backed offer\nAdjusted score: 55/100\nDecision: WATCH\n"
            "## Candidate: renewal-backed offer\nAdjusted score: 45/100\nDecision: TEST"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("adjusted score" in failure for failure in result["failures"]), result["failures"])

    def test_discovery_cases_allow_killing_non_lead_candidates(self):
        """A discovery must be able to reject a weak candidate while recommending a viable lead."""
        cases = validate_cases(CASES)
        self.assertIn("KILL", cases[1]["allowed_decisions"])
        self.assertIn("KILL", cases[5]["allowed_decisions"])

    def test_common_unicode_hyphen_preserves_constraint_match(self):
        """Typography must not hide an otherwise explicit 30-day constraint from scoring."""
        case = validate_cases(CASES)[5]
        response = (
            "Verdict: TEST — Lead: service sprint. A two-person team can run a 30‑day experiment within a $2,000 budget. "
            "The cost is capped and the success threshold is two deposits.\n"
            "| Candidate | Adjusted score | Decision |\n| --- | ---: | --- |\n| service sprint | 75/100 | TEST |"
        )
        self.assertTrue(score_response(case, response)["passed"])

    def test_discovery_rejects_decision_label_before_candidate_table(self):
        """An overall Decision before a valid table must not supplement the lead Verdict."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit.\nDecision: WATCH\n"
            "Target user: small ecommerce teams. Accessibility is the market change. "
            "Alternatives and willingness to pay are unknown. Experiment: test a paid offer.\n"
            "| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation audit | 75/100 | TEST |\n| training service | 55/100 | WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("decision table cells" in failure for failure in result["failures"]))

    def test_portfolio_rejects_decision_label_after_candidate_table(self):
        """An overall Decision after a valid table must not add another labeled decision."""
        case = validate_cases(CASES)[8]
        response = (
            "Verdict: TEST — Portfolio lead: renewal-backed concept. Conflicting survey evidence is weaker "
            "than paid renewal behavior. Confidence: medium. Score: 72. Experiment: expand the paid pilot.\n"
            "| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| survey-backed concept | 55/100 | WATCH |\n| renewal-backed concept | 75/100 | TEST |\n"
            "Decision: WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("decision table cells" in failure for failure in result["failures"]))

    def test_discovery_rejects_verdict_inside_candidate_table(self):
        """A Verdict in a candidate row must not masquerade as table commentary."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Adjusted score | Decision | Notes |\n| --- | ---: | --- | --- |\n"
            "| remediation audit | 75/100 | TEST | Verdict: WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overall verdict" in failure for failure in result["failures"]))

    def test_discovery_rejects_conflicting_decision_table_row(self):
        """A table row with two decision cells must fail instead of being treated as one candidate decision."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n"
            "| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation audit | 75/100 | TEST / WATCH |"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("table row" in failure for failure in result["failures"]))

    def test_discovery_rejects_multiple_verdicts_with_candidate_headings(self):
        """A second overall Verdict in a heading response must not be mistaken for a candidate decision."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n## Candidate: remediation audit\nAdjusted score: 75/100\nDecision: TEST\nVerdict: WATCH"
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overall verdict" in failure for failure in result["failures"]))

    def test_discovery_rejects_multiple_verdicts_with_candidate_table(self):
        """A table must not allow a contradictory second lead Verdict after its rows."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: remediation audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer.\n| Opportunity | Adjusted score | Decision |\n| --- | ---: | --- |\n"
            "| remediation audit | 75/100 | TEST |\nVerdict: WATCH"
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
            "## Candidate: remediation audit\nAdjusted score: 75/100\nDecision: TEST\nVerdict: TEST — Lead: remediation audit."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("first labeled decision" in failure for failure in result["failures"]))

    def test_discovery_rejects_lead_first_unstructured_verdict(self):
        """A lead verdict without a score/decision candidate structure cannot be checked consistently."""
        case = validate_cases(CASES)[1]
        response = (
            "Verdict: TEST — Lead: accessibility audit. Target user: small ecommerce teams. "
            "Accessibility is the market change. Alternatives and willingness to pay are unknown. "
            "Experiment: test a paid offer."
        )
        result = score_response(case, response)
        self.assertFalse(result["passed"])
        self.assertTrue(any("candidate headings or a candidate table" in failure for failure in result["failures"]))

    def test_sql_boundary_rejects_opportunity_analysis(self):
        """Giving a SQL request a GO/TEST/WATCH/KILL analysis must fail the boundary case."""
        case = validate_cases(CASES)[-1]
        analysis = "Verdict: TEST. Score: 65/100. Run a paid pilot for this SQL query."
        result = score_response(case, analysis)
        self.assertFalse(result["passed"])
        self.assertTrue(any("must not trigger" in failure for failure in result["failures"]))

        boundary_response = "SELECT plan_tier, COUNT(DISTINCT user_id) FROM events GROUP BY plan_tier;"
        self.assertTrue(score_response(case, boundary_response)["passed"])

        scoped_decline = "This is outside the Idea Opportunity Engine scope; it is not an opportunity analysis."
        self.assertTrue(score_response(case, scoped_decline)["passed"])

        with_query = "WITH activity AS (SELECT user_id FROM events) SELECT COUNT(*) FROM activity;"
        self.assertTrue(score_response(case, with_query)["passed"])

    def test_non_trigger_case_has_no_positive_phrase_requirement(self):
        """A boundary case gates only opportunity-analysis leakage, not a prescribed SQL or refusal phrase."""
        case = validate_cases(CASES)[-1]
        self.assertEqual([], case["required_behavior_groups"])

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
