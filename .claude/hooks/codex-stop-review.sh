#!/usr/bin/env bash
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

cd "$ROOT" || exit 0

STOP_HOOK_ACTIVE="$(
  python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null || true
)"

if [[ "$STOP_HOOK_ACTIVE" == "true" ]]; then
  exit 0
fi

if git diff --quiet --exit-code \
  && git diff --cached --quiet --exit-code \
  && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  exit 0
fi

# Model selection: honour the same env-var override hierarchy as invoke-cross-reviewer.sh
# (AI_REVIEW_MODEL → CODEX_REVIEW_MODEL → hardcoded default).
REVIEW_MODEL="${AI_REVIEW_MODEL:-${CODEX_REVIEW_MODEL:-gpt-5.5}}"

PROMPT="You are a read-only reviewer. Run 'git status --short', 'git diff --stat',
'git diff', 'git diff --cached', and 'git ls-files --others --exclude-standard'
to inspect all uncommitted changes (staged and untracked). Assess whether the
changes are coherent, correct, and free of obvious problems (security issues,
missing tenant_id scoping, business logic in routes instead of services,
missing tests, unnecessary complexity).
Start your response with exactly one word: APPROVE (if everything looks fine)
or FIX (if there are issues). After FIX list the specific problems concisely.
Do not modify any files."

# Inner timeout must be shorter than the outer hook timeout (settings.json: 150 s)
# so the advisory FIX output can be produced before the process is killed.
INNER_TIMEOUT=120

OUTPUT_FILE="$(mktemp)"
RAW_OUTPUT="$(
  timeout "$INNER_TIMEOUT" codex exec -s read-only \
    -c model_reasoning_effort=\"low\" \
    -m "$REVIEW_MODEL" \
    --output-last-message "$OUTPUT_FILE" \
    "$PROMPT" 2>&1
)"
STATUS=$?
OUTPUT="$(cat "$OUTPUT_FILE" 2>/dev/null || true)"
rm -f "$OUTPUT_FILE"

if [[ $STATUS -eq 124 ]]; then
  OUTPUT="FIX
Codex review timed out after ${INNER_TIMEOUT} seconds."
elif [[ $STATUS -ne 0 ]]; then
  OUTPUT="FIX
Codex review command failed with exit code $STATUS.

$RAW_OUTPUT"
elif [[ "$OUTPUT" != APPROVE* && "$OUTPUT" != FIX* ]]; then
  OUTPUT="FIX
Codex reviewer returned a non-standard verdict. Raw output:

${OUTPUT:-$RAW_OUTPUT}"
fi

REVIEW_OUTPUT="$OUTPUT" python3 - <<'PY'
import json
import os

message = "Codex read-only cross-review verdict:\n" + os.environ["REVIEW_OUTPUT"]
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": message,
    }
}))
PY
