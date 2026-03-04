# Fix Loop — Deep Audit

Patterns for constructing fix agents, passing context, handling retries, and
escalating unfixable issues.

---

## Architecture

The fix loop runs **sequentially** after triage. Each fix agent runs in an isolated
git worktree. One at a time.

```
Orchestrator
  └─ Fix Agent 1 (Sonnet, General-purpose, worktree) → diff reviewed → merged
  └─ Fix Agent 2 (Sonnet, General-purpose, worktree) → diff reviewed → merged
  └─ ...
  └─ /simplify on all modified files (Phase 4.5)
  └─ Verify Agent (Haiku, Explore) OR test runner
```

Worktree isolation:
- Clean rollback if a fix goes wrong — discard the worktree
- Diff is reviewable before merging back to the working branch

---

## Fix Agent Prompt Template

Paste this as the agent `prompt`, substituting `{...}` placeholders. Use
`subagent_type: "general-purpose"`, `isolation: "worktree"`, tools `Read, Edit, Write, Glob, Grep, Bash`.

```
You are a focused code fix agent. Your job is to apply one specific fix.

ISSUE TO FIX
File: {file}
Line: {line}
Problem: {description}
How to fix: {fix_hint}

STRICT RULES (violating any of these is a failure)
1. Make ONLY the change described. Do not refactor, clean up, or improve
   anything beyond the exact fix.
2. Do not rename variables, extract functions, add comments, or fix other
   issues you notice nearby — those belong in a separate task.
3. Do not delete files, rename modules, or restructure directories.
   If the fix requires structural changes, stop immediately and output:
   ESCALATE: <explain why structural change is needed>
4. If after reading the file you believe the finding is a false positive
   (the code is already correct), do not change anything and output:
   FALSE_POSITIVE: <explain why the code is correct>
5. After applying the fix, read the file back to confirm the change landed.

Apply the fix now. Do not explain what you're doing — just do it.
```

---

## Context Efficiency

When a file is large (>200 lines), include the relevant section rather than the
full path alone. Read the file, extract lines `{line-10}` to `{line+20}`, and
include that snippet in the prompt:

```
Relevant code context (lines {start} to {end}):
{code_snippet}
```

This prevents the fix agent from spending tokens reading the full file.

---

## Retry Logic

| Attempt | Action |
|---------|--------|
| 1st | Spawn fix agent with standard prompt |
| No change detected | Re-read the file; if unchanged, retry with added context (lines {line-20} to {line+20} included as a snippet in the prompt) |
| 2nd (if file still unchanged) | Flag as UNRESOLVABLE and continue |
| ESCALATE output | Surface to user as a new P0 item |
| FALSE_POSITIVE output | Log as resolved (false positive), continue |

Detecting "no change": after the fix agent completes, run `git diff HEAD` in the
working tree (or compare the file's content before vs. after). If no lines changed
in the target file, treat it as "no change" regardless of what the fix agent reported.
Semantic checking (e.g., "did validation appear?") is optional context for retry prompts.

---

## Escalation

An ESCALATE signal from a fix agent means the fix requires structural or
architectural changes beyond a targeted edit. Handle it as:

1. Elevate to a new P0 finding (overrides the original P1 classification)
2. Surface to user: "Fix for {file}:{line} requires {reason}. Handle manually?"
3. Log in report under "Escalated to User"
4. Continue to the next fix

---

## P0 User Confirmation Flow

For each P0 finding, present in this exact format before spawning any fix agent:

```
[P0] {domain} — {file}:{line}
  Problem: {description}
  Fix: {fix_hint}

  Options:
  1. fix — spawn a fix agent now
  2. skip — record as known issue, move on
  3. manual — I'll handle this myself, mark as deferred

Choice [fix/skip/manual]:
```

- **fix**: use the same General-purpose fix agent pattern as P1
- **skip**: log in report as "Known Issue (skipped)"
- **manual**: log in report as "Deferred to user"

Wait for user input. Do not proceed until answered.

---

## Fix Order Optimization

This skill spawns **one fix agent per finding** (not one per file). Since each agent
runs sequentially and its worktree is created from the current HEAD *after* the
previous fix is merged, line numbers remain accurate at the time each agent starts.

If you ever batch multiple findings into a single agent (e.g., to save agent overhead
for trivial adjacent fixes), apply edits in **reverse line order** within that session
(highest line number first) to prevent earlier edits from shifting later line references.

Example: batching fixes for lines 47, 83, and 120 of `auth.ts` → apply 120 → 83 → 47.

---

## Worktree Merge Process

After each fix agent completes in its worktree:

1. Review the diff: `git diff HEAD...{worktree-branch}` — confirm: (a) only the
   target file(s) changed, (b) no unrelated deletions, (c) no file renames
2. If diff looks clean: merge back (`git merge --ff-only {worktree-branch}`)
3. If diff has unexpected changes: discard the worktree, flag as UNRESOLVABLE,
   surface the finding to the user with the unexpected diff attached
4. The worktree is automatically cleaned up after merge or discard

This gives you a clear, reviewable paper trail of every change the audit applied.

---

## Post-Fix Verification

After all fix agents complete, the orchestrator runs verification:

**If test runner detected:**
```bash
# Use whichever is appropriate for the project:
pytest                          # Python
npm test / npx jest             # JavaScript/TypeScript
cargo test                      # Rust
go test ./...                   # Go
```

Read the output. If tests pass: ✓ proceed to report.
If tests fail: check if the failure existed before the audit by running
`git stash list` to see if there's a pre-audit state, or compare against the
last clean commit with `git diff HEAD~1 -- {failing_file}`. Do NOT run
`git stash` (risks hiding uncommitted work). If the fix introduced the
regression, spawn a targeted fix agent to revert or correct it.

**If no test runner (Explore spot-check):**
Spawn a Haiku Explore agent with the fixed file list and the verify agent prompt
from `references/agent-roles.md`.

---

## Large Repo Considerations

Worktree isolation is the default and recommended mode. However, on repos where
`git worktree add` is slow (large LFS files, deep history, many submodules, or
node_modules not in .gitignore), 10 sequential fix agents each creating a worktree
can add significant wall-clock time.

**When to skip worktrees:**
- Repo takes >10s to create a worktree (test with `time git worktree add /tmp/test-wt HEAD`)
- CI environment with ephemeral workspaces (rollback is always available via reset)
- User explicitly says speed matters more than isolation

**Direct-edit fallback (no worktree):**
Omit `isolation: "worktree"` from the Agent call. Fix agents write directly to the
working branch. To preserve rollback ability, note the current HEAD before starting:

```bash
git rev-parse HEAD  # save this as {pre_audit_sha}
```

If a fix goes wrong, the orchestrator can revert with:
```bash
git revert {bad_commit} --no-edit
# or, to reset all audit fixes at once:
git reset --hard {pre_audit_sha}
```

Surface the fallback choice to the user only when worktree creation is detectably
slow — do not default to it. The diff-review safety net is lost without worktrees.
