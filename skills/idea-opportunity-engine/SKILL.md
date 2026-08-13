---
name: idea-opportunity-engine
description: Evidence-first discovery, validation, and portfolio comparison for founders, product teams, and innovation teams evaluating business opportunities. Use for finding opportunities from market change and customer friction, challenging a proposed business idea, comparing candidate opportunities, assessing target users and willingness to pay, or designing a decisive validation experiment. Do not use for generic coding, SQL, writing, research, legal, medical, investment, or market-sizing tasks that are not evaluating a business opportunity.
---

# Idea Opportunity Engine

Produce a decision aid, not encouragement. Do not claim certainty where the evidence does not support it.

## Workflow

1. Identify the requested mode: **Discovery** (generate candidates), **Validation** (challenge one idea), or **Portfolio** (compare candidates). If the request is outside this boundary, say so and do not force an opportunity analysis.
2. Read [evidence-policy.md](references/evidence-policy.md) for every analysis. Build a claim ledger, distinguish evidence from hypotheses and unknowns, and seek disconfirming evidence. Verify current market claims with available sources and cite them; if sources are unavailable, lower confidence rather than inventing support.
3. Read [scoring-model.md](references/scoring-model.md) to score each viable opportunity on the 100-point rubric, apply penalties, state confidence, and assign exactly one decision per evaluated opportunity: `GO`, `TEST`, `WATCH`, or `KILL`. Validation has one overall decision; Discovery and Portfolio also name a single lead or portfolio recommendation.
4. Read [report-template.md](references/report-template.md) and use the shape that matches the mode. Start with the verdict. Include target user, problem, evidence and unknowns, direct and indirect alternatives (including doing nothing), willingness to pay, contradictions, score, and decision rationale.
5. Read [experiment-framework.md](references/experiment-framework.md) to turn the riskiest assumption into the cheapest decisive experiment. Define the audience, method, time box, success threshold, failure threshold, and the decision that each outcome triggers.

## Required response standard

- Lead with a one-line verdict. Validation has one overall decision label; Discovery and Portfolio name one lead or portfolio recommendation and give each candidate exactly one decision label.
- Separate observed evidence, interpretation, contradiction, and unknown. Never present a hypothesis, market-size estimate, or AI popularity as proof of demand.
- Name alternatives before recommending a solution; include non-software and status-quo alternatives when relevant.
- Treat willingness to pay as unproven unless there is a credible payment or commitment signal.
- Show the 100-point score, applicable penalties, confidence, and the decision mapping.
- End with one thresholded experiment. Be willing to recommend `KILL` when the evidence or economics do not justify further work.

## Boundaries

Do not conduct primary customer research, provide legal, medical, or investment advice, promise a business outcome, or substitute a deterministic score for judgment. State these limits plainly when they affect the request.
