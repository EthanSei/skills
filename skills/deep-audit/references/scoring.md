# Scoring Rubric — Deep Audit

Severity classification for findings from specialist agents. When in doubt, escalate
to the higher severity — the goal is thorough audit, not false reassurance.

---

## Severity Levels

### P0 — Critical (user confirmation required before fixing)

Issues that could cause security incidents, data loss, or broken core functionality.
**Never auto-fix P0.** Surface to user with full context and ask: fix, skip, or manual.

**Security P0:**
- SQL/NoSQL/shell injection via string concatenation with user input
- Hardcoded credentials, API keys, tokens, or private keys in source
- Authentication bypass: missing auth check on protected endpoint
- Sensitive data returned in API responses or logged (passwords, SSNs, tokens)
- Arbitrary file read/write via path traversal with user-supplied input
- Server-side request forgery (SSRF) with no URL allowlist
- Remote code execution via eval/exec with user input

**Quality P0:**
- Function that provably throws/panics on valid inputs (crash bug)
- Data written to wrong destination (wrong table, wrong user's record)
- Critical business logic with zero test coverage and recent changes

**Performance P0:**
- Query or operation with no LIMIT that returns all rows in a large table
- Synchronous blocking call inside Node.js event loop (sync DB call, fs.readFileSync on hot path)

---

### P1 — Major (auto-fix without asking)

Significant issues that degrade reliability, maintainability, or correctness but
don't represent immediate exploits. Fix these with minimal targeted changes.

**Security P1:**
- Defense-in-depth missing: no input validation on API boundary (even if not exploitable today)
- Auth check present but incomplete (checks role but not ownership)
- Sensitive info in error messages returned to client (stack traces, internal paths)
- JWT decoded without signature verification

**Quality P1:**
- Missing error/failure case coverage for any function handling user data or I/O
- Functions over ~50 lines with multiple distinct responsibilities
- Duplicated logic block (3+ identical or near-identical copies)
- Missing null/undefined guard where documented as required

**Performance P1:**
- N+1 query pattern with any collection that could realistically exceed 100 items
- Expensive computation called inside a loop when it could be hoisted

---

### P2 — Minor (report only, never auto-fix)

Issues worth knowing about but not worth automated intervention. Present as a
prioritized list for the user to address at their discretion.

- Naming that misleads but doesn't cause bugs
- Magic numbers/strings (readability issue, not correctness)
- Missing tests for edge cases unlikely to be hit
- Performance micro-optimization with <5% expected impact
- Style deviations from project patterns (single occurrence)
- Informational: this pattern works but a better alternative exists

---

## Adversarial Stance Per Domain

Different agents use different levels of skepticism:

| Agent | Stance | Rationale |
|-------|--------|-----------|
| security | **Fully adversarial** | Assume every unvalidated input is attacker-controlled |
| test-coverage | **Adversarial** | Assume any untested path has a latent bug |
| code-quality | **Lean toward flagging** | Better to over-report than miss real issues |
| performance | **Realistic** | Full adversarial generates too many theoretical findings |
| consistency | **Comparative** | Flag divergences from established codebase patterns, not opinions |

When prompting security agents, frame it as: *"You are an attacker who has read the
source code. What would you exploit?"* — not a polite reviewer looking for suggestions.

---

## Severity Escalation Rules

When an agent is uncertain between two severities, apply these rules:

1. **Security uncertainty**: Always escalate. P1→P0 if there's any realistic attack path.
2. **Coverage uncertainty**: If a function modifies state or handles money/auth/data,
   missing test coverage is P0 not P1.
3. **Quality uncertainty**: Default to P1 if the issue could plausibly cause a bug.
   Default to P2 if it's purely cosmetic.
4. **Performance uncertainty**: Default to P2. Only P1 if measurable under typical load.

---

## Cap and Prioritization

- If total P0 + P1 findings exceed **10**, present the full list and ask the user
  which items to prioritize before entering the fix loop.
- When over the cap, P0 findings always get the fix slots before P1.
- P2 findings are never counted toward the cap — always reported in full.

---

## False Positive Handling

If a fix agent determines a finding is a false positive (the code is actually correct
and the agent misunderstood context), it should:
1. Not make any change
2. Output: `FALSE_POSITIVE: {explanation of why the code is correct}`

The orchestrator logs this and moves to the next finding. False positives count
against the retry budget (max 2 attempts per finding).
