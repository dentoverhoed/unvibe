#!/usr/bin/env bash
# Stop hook: the agent can't finish its turn while the skill checks fail.
# Exit 2 tells Claude Code to block the stop and show stderr to the agent.
input="$(cat)"
cd "$(dirname "$0")/../.." || exit 0
for py in python3 python py; do
  # Skip stubs that exist but don't run (e.g. the Windows Store python3).
  if "$py" -c "" >/dev/null 2>&1; then
    "$py" scripts/check_skill.py 1>&2 && exit 0
    # Already continuing because of this hook: block once, never loop.
    if printf '%s' "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
      echo "check-skill hook: checks still fail; stopping anyway so the user can decide" >&2
      exit 0
    fi
    exit 2
  fi
done
echo "check-skill hook: no working Python found, skipping" >&2
exit 0
