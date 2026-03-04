# Deep Research — Synthesis Rules

How to merge, deduplicate, rank, and generate approaches from the 5 research
agents' findings.

---

## Step 1: Merge

Collect all 5 JSON arrays into a single flat array. Tag each finding with its
source agent:

```json
{
  "agent": "codebase|web-research|tools-mcp|skills|dependencies",
  "relevance": "high|medium|low",
  "source": "...",
  "finding": "...",
  "recommendation": "...",
  "references": ["..."]
}
```

If an agent returned an empty array or failed to respond, note it but continue.
Not every task needs all 5 dimensions — missing results are normal.

---

## Step 2: Deduplicate

Two findings are duplicates if they point to the same solution:
- Web-research recommends library X **and** dependencies agent reports X is already installed
- Codebase agent finds a utility **and** skills agent finds a skill that wraps the same utility
- Multiple web sources recommend the same approach

When merging duplicates:
- Keep the finding with the most specific recommendation
- Note corroboration: "Found by: codebase, web-research" (increases confidence)
- Prefer the installed/available version over the one that requires setup

---

## Step 3: Resolve Conflicts

Common conflict patterns and how to resolve them:

| Conflict | Resolution |
|----------|------------|
| Web recommends library X, but dependencies show incompatible version of peer dep Y | Flag conflict. Note: "X requires Y>=3.0 but project uses Y@2.x. Options: upgrade Y, use alternative Z, or vendor X." |
| Codebase uses pattern A, web recommends pattern B | Prefer codebase pattern for consistency. Note: "Codebase uses A (see files). Web recommends B for [reasons]. Recommend A unless migrating." |
| Two agents recommend different libraries for the same purpose | Present both as options in the approaches. Note adoption, maintenance, and compatibility for each. |
| MCP tool available but web suggests manual approach | Prefer the available tool. Note: "MCP tool {name} already configured — use it instead of manual approach." |
| Skill exists for this but codebase has a custom implementation | Note both. Recommend whichever is more maintained and fits better. |

When a conflict can't be cleanly resolved, surface it explicitly in the report
as a decision point for the user.

---

## Step 4: Filter and Rank

1. **Remove** `low` relevance findings from the user-facing report (keep in
   structured artifact for completeness)
2. **Sort** remaining findings:
   - `high` relevance first, then `medium`
   - Within the same relevance level, sort by corroboration count (more sources = higher)
   - Within the same corroboration, sort by: codebase > dependencies > tools-mcp > skills > web-research
     (local context is more actionable than external suggestions)

---

## Step 5: Generate Approaches

Based on the ranked findings, propose **2-3 approaches**. Each approach should be
a coherent strategy that a developer could follow end-to-end.

### Approach structure:
```
Approach: {name}
Summary: One sentence describing the strategy
Pros: What makes this approach good
Cons: What the downsides are
Supported by: Which findings back this up
Relevant files: Code that would be modified or extended
Dependencies needed: New packages, if any
Estimated complexity: Low / Medium / High
```

### Rules for approach generation:
- **Always include a "leverage existing code" approach** if the codebase agent found
  relevant patterns or utilities. Extending what exists is usually better than
  building from scratch.
- **Always include at least one alternative** that takes a meaningfully different
  direction (different library, different architecture, different trade-off).
- **Minimum 2 approaches**: If findings only support one approach, add a "build from
  scratch / manual implementation" alternative noting the lack of prior art.
- **Never include more than 3 approaches** — too many options create analysis paralysis.
- If one approach clearly dominates, say so. Mark it `recommended: true`.
- If the choice is genuinely a toss-up, say that too and explain what the deciding
  factors would be.

### When to recommend:
- Strongly recommend when: one approach reuses existing code, is well-tested, and
  requires minimal new dependencies.
- Weakly recommend when: the best approach depends on priorities the user hasn't
  stated (speed vs. maintainability, etc.).
- Don't recommend when: approaches are genuinely equivalent — ask the user to decide.

---

## Handling Edge Cases

**No findings at all**: If all 5 agents return empty arrays, the task may be too
novel or too vague. Report: "Research found no directly relevant prior art. This
may require exploratory implementation." Suggest the user break the task into
smaller, more searchable sub-problems.

**One agent dominates**: If only the codebase agent (or only web-research) has
findings, the approaches will naturally be one-dimensional. Note the gap:
"No relevant external libraries found — approaches are based on extending
existing code."

**Conflicting recommendations**: If findings genuinely conflict (e.g., half say
"use library X" and half say "avoid X"), present both sides and make the conflict
a decision point in the approaches rather than hiding it.

**All findings filtered as low relevance**: If all findings are `low` after
filtering, promote the top 3-5 to the report with a note that research confidence
is low. Never present an empty report when findings exist.

**Agent failures**: If one or more agents fail (invalid output, timeout), note
which agents failed in the report header and proceed with available results.
A research report from 3 agents is still valuable.
