# Idea Opportunity Engine Distribution Design

## Goal

Publish `sheshixuan/idea-opportunity-engine` as a public, installable Codex package that helps founders, product teams, and innovation teams discover and validate business opportunities without inventing evidence or defaulting to encouragement.

## Agreed product boundary

The user selected a public GitHub distribution and approved the repository name `idea-opportunity-engine`. The package supports three analysis modes:

- Discovery: find candidate opportunities from market change and customer friction.
- Validation: challenge an existing idea with supporting and contradicting evidence.
- Portfolio: compare multiple opportunities using one scoring model.

Every triggered analysis separates evidence, hypotheses, contradictions, and unknowns; evaluates direct and indirect alternatives; examines willingness to pay; designs the cheapest decisive experiment; and ends with exactly one of `GO`, `TEST`, `WATCH`, or `KILL`.

The skill does not provide legal, medical, or investment advice, guarantee market outcomes, conduct primary customer research, or treat market size and AI popularity as proof of demand. Generic coding, SQL, writing, and research tasks must not trigger it unless the user is evaluating a business opportunity.

## Distribution architecture

Use the repository root as the plugin root:

```text
idea-opportunity-engine/
├── .codex-plugin/plugin.json
├── .agents/plugins/marketplace.json
├── skills/idea-opportunity-engine/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
├── evals/cases/
├── scripts/
├── tests/
├── install.sh
├── README.md
└── LICENSE
```

This follows the current official model: a reusable workflow is authored as a Skill, while distribution to other people uses a Plugin. The nested skill path also remains directly installable through `$skill-installer`. The repo marketplace entry points to `./`, so `codex plugin marketplace add sheshixuan/idea-opportunity-engine` can discover the root plugin.

Official sources consulted on 2026-08-13:

- https://developers.openai.com/codex/skills
- https://developers.openai.com/plugins/build/plugins

## Skill components

`SKILL.md` is a concise router and workflow. It tells the agent when to read each first-level reference:

- `evidence-policy.md`: source hierarchy, claim ledger, contradiction handling, and evidence gates.
- `scoring-model.md`: 100-point rubric, penalties, confidence, and decision mapping.
- `report-template.md`: required response shapes for Discovery, Validation, and Portfolio.
- `experiment-framework.md`: risky-assumption selection, experiment types, success thresholds, failure thresholds, and kill criteria.

The skill has no API key, MCP server, or paid-service dependency. When web or connected sources are available, the agent should verify current market claims and cite them. Without those tools, it must downgrade confidence and label unsupported claims as hypotheses or unknowns.

## Evaluation design

Ten JSON cases cover confirmation bias, active discovery, evidence discipline, willingness to kill weak ideas, B2B payment signals, constrained opportunity discovery, non-software alternatives, pricing validation, conflicting evidence, and a SQL trigger-boundary negative case.

The deterministic harness has two layers:

1. Case validation: checks schema, IDs, expected decisions, trigger flags, and acceptance rules.
2. Response scoring: checks required observable behaviors, forbidden behaviors, decision constraints, and the non-trigger boundary.

Deterministic checks do not prove commercial judgment quality. The repository documents that a human or LLM judge is still required for semantic quality, source reliability, and whether experiments are genuinely decision-changing.

## Installation behavior

`install.sh` installs the standalone skill from a cloned checkout. It defaults to `$CODEX_HOME/skills` when `CODEX_HOME` is set and otherwise `$HOME/.agents/skills`, matching current Codex discovery guidance. It supports explicit install, update, uninstall, dry-run, and destination override operations. All destructive operations are limited to an exact `idea-opportunity-engine` destination.

The README also documents the official `$skill-installer` GitHub path and plugin marketplace commands. Update and uninstall instructions are included for both supported installation paths.

## Release gates

Before creating the public repository:

1. Validate the skill with the official bundled skill validator.
2. Validate the plugin with the bundled plugin validator.
3. Run all unit and integration tests.
4. Validate all ten eval case files and run response-scoring fixtures.
5. Exercise install, update, dry-run, and uninstall in a temporary destination.
6. Scan tracked files for common credential and personal-data patterns.
7. Create the public GitHub repository only if all gates pass.
8. After pushing, verify the remote repository and install the published skill into a temporary directory through the bundled `$skill-installer` helper.

## Release metadata

- Initial version: `0.1.0`
- License: MIT
- Publisher: `sheshixuan`
- Repository: `https://github.com/sheshixuan/idea-opportunity-engine`
- No external service or authentication requirement

