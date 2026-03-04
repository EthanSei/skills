---
name: deep-audit
description: >-
  Post-execution deep audit and auto-heal. Spawns 5 specialist sub-agents
  to evaluate code quality, security, test coverage, performance, and
  codebase consistency in parallel, then auto-fixes P1 issues (surfaces P0
  for confirmation), runs /simplify on fixed files, and verifies tests pass.
  Activates after: done implementing, finished, completed task, shipped,
  code review, audit, deep audit, evaluate, post-execution, implementation
  complete, ready to merge, ready to review, all done, closing audit.
allowed-tools: Read Glob Grep Bash Agent Write Edit
metadata:
  version: 0.2.0
---

# Deep Audit

Post-execution audit and auto-heal. Spawns specialist sub-agents to find issues,
then fixes them. Runs after implementation is complete — never during.

## When This Skill Activates

Trigger after execution completes:
- User says: "done", "finished", "all done", "ready to review", "ship it"
- User explicitly requests: "audit", "code review", "evaluate", "deep audit"
- Another skill's closing checklist runs (e.g., TDD closing audit)

Do NOT activate mid-implementation. This skill is a closing gate, not a blocker.

## Phase 1: Context Gathering

Before spawning agents, establish scope:

1. Run `git diff --name-only HEAD` to get the list of changed files. If the working
   tree is clean, use `git diff --name-only HEAD~1` (last commit). If `HEAD~1` fails
   (repo has only one commit), ask the user to specify which files to audit.
2. Capture the repo root: `git rev-parse --show-toplevel`. Pass this as `{repo_root}`
   to the consistency agent in Phase 2.
3. Check for uncommitted changes: `git status --porcelain`. If non-empty, warn the user:
   "Uncommitted changes detected — fix agents will be applied on top of your working
   state. Consider committing or stashing first." Do not block; continue if user agrees.
4. If no git context: ask the user which files or directories to audit.
5. **speak-memory**: If `.speak-memory/index.md` exists and an active story matches
   the current work, read it. Use the story's Current Context and Checklist to
   sharpen the audit scope to relevant modules and behaviors. If `.speak-memory/`
   does not exist, skip this step.
6. If scope exceeds 50 files, ask user to narrow it before proceeding.

Announce: "Starting deep audit across {file_count} files." (substitute the actual count)

## Phase 2: Parallel Audit

Spawn all 5 agents **in a single message** (parallel Agent tool calls). Each agent
returns a JSON findings array — see `references/agent-roles.md` for full prompts.

| Agent | Subagent Type | Focus |
|-------|---------------|-------|
| code-quality | Explore | Naming, complexity, dead code, duplication, patterns |
| security | Explore | OWASP top 10, injection, secrets, auth/authz |
| test-coverage | Explore | Missing tests, edge cases, unhappy paths, assertions |
| performance | Explore | N+1 queries, blocking ops, unnecessary loops, memory |
| consistency | Explore | Reinvented patterns, convention drift, divergence from codebase norms |

All 5 audit agents: tools = `Read, Glob, Grep` (no Bash — avoids approval spam).
The **consistency** agent additionally receives `{repo_root}` so it can search the
broader codebase for established patterns to compare against.

**Required output format** (instruct each agent to return exactly this):
```json
[
  {
    "severity": "P0|P1|P2",
    "file": "relative/path/to/file.ts",
    "line": 42,
    "description": "What the issue is",
    "fix_hint": "How to fix it (specific, actionable)"
  }
]
```

Return empty array `[]` if no findings in that domain.

## Phase 3: Triage

Merge all 5 arrays. Apply severity rubric from `references/scoring.md`:

- **P0** (critical): Security vulnerabilities, data loss risk, broken functionality,
  exposed secrets. **Present to user before fixing.**
- **P1** (major): Missing tests for changed behavior, significant quality defects,
  likely-to-cause-bugs patterns. **Auto-fix without asking.**
- **P2** (minor): Style issues, naming, minor optimizations, informational.
  **Report only — do not fix.**

Sort: P0 → P1 → P2. If P0 + P1 combined exceeds 10 items, present the full list
to the user and ask which 10 to auto-fix. All findings still appear in the final
report — only the selected items are fixed in Phase 4.

## Phase 4: Auto-Heal Loop

Before starting any fixes, capture the pre-audit baseline: `git log -1 --format=%H`.
Save this as `{pre_audit_sha}` for regression checking in Phase 5.

### P0 Handling (user confirmation required)

Present each P0 finding using the format in `references/fix-loop.md` (P0 User Confirmation Flow).
Wait for user input before proceeding.

On "fix": treat as P1 (spawn fix agent below). On "skip" or "manual": log to report.
If the fix agent returns `ESCALATE`, do not re-prompt "fix/skip/manual" — present only
"skip" and "manual" with the escalation reason. Structural changes must be handled outside
the audit loop.

### P1 Auto-Fix (sequential, worktree-isolated)

For each P1 finding, spawn one General-purpose agent with `isolation: "worktree"`.
Run sequentially — do not parallelize fix agents (prevents branch conflicts).

Instruct the fix agent:
- The specific finding: file, line, description, fix_hint
- Apply the **minimal change** that resolves the issue. No refactoring, no cleanup
  beyond the exact fix. Follow code-discipline: change only what's needed.
- Do not delete files, rename modules, or restructure directories — escalate these
  to P0 and surface to user instead.
- Tools: `Read, Edit, Write, Glob, Grep, Bash`

After each fix: the worktree diff is reviewed and merged if clean. If unchanged
after 2 attempts, flag as unresolvable and continue to the next item.

For detailed fix agent prompt templates, worktree merge steps, and retry patterns:
`references/fix-loop.md`.

## Phase 4.5: Simplify Pass

If no files were modified during Phase 4 (all findings were skipped, deferred, or
false positives), skip this phase entirely.

Otherwise, check if `/simplify` is an installed skill. If not installed, skip this
phase and note it in the report. If installed, invoke `/simplify` on every file that
was modified during Phase 4. `/simplify` runs its own 3-agent review (code reuse,
quality, efficiency) and applies any improvements it finds — catching any awkward code
that fix agents introduced while solving a targeted issue.

## Phase 5: Verification

After all fixes and the simplify pass (Phase 4.5) are applied:

1. **Detect test runner**: look for `jest.config.js`, `jest.config.ts`, `vitest.config.*`,
   `pytest.ini`, `pyproject.toml` (containing `[tool.pytest.ini_options]`), `Cargo.toml`,
   `package.json` (with `scripts.test` field), `Makefile` (with `test` target), `build.gradle`.
2. **If found**: run the full test suite. If any tests fail, check out `{pre_audit_sha}`
   (captured at the start of Phase 4) and run tests again to determine if the failure
   is pre-existing. If tests pass at the baseline but fail at HEAD, a fix introduced a
   regression — spawn a targeted fix agent to revert or correct it. Regression fixes
   do not count against the Phase 4 auto-fix budget.
3. **If not found**: spawn a quick Explore agent to spot-check each fixed file for
   obvious syntax errors or broken imports.

Do not skip verification.

## Phase 6: Report

Output a concise summary to the user (use `assets/report-template.md` for formatting):
- Files audited, findings by severity
- What was auto-fixed (P1) with file:line references
- P0 items and their resolution (fixed/skipped/deferred)
- P2 items as a readable list
- Test suite result

**speak-memory**: If an active story was loaded in Phase 1, use Write/Edit to update
the story file — append to Recent Activity and update Current Context.

## Key Constraints

- Audit agents: **Opus** (maximum finding quality). Fix agents: **Opus** (correct edits critical). Verify agent: **Sonnet**.
- Max **2 levels of nesting**: orchestrator → specialist. Specialists never spawn agents.
- Max **10 auto-fixes** per run. Excess P0/P1 items are reported but not fixed.
- Fix agents always run with `isolation: "worktree"` — safe rollback if anything goes wrong.
- Never delete files, rename modules, or restructure in the fix loop — escalate to user.
- Bash removed from audit agents intentionally — prevents approval spam during audit.
- `/simplify` is invoked as Phase 4.5 on all modified files (if installed).

## Closing Checklist

Do not declare the audit done until all boxes are checked:

- [ ] All P0 findings addressed (confirmed fix, or explicitly deferred by user)
- [ ] All P1 findings auto-fixed (or flagged unresolvable after 2 attempts)
- [ ] /simplify run on all modified files (Phase 4.5), or skipped with note if not installed
- [ ] Test suite passes (or no regression vs. pre-audit state)
- [ ] P2 items communicated to user
- [ ] speak-memory story updated (if applicable)

## Reference Files

Load only when needed:

- `references/agent-roles.md` — Full prompt templates for each specialist audit agent
- `references/scoring.md` — P0/P1/P2 rubric with examples and edge cases
- `references/fix-loop.md` — Fix agent templates, retry logic, escalation patterns
- `assets/report-template.md` — Audit report format
