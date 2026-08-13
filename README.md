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

After this repository is public, clone it and copy only the nested skill into your Codex skills directory:

```bash
git clone https://github.com/sheshixuan/idea-opportunity-engine.git
cd idea-opportunity-engine
skill_root="${CODEX_HOME:-$HOME/.codex}/skills"
skill_dest="$skill_root/idea-opportunity-engine"
test ! -e "$skill_dest" || { echo "Refusing to overwrite $skill_dest" >&2; exit 1; }
mkdir -p "$skill_root"
cp -R skills/idea-opportunity-engine "$skill_dest"
```

This procedure copies only `skills/idea-opportunity-engine`; it does not install the repository root. A convenience `install.sh` is planned for the full release, but is not part of this package revision.

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

For a standalone skill installed with `$skill-installer`, remove its installed `idea-opportunity-engine` skill directory and run the install command again. For a cloned checkout, update the checkout and replace only the nested skill directory:

```bash
git pull --ff-only && (
  skill_root="${CODEX_HOME:-$HOME/.codex}/skills"
  skill_dest="$skill_root/idea-opportunity-engine"
  test -d "$skill_dest" || { echo "No installed skill at $skill_dest" >&2; exit 1; }
  stage_dir="$(mktemp -d "$skill_root/.idea-opportunity-engine-update.XXXXXX")" || exit 1
  staged_skill="$stage_dir/idea-opportunity-engine"
  backup_skill="$stage_dir/previous"
  preserve_recovery() {
    keep_stage=1
    echo "Automatic restore failed. Recovery copy retained at: $backup_skill" >&2
  }
  restore_previous() {
    if [ -e "$skill_dest" ]; then
      rm -rf "$skill_dest" || { preserve_recovery; return 1; }
    fi
    if mv "$backup_skill" "$skill_dest"; then
      return 0
    fi
    preserve_recovery
    return 1
  }
  keep_stage=0
  cleanup() {
    exit_code=$?
    if [ "$keep_stage" -eq 1 ]; then
      trap - EXIT HUP INT TERM
      exit "$exit_code"
    fi
    rm -rf "$stage_dir"
    trap - EXIT HUP INT TERM
    exit "$exit_code"
  }
  trap cleanup EXIT HUP INT TERM
  cp -R skills/idea-opportunity-engine "$staged_skill"
  test -f "$staged_skill/SKILL.md" || { echo "Staged skill is incomplete" >&2; exit 1; }
  if ! mv "$skill_dest" "$backup_skill"; then
    echo "Could not move existing skill to backup; update aborted." >&2
    exit 1
  fi
  if [ ! -d "$backup_skill" ] || [ -e "$skill_dest" ]; then
    preserve_recovery
    exit 1
  fi
  if mv "$staged_skill" "$skill_dest" && [ -f "$skill_dest/SKILL.md" ] && [ ! -e "$skill_dest/idea-opportunity-engine" ]; then
    rm -rf "$backup_skill"
    exit 0
  fi
  echo "Could not install staged skill; attempting restore." >&2
  restore_previous || exit 1
  exit 1
)
```

To uninstall the plugin, remove or disable it through the Codex plugin marketplace. To uninstall a cloned-checkout installation, remove only the exact nested skill destination:

```bash
skill_dest="${CODEX_HOME:-$HOME/.codex}/skills/idea-opportunity-engine"
case "$skill_dest" in
  */skills/idea-opportunity-engine) rm -rf "$skill_dest" ;;
  *) echo "Refusing unexpected destination: $skill_dest" >&2; exit 1 ;;
esac
```

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
