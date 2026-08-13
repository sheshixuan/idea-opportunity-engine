# Idea Opportunity Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, verify, and publish a public Codex Plugin containing the installable Idea Opportunity Engine Skill and its deterministic 10-case eval harness.

**Architecture:** The repository root is a plugin and repo marketplace; the reusable workflow lives once under `skills/idea-opportunity-engine`. Python standard-library validators and tests cover repository structure and eval behavior, while a shell installer supports standalone local installation.

**Tech Stack:** Markdown, JSON, YAML, POSIX-compatible Bash, Python 3 standard library, Codex bundled Skill/Plugin validators, Git, GitHub CLI.

## Global Constraints

- Repository name and public target are exactly `sheshixuan/idea-opportunity-engine` unless a safe read-only check discovers an existing repository.
- Plugin and skill version starts at `0.1.0` and uses the MIT license.
- Required references are exactly `evidence-policy.md`, `scoring-model.md`, `report-template.md`, and `experiment-framework.md`.
- The eval suite contains exactly 10 standard JSON cases, including one `should_trigger: false` SQL boundary case.
- No API keys, tokens, credentials, customer data, or private conversation content may be committed.
- The package has no mandatory MCP server, API, paid service, or non-standard Python dependency.
- Do not claim the skill guarantees business outcomes or that deterministic keyword checks prove semantic judgment quality.
- Do not create the public GitHub repository until all local release gates pass.

---

### Task 1: Plugin and Skill package

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `skills/idea-opportunity-engine/SKILL.md`
- Create: `skills/idea-opportunity-engine/agents/openai.yaml`
- Create: `skills/idea-opportunity-engine/references/evidence-policy.md`
- Create: `skills/idea-opportunity-engine/references/scoring-model.md`
- Create: `skills/idea-opportunity-engine/references/report-template.md`
- Create: `skills/idea-opportunity-engine/references/experiment-framework.md`
- Create: `README.md`
- Create: `LICENSE`

**Interfaces:**
- Consumes: the approved design document and official current Skill/Plugin layout.
- Produces: a root plugin named `idea-opportunity-engine`, one nested Skill of the same name, four first-level references, and customer documentation.

- [ ] **Step 1: Scaffold the plugin with the bundled plugin creator**

Run the bundled creator for `idea-opportunity-engine` with a `skills/` directory, then place the generated plugin files at this repository root without creating a second nested repository.

- [ ] **Step 2: Initialize the nested skill with the bundled skill creator**

Run `init_skill.py` for `idea-opportunity-engine` with `references` resources and interface values:

```text
display_name=Idea Opportunity Engine
short_description=Evidence-first opportunity discovery and validation
default_prompt=Use $idea-opportunity-engine to evaluate this business opportunity and design the cheapest decisive test.
```

- [ ] **Step 3: Author the four references**

Encode the evidence hierarchy, 100-point scoring rubric, three report shapes, and experiment contract from the design. Each reference must be linked directly from `SKILL.md`; no nested reference chains.

- [ ] **Step 4: Author the concise SKILL router**

The frontmatter contains only `name` and `description`. The description must cover discovery, validation, portfolio comparison, target users, and trigger boundaries. The body must require a verdict-first response, evidence/unknown separation, alternatives, willingness to pay, a scored decision, and a thresholded experiment.

- [ ] **Step 5: Author distribution metadata and customer documentation**

The plugin manifest points to `./skills/`, uses repository and homepage URL `https://github.com/sheshixuan/idea-opportunity-engine`, and declares no MCP/apps/hooks. The repo marketplace points to `./`. README includes plugin install, `$skill-installer`, cloned-checkout install, three usage examples, update, uninstall, testing, privacy, and limitations.

- [ ] **Step 6: Run the bundled Skill and Plugin validators**

Run `quick_validate.py` on `skills/idea-opportunity-engine` and `validate_plugin.py` on the repository root. Expected: both exit 0 with no placeholders.

- [ ] **Step 7: Commit the package**

```bash
git add .codex-plugin .agents skills README.md LICENSE
git commit -m "feat: package idea opportunity engine"
```

### Task 2: Eval harness and safe installer

**Files:**
- Create: `evals/cases/001-confirmation-bias.json`
- Create: `evals/cases/002-active-discovery.json`
- Create: `evals/cases/003-evidence-discipline.json`
- Create: `evals/cases/004-kill-watch.json`
- Create: `evals/cases/005-b2b-willingness-to-pay.json`
- Create: `evals/cases/006-constrained-opportunity.json`
- Create: `evals/cases/007-non-software-alternatives.json`
- Create: `evals/cases/008-pricing-validation.json`
- Create: `evals/cases/009-conflicting-evidence.json`
- Create: `evals/cases/010-trigger-boundary-sql.json`
- Create: `evals/run_harness.py`
- Create: `scripts/validate_repository.py`
- Create: `scripts/security_scan.py`
- Create: `tests/test_eval_harness.py`
- Create: `tests/test_install_script.py`
- Create: `tests/test_repository_validation.py`
- Create: `tests/test_security_scan.py`
- Create: `install.sh`

**Interfaces:**
- Consumes: the Task 1 package paths and decision vocabulary.
- Produces: `validate_cases(case_dir)`, `score_response(case, text)`, repository/security CLI validators, and `install.sh` operations `install`, `--update`, `--uninstall`, `--dry-run`, and `--dest DIR`.

- [ ] **Step 1: Write failing eval harness tests**

Tests must prove malformed cases are rejected, exactly ten valid cases pass, a compliant response passes, a missing required behavior fails, a forbidden behavior fails, a wrong decision fails, and the SQL non-trigger case rejects an opportunity analysis.

- [ ] **Step 2: Run the eval tests and verify RED**

Run `python3 -m unittest tests.test_eval_harness -v`. Expected: import or missing-file failure because the harness is not implemented.

- [ ] **Step 3: Add the 10 cases and minimal harness**

Implement case validation and observable response scoring using only the Python standard library. Each case has a unique three-digit ID, mode, prompt, `should_trigger`, allowed decisions, required behavior groups, forbidden phrases, and notes for the semantic judge.

- [ ] **Step 4: Run the eval tests and verify GREEN**

Run `python3 -m unittest tests.test_eval_harness -v`. Expected: all tests pass.

- [ ] **Step 5: Write failing installer tests**

Use temporary directories to prove fresh install, existing-destination refusal, update replacement, dry-run no-write behavior, uninstall of only the exact skill destination, and destination override.

- [ ] **Step 6: Run installer tests and verify RED**

Run `python3 -m unittest tests.test_install_script -v`. Expected: missing `install.sh` failure.

- [ ] **Step 7: Implement the installer and verify GREEN**

Use quoted paths, `mktemp -d`, an exit trap, and exact destination checks. Run the installer test module again and expect all tests to pass.

- [ ] **Step 8: Add repository and secret-scan tests before implementations**

Tests must catch a missing required file, a mismatched plugin/skill name, a common token-shaped credential, a private key marker, and an email-like value outside the allowed public documentation patterns.

- [ ] **Step 9: Run validator tests RED, implement validators, then run GREEN**

Run `python3 -m unittest tests.test_repository_validation tests.test_security_scan -v` before and after implementation. The final run must pass.

- [ ] **Step 10: Run the complete deterministic suite**

Run `python3 -m unittest discover -s tests -v`, `python3 evals/run_harness.py --validate-cases`, `python3 scripts/validate_repository.py`, and `python3 scripts/security_scan.py`. Expected: zero failures and exactly 10 valid cases.

- [ ] **Step 11: Commit the harness and installer**

```bash
git add evals scripts tests install.sh README.md
git commit -m "test: add eval and installation gates"
```

### Task 3: Release verification and GitHub publication

**Files:**
- Modify: `README.md` only if a tested installation command differs from the documented command.
- Create locally but do not commit: temporary install directories and generated eval responses.

**Interfaces:**
- Consumes: the complete local repository, authenticated `gh`, and the public repository target.
- Produces: a verified public `main` branch and a post-publish installation check.

- [ ] **Step 1: Run all fresh local release gates**

Run both bundled validators, all unit tests, case validation, repository validation, security scanning, and install/update/uninstall integration in a new temporary directory. Stop if any command exits nonzero.

- [ ] **Step 2: Forward-test all ten prompts**

Use fresh agents with only the Skill path and prompt text, save raw responses outside tracked files, and run `evals/run_harness.py --responses-dir <directory>`. Record deterministic pass/fail counts and retain the semantic-judge limitation.

- [ ] **Step 3: Review the complete diff and tracked-file inventory**

Run `git status -sb`, `git diff --check`, inspect `git ls-files`, and re-run the secret scan on tracked files. Confirm no temporary results or private files are staged.

- [ ] **Step 4: Rename the completed local branch to `main`**

This new repository has no remote history; perform the rename only after all implementation and review gates pass.

- [ ] **Step 5: Create and push the public repository**

Run `gh repo create sheshixuan/idea-opportunity-engine --public --source=. --remote=origin --push --description "Evidence-first business opportunity discovery and validation skill for Codex"`.

- [ ] **Step 6: Verify the remote repository**

Use `gh repo view`, confirm visibility is `PUBLIC`, confirm default branch is `main`, and fetch the remote `SKILL.md`, `plugin.json`, and README through GitHub.

- [ ] **Step 7: Verify installation from the published GitHub path**

Run the bundled `skill-installer` helper with `--url https://github.com/sheshixuan/idea-opportunity-engine/tree/main/skills/idea-opportunity-engine --dest <temporary-directory>`, then run the bundled Skill validator on the installed copy. Remove only the temporary directory afterwards.

- [ ] **Step 8: Verify plugin marketplace discovery**

Use an isolated temporary Codex home when supported to add `sheshixuan/idea-opportunity-engine` as a marketplace and confirm the marketplace and plugin can be resolved without changing the user's normal Codex configuration. If the CLI cannot isolate its config, document the exact unexecuted interactive plugin step and rely on manifest/marketplace validators.

- [ ] **Step 9: Report the release**

Return the repository URL, one-line customer installation prompt, exact validation counts, plugin installation alternative, and limitations. Do not describe the repository as published until Steps 5–8 have evidence.

