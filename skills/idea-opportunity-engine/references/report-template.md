# Report Shapes

Use one shape and start with the verdict. **Validation** has one overall decision label: `GO`, `TEST`, `WATCH`, or `KILL`. **Discovery** and **Portfolio** name one lead or portfolio recommendation, then assign exactly one of those decision labels to every evaluated candidate.

## Discovery

1. **Verdict:** use exactly `Verdict: <DECISION> — Lead: <candidate name>.` The candidate name must exactly match one candidate-table name, and the verdict must equal that candidate's decision.
2. **Opportunity table:** use columns `Candidate`, `Target user`, `Evidence`, `Alternatives`, `Willingness to pay`, `Adjusted score`, `Confidence`, and `Decision`. Each adjusted score is an integer `/100` and must map to its decision.
3. **Recommended opportunity:** target user, problem, why now, evidence, contradictions, unknowns, and why it outranks alternatives.
4. **Decisive experiment:** use the experiment contract.

## Validation

1. **Verdict:** use exactly `Verdict: <DECISION> — <rationale>.`
2. **Decision card:** target user, painful job, proposed offer, exactly one `Adjusted score: <integer>/100`, confidence, and main reason. The adjusted score must map to the verdict; do not add another labeled decision.
3. **Evidence ledger:** supporting evidence, contrary evidence, inferences, and unknowns with sources or basis.
4. **Alternatives and payment:** direct, indirect, non-software, and do-nothing alternatives; payer, budget, price evidence, and switching cost.
5. **Decisive experiment:** use the experiment contract.

## Portfolio

1. **Verdict:** use exactly `Verdict: <DECISION> — Portfolio lead: <candidate name>.` The candidate name must exactly match one comparison-table name, and the verdict must equal that candidate's decision.
2. **Comparison table:** use columns `Opportunity`, `Target user`, `Adjusted score`, `Confidence`, `Payment evidence`, `Key risk`, and `Decision`. Each adjusted score is an integer `/100` and must map to its decision.
3. **Trade-offs:** explain why the leader wins and what evidence would change the ranking.
4. **Next experiment:** specify the cheapest test for the leading unresolved risk; state whether the other options should be watched or killed.

For all shapes, do not hide unknowns in a conclusion. Cite current external claims when sources are available and label unverified claims plainly.

If a table would be unreadable, Discovery or Portfolio may instead use one `## Candidate: <candidate name>` section per candidate. Each section must contain exactly one `Adjusted score: <integer>/100` and exactly one `Decision: <DECISION>`. The named lead must exactly match one heading. Do not repeat adjusted-score or labeled-decision fields elsewhere.
