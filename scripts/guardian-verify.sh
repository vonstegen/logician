#!/bin/bash
# guardian-verify.sh — Canonical State Guardian
# Prevents Matrix/Ele­ment X gateway hallucinations by forcing
# verification of filesystem, git state, and key files before reporting success.
# Use after any write_file, git, or major operation when responding via Matrix.

set -euo pipefail

ACTION="${1:-Unspecified operation}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOGFILE="research/gateway-desync.log"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 CANONICAL STATE GUARDIAN v0.1                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Time: $TIMESTAMP"
echo "║ Claimed action: $ACTION"
echo "║ Working dir: $PROJECT_ROOT"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "Git State:"
git status --short || echo "Not a git repo or git error"

echo -e "\nKey File Verification:"
declare -a KEY_FILES=(
  "research/RESEARCH-LOG.md"
  "DAILY-CHECKLIST.md"
  "ROADMAP.md"
  "experiments/energy-optimization-001/README.md"
  "hardware-roster.md"
)

for file in "${KEY_FILES[@]}"; do
  if [ -f "$file" ]; then
    SIZE=$(wc -c < "$file")
    MOD=$(stat -c %y "$file" 2>/dev/null | cut -d. -f1 || echo "unknown")
    echo "✓ $file  ($SIZE bytes, $MOD)"
  else
    echo "✗ $file — MISSING"
  fi
done

echo -e "\nUncommitted changes detected: $(git status --porcelain | wc -l) file(s)"

if git status --porcelain | grep -q .; then
  CONCLUSION="DESYNC DETECTED — uncommitted changes or untracked files present. Run git add/commit before claiming success on Matrix."
  STATUS="DESYNC"
else
  CONCLUSION="VERIFIED — Canonical state is clean. Safe to report success."
  STATUS="VERIFIED"
fi

echo -e "\nCONCLUSION: $CONCLUSION"

# Log the verification
mkdir -p research
echo "[$TIMESTAMP] $STATUS | $ACTION" >> "$LOGFILE"
echo "Logged to $LOGFILE"

echo -e "\nUsage reminder: Always run './scripts/guardian-verify.sh \"description of what you claim to have done\"' before Matrix responses."
echo "This grounds VIGIL as the canonical fixed point."
