#!/bin/sh
# Install only the nested standalone skill from this checkout.
set -eu

operation=install
dry_run=0
destination=""

usage() {
  echo "Usage: $0 [install|--update|--uninstall] [--dry-run] [--dest DIR]" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    install) operation=install ;;
    --update) operation=update ;;
    --uninstall) operation=uninstall ;;
    --dry-run) dry_run=1 ;;
    --dest)
      shift
      if [ "$#" -eq 0 ] || [ -z "$1" ]; then
        echo "--dest requires a directory" >&2
        exit 2
      fi
      destination=$1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
  shift
done

if [ -z "$destination" ]; then
  if [ -n "${CODEX_HOME:-}" ]; then
    destination="$CODEX_HOME/skills"
  else
    destination="${HOME:?HOME must be set}/.agents/skills"
  fi
fi

destination=${destination%/}
if [ -z "$destination" ]; then
  destination=/
fi
skill_dest="$destination/idea-opportunity-engine"
case "$skill_dest" in
  */idea-opportunity-engine) ;;
  *)
    echo "Refusing unexpected destination: $skill_dest" >&2
    exit 1
    ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_skill="$script_dir/skills/idea-opportunity-engine"
if [ ! -f "$source_skill/SKILL.md" ]; then
  echo "Source skill is incomplete: $source_skill" >&2
  exit 1
fi

announce() {
  if [ "$dry_run" -eq 1 ]; then
    echo "Dry run: $*"
  else
    echo "$*"
  fi
}

stage_and_install() {
  action=$1
  if [ "$action" = "update" ] && [ ! -d "$skill_dest" ]; then
    echo "No installed skill at $skill_dest; use install first" >&2
    return 1
  fi
  if [ "$dry_run" -eq 1 ]; then
    announce "$action $source_skill -> $skill_dest"
    return 0
  fi

  mkdir -p "$destination"
  stage_dir=$(mktemp -d "$destination/.idea-opportunity-engine-install.XXXXXX") || exit 1
  keep_stage=0
  backup_moved=0
  preserve_recovery() {
    keep_stage=1
    echo "Recovery copy retained at: $backup_skill" >&2
  }
  cleanup() {
    exit_code=$?
    if [ "$keep_stage" -eq 0 ]; then
      rm -rf -- "$stage_dir"
    fi
    trap - EXIT HUP INT TERM
    exit "$exit_code"
  }
  interrupted() {
    trap - HUP INT TERM
    if [ "$backup_moved" -eq 1 ] && [ -e "${backup_skill:-}" ]; then
      preserve_recovery
      exit 128
    fi
    if [ -e "$skill_dest" ]; then
      echo "Update interrupted before backup; existing install remains at: $skill_dest" >&2
      exit 128
    fi
    keep_stage=1
    echo "Update interrupted during backup movement; staging retained for inspection at: $stage_dir" >&2
    exit 128
  }
  trap cleanup EXIT
  trap interrupted HUP INT TERM

  staged_skill="$stage_dir/idea-opportunity-engine"
  cp -R "$source_skill" "$staged_skill"
  if [ ! -f "$staged_skill/SKILL.md" ]; then
    echo "Staged skill is incomplete" >&2
    exit 1
  fi

  if [ "$action" = "install" ]; then
    if [ -e "$skill_dest" ]; then
      echo "Refusing to overwrite existing destination: $skill_dest" >&2
      exit 1
    fi
    mv "$staged_skill" "$skill_dest"
    echo "Installed $skill_dest"
    return 0
  fi

  backup_skill="$stage_dir/previous"
  backup_moved=1
  if ! mv "$skill_dest" "$backup_skill"; then
    backup_moved=0
    echo "Could not move existing skill to backup; update aborted." >&2
    exit 1
  fi
  if mv "$staged_skill" "$skill_dest" && [ -f "$skill_dest/SKILL.md" ]; then
    if ! rm -rf -- "$backup_skill"; then
      preserve_recovery
      exit 1
    fi
    echo "Updated $skill_dest"
    return 0
  fi
  echo "Could not install staged skill; attempting restore." >&2
  if ! rm -rf -- "$skill_dest"; then
    preserve_recovery
    exit 1
  fi
  if mv "$backup_skill" "$skill_dest"; then
    backup_moved=0
    exit 1
  fi
  preserve_recovery
  exit 1
}

case "$operation" in
  install)
    if [ -e "$skill_dest" ]; then
      echo "Refusing to overwrite existing destination: $skill_dest" >&2
      exit 1
    fi
    stage_and_install install
    ;;
  update)
    stage_and_install update
    ;;
  uninstall)
    if [ ! -e "$skill_dest" ]; then
      echo "No installed skill at $skill_dest" >&2
      exit 1
    fi
    if [ "$dry_run" -eq 1 ]; then
      announce "uninstall $skill_dest"
      exit 0
    fi
    rm -rf -- "$skill_dest"
    echo "Uninstalled $skill_dest"
    ;;
esac
