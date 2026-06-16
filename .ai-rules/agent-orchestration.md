# Agent Orchestration

Use this file at the **start of every non-trivial task**. It complements
tool-specific entry points (`AGENTS.md`, `CLAUDE.md`) and binding rules in other
`.ai-rules/` files.

## 1. Classify the task

| Type | Examples | Load first |
|------|----------|------------|
| Bug fix | Wrong status code, regression | `tdd-and-regression.md`, `context-map.md` |
| Feature | New endpoint, service workflow | `spec-driven-development.md`, `incremental-work.md` |
| Refactor | Rename, extract, no behavior change | `incremental-work.md`, `architecture.md` |
| Security | Auth, uploads, webhooks | `threat-modeling.md`, `security.md` |
| Infra | Docker, CI, Makefile | `docker.md`, `context-map.md` |
| Docs / status | README, ROADMAP, tracking files | `documentation.md`, `review.md` |
| Template clone | New product from this repo | `template-onboarding.md` |
| Roadmap / debt | ROADMAP.md or TECH_DEBT.md item | `planning-and-task-breakdown.md`, `incremental-work.md` |

## 2. Load relevant rules

- Read `.ai-rules/context-map.md` and open the listed files for this task type.
- Read binding rules that apply (architecture, testing, security, git, etc.).
- Optional: use a persona from `agents/` for review-only work (see
  `docs/ai-workflows.md`).

## 3. Define scope

- State the **objective** in one sentence.
- List **in scope** and **out of scope** explicitly.
- Do not expand scope (no drive-by refactors, no unrelated docs, no P3 work
  unless requested).

## 4. Run the anti-overengineering check

Before adding files, dependencies, abstractions, or large rewrites, apply
`.ai-rules/anti-overengineering.md`:

- Can existing code or project patterns solve this?
- Can code be deleted or simplified instead of added?
- Is a new dependency, file, abstraction, or generic framework actually needed?
- Are security, validation, errors, tests, tenancy, and production safety still
  covered?

## 5. List assumptions

- Note defaults you are using (tenant model, env, API version `/api/v1`).
- If blocked on a product decision, ask **one** focused question; otherwise
  proceed with the smallest safe default and document it.

## 6. Pick validation commands

| Change type | Minimum validation |
|-------------|-------------------|
| Application code / tests / migrations | `make validate` |
| CI / scripts / policy only | `make policy-guards` and `make validate-ai-workflows` |
| Docs / AI rules only | `make validate-ai-workflows`; run `make validate` if docs claim test counts |
| Docker / Compose | `make validate` if app touched; else build smoke as needed |

## 7. Execute incrementally

Follow `.ai-rules/incremental-work.md` and `.ai-rules/planning-and-task-breakdown.md`.

## 8. Report completion

For every non-trivial task that changes files, the Builder Agent MUST
automatically run a read-only Reviewer before the final response. Do not ask
the user whether to run review, and do not require a second user prompt,
pasted handoff, local runner command, or separate CLI window.

### Reviewer selection (cross-provider first, same-provider fallback)

Prefer **cross-provider review**: a different AI provider/CLI than the
Builder reviews the diff. See `.ai-rules/model-routing.md` §7 for why, and
`docs/two-agent-review-workflow.md` "Verification status" for what is and is
not confirmed to work in a given environment.

**When running under Codex CLI (Builder = Codex):**

1. For non-trivial tasks, first try:
   `scripts/ai/invoke-cross-reviewer.sh claude [handoff-file]`
2. If the Claude CLI is unavailable, or its non-interactive mode is
   unavailable, or the script exits non-zero: fall back to native
   same-provider `codex review --uncommitted` via
   `scripts/ai/invoke-cross-reviewer.sh codex [handoff-file]`. The script
   invokes Codex with global `-s read-only -a never`.
3. Do not apply Reviewer feedback automatically.
4. Present the Reviewer's output to the user as-is.
5. Apply fixes only after the user explicitly approves them.

**When running under Claude Code (Builder = Claude):**

1. For non-trivial tasks, first try:
   `scripts/ai/invoke-cross-reviewer.sh codex [handoff-file]`
2. If the Codex CLI is unavailable, or its non-interactive mode is
   unavailable, or the script exits non-zero: fall back to the
   `code-reviewer` subagent configured in `.claude/agents/code-reviewer.md`.
3. Do not apply Reviewer feedback automatically.
4. Present the Reviewer's output to the user as-is.
5. Apply fixes only after the user explicitly approves them.

**When running under Cursor (Builder = Cursor):**

- Follow this same decision tree where the environment allows running the
  cross-reviewer script or a native subagent.
- If Cursor cannot spawn either a cross-provider or same-provider Reviewer
  automatically, produce the `.commands/builder-handoff.md` handoff and tell
  the user how to run `scripts/ai/invoke-cross-reviewer.sh <claude|codex>`
  manually, or to use the other tool's CLI directly.

### Reviewer behavior (all paths)

- The Reviewer is read-only and must inspect the current git diff, untracked
  files, validation output, security and production risks, overengineering,
  tests, docs drift, and scope creep.
- The Builder must wait for the Reviewer result before final response.
- Read-only or trivial tasks may skip Reviewer, but MUST explicitly say
  `Reviewer skipped: <reason>`.
- `.commands/builder-handoff.md` remains the Builder handoff format when a
  structured handoff is needed; do not duplicate that template here.
- For model/tier selection of both Builder and Reviewer, see
  `.ai-rules/model-routing.md`.

Every task response MUST include the sections in **`.ai-rules/learning-mode.md`**
(for non-trivial file-changing tasks) and at minimum:

- **Files changed** (created / modified)
- **Tests / validation run** (exact commands and pass/fail)
- **Risks** (deployment, security, migration, compatibility)
- **Remaining work** (if any; do not invent follow-ups)
- **Builder summary** (what changed and why)
- **Reviewer verdict** (or explicit skip reason for read-only/trivial tasks)

See `learning-mode.md` for mentor sections: why each file, what calls it, what
could break, manual verification, interview-defense explanation.

## 9. Git workflow

Follow `.ai-rules/git.md`: no commit, push, merge, force-push, or branch delete
unless the user explicitly writes `approve`.

Before any commit:

1. Draft the exact subject and body (Conventional Commits).
2. Show or verify that message with the user when they requested a commit.
3. Confirm it contains **no** AI attribution trailers (`Co-authored-by: Cursor`,
   `Co-authored-by: Claude`, `Generated-by:`, `Created-by: AI`, etc.).
4. Run `bash scripts/ci/check_no_ai_commit_trailers.sh --message-file <file>`
   on the proposed message, or inspect `git log -1 --pretty=format:%B` after
   commit and before push.
5. Run `make policy-guards` before push when the branch includes new commits.

Install the commit-msg hook once per clone:
`uv run pre-commit install --hook-type commit-msg`.
