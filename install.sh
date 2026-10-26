#!/usr/bin/env bash
# Installs the job-hunt kit into ~/.claude.
# Safe to re-run after updating: your profile, tracker, house rules and practice history are never touched.
# If you already have a skill with the same name that didn't come from this kit, it's backed up first.
#
#   bash install.sh               install or update
#   bash install.sh --uninstall   remove the skills (your files in ~/.claude/job-search are kept)

# Re-run under bash if started with `sh install.sh` or another shell.
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude="$HOME/.claude"
data="$claude/job-search"
marker=".job-hunt-kit"
skills=(jobsweep tailor-apply interview-drill)

if [ "${1:-}" = "--uninstall" ]; then
  for s in "${skills[@]}"; do
    if [ -f "$claude/skills/$s/$marker" ]; then rm -rf "$claude/skills/$s"; echo "removed /$s"; fi
  done
  if grep -q "job-hunt-kit" "$claude/agents/jd-scout.md" 2>/dev/null; then
    rm -f "$claude/agents/jd-scout.md"; echo "removed jd-scout agent"
  fi
  echo "Your profile, tracker and practice history are still in $data (delete that folder to remove them)."
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but wasn't found."
  echo "  macOS:  run 'xcode-select --install', or install it from https://www.python.org/downloads/"
  echo "  Linux:  install the python3 package with your package manager"
  exit 1
fi

for d in "$here/skills" "$here/agents" "$here/templates"; do
  if [ ! -d "$d" ]; then
    echo "Can't find $(basename "$d")/ next to install.sh. Run this from inside the downloaded folder."
    exit 1
  fi
done

mkdir -p "$claude/skills" "$claude/agents" "$data/templates"
backup="$claude/job-hunt-kit-backup-$(date +%Y%m%d-%H%M%S)"

backup_if_foreign() {   # $1 = existing path, $2 = true if it came from this kit
  if [ -e "$1" ] && [ "$2" != true ]; then
    mkdir -p "$backup"
    mv "$1" "$backup/"
    echo "⚠️  You already had $(basename "$1"), which isn't from this kit. Moved it to $backup/"
  fi
}

for s in "${skills[@]}"; do
  dest="$claude/skills/$s"
  ours=false; [ -f "$dest/$marker" ] && ours=true
  backup_if_foreign "$dest" "$ours"
  rm -rf "$dest"
  cp -R "$here/skills/$s" "$dest"
  touch "$dest/$marker"
  chmod +x "$dest"/scripts/*.py 2>/dev/null || true
done

agent="$claude/agents/jd-scout.md"
ours=false; grep -q "job-hunt-kit" "$agent" 2>/dev/null && ours=true
backup_if_foreign "$agent" "$ours"
{ cat "$here/agents/jd-scout.md"; echo; echo "<!-- installed by job-hunt-kit -->"; } > "$agent"

cp "$here"/templates/*.md "$data/templates/"
for f in profile drill-progress tracker; do
  [ -f "$data/$f.md" ] || cp "$here/templates/$f.md" "$data/$f.md"
done

# Verify, so a broken install is reported here and not at first use.
missing=()
for p in "$claude/skills/jobsweep/SKILL.md" "$claude/skills/tailor-apply/SKILL.md" \
         "$claude/skills/interview-drill/SKILL.md" "$agent" \
         "$data/profile.md" "$data/tracker.md" "$data/drill-progress.md"; do
  [ -f "$p" ] || missing+=("$p")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "❌ Install incomplete. Missing:"; printf '   %s\n' "${missing[@]}"; exit 1
fi
if ! python3 "$claude/skills/interview-drill/scripts/stats.py" >/dev/null 2>&1; then
  echo "❌ The practice scripts didn't run with $(python3 --version 2>&1). Python 3.8 or newer is needed."; exit 1
fi

cat <<'MSG'

✅ Installed: /jobsweep, /tailor-apply, /interview-drill

Next:
  1. Restart Claude Code (or open a new session).
  2. Run any of these. Each one asks you a few setup questions the first time:
       /jobsweep          find and score jobs for you
       /tailor-apply      tailor your resume to a job, then apply
       /interview-drill   practice coding interviews

Your personal files live in ~/.claude/job-search/ (profile, tracker, practice history).
MSG
