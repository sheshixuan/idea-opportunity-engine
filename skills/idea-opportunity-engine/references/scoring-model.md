# 100-Point Scoring Model

Score each opportunity once evidence, alternatives, and unknowns are explicit. Use integers and show brief reasoning for every category.

| Dimension | Points | What earns a high score |
| --- | ---: | --- |
| Problem severity and frequency | 20 | The target user experiences a frequent, costly, urgent problem. |
| Evidence quality | 20 | Recent behavioral or operational evidence directly supports the problem and segment. |
| Willingness to pay | 20 | Payment, budget, procurement, or a credible economic buyer signal exists. |
| Differentiation versus alternatives | 15 | The approach wins against direct, indirect, and status-quo alternatives on a meaningful job. |
| Reachability and distribution | 10 | The target segment can be reached repeatedly at a plausible cost. |
| Feasibility and execution | 10 | The smallest useful offer can be delivered with manageable capability, cost, and risk. |
| Timing and market conditions | 5 | A durable change makes adoption more likely now without depending on hype. |

The base score is the sum of these dimensions, out of 100.

## Penalties and confidence

Apply each relevant penalty after the base score:

- Subtract 10 for a material claim supported only by stated intent or narrative.
- Subtract 10 when a strong direct or status-quo alternative is not convincingly beaten.
- Subtract 10 when no credible payer, budget, or commitment signal is identified.
- Subtract 5 to 15 for unresolved contradictory evidence, choosing the larger penalty when the contradiction challenges the core problem or segment.

State confidence separately as high, medium, or low. Confidence reflects evidence coverage and consistency; it does not change the arithmetic score. Do not use a high score with low confidence to claim certainty.

## Decision mapping

| Adjusted score | Confidence and gate | Decision |
| --- | --- | --- |
| 80–100 | High confidence; behavioral or operational evidence and a payment signal | `GO` |
| 60–79 | Viable but one decisive uncertainty remains | `TEST` |
| 40–59 | Meaningful uncertainty, weak timing, or limited evidence | `WATCH` |
| 0–39 | Weak economics, weak evidence, or no credible path to payment | `KILL` |

Downgrade `GO` to `TEST` if its evidence gate is not met. The decision is a prioritization aid, not an investment recommendation.
