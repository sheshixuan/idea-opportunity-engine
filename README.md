# Idea Opportunity Engine

An evidence-first Codex plugin and standalone skill for business opportunity discovery, validation, and portfolio comparison. It separates evidence from hypotheses, assesses alternatives and willingness to pay, assigns a 100-point score, and proposes the cheapest decisive experiment.

## Install as a plugin

After this repository is public, add its marketplace in Codex:

```bash
codex plugin marketplace add sheshixuan/idea-opportunity-engine
```

Install or enable **Idea Opportunity Engine** from the Codex plugin marketplace. The marketplace manifest exposes this repository root as the plugin and contains no MCP server, app, hook, API key, or paid-service requirement.

## Install the standalone skill

Use the bundled `$skill-installer` from Codex:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/sheshixuan/idea-opportunity-engine/tree/main/skills/idea-opportunity-engine
```

The skill becomes available on the next Codex turn.

### Install from a cloned checkout

Clone the repository, then use the included installer:

```bash
git clone https://github.com/sheshixuan/idea-opportunity-engine.git
cd idea-opportunity-engine
./install.sh
```

`install.sh` is added in the next repository task. Until then, copy `skills/idea-opportunity-engine` into your Codex skills directory manually.

## Use

Invoke `$idea-opportunity-engine` with an opportunity question.

```text
Use $idea-opportunity-engine to find three B2B opportunities created by new accessibility requirements for small ecommerce teams.
```

```text
Use $idea-opportunity-engine to challenge my idea for an AI meeting-summary product for independent consultants. Recommend GO, TEST, WATCH, or KILL.
```

```text
Use $idea-opportunity-engine to compare these opportunities: a returns-automation service, a compliance training tool, and a field-sales note taker.
```

## Update and uninstall

For a standalone skill installed with `$skill-installer`, remove its installed `idea-opportunity-engine` skill directory and run the install command again. For a cloned checkout, use `./install.sh --update` after the installer is available.

To uninstall the plugin, remove or disable it through the Codex plugin marketplace. To uninstall a cloned-checkout installation, use `./install.sh --uninstall` after the installer is available.

## Testing

Validate the package with the bundled tools:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/idea-opportunity-engine
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

The next repository task adds deterministic eval, installer, repository, and security checks.

## Privacy

The package has no required external service, API key, MCP server, telemetry, or customer-data store. When you provide opportunity material or choose to research current claims, your normal Codex and connected-tool privacy settings apply. Do not provide confidential customer information unless you are authorized to do so.

## Limitations

This skill is a structured decision aid, not legal, medical, or investment advice. It cannot guarantee commercial outcomes, replace primary customer research, or establish demand from market size, AI popularity, or a persuasive narrative. Deterministic scores make assumptions inspectable; they do not replace judgment or source-quality review.
