# Deep Research — Synthesis Rules

How to merge, grade, rank, and generate approaches from the research swarm's
evidence-tagged findings.

---

## Step 1: Merge

Collect all 5 JSON arrays into a single flat array. Tag each finding with its
source agent:

```json
{
  "agent": "codebase|web-research|tools-mcp|skills|dependencies",
  "evidence_tier": "primary|secondary|speculative",
  "relevance": "high|medium|low",
  "source": "...",
  "finding": "...",
  "supports_hypothesis": "...",
  "recommendation": "...",
  "references": ["..."]
}
```

If an agent returned an empty array or failed to respond (invalid output, timeout),
note which agents failed and continue. A synthesis from 3 agents is still valuable.

---

## Step 2: Deduplicate

Two findings are duplicates if they point to the same solution:
- Web-research recommends library X **and** dependencies agent reports X is already installed
- Codebase agent finds a utility **and** skills agent finds a skill wrapping the same utility

When merging duplicates:
- Keep the finding with the highest evidence tier
- Note corroboration: "Found by: codebase [primary], web-research [secondary]"
- Corroboration from multiple agents at primary/secondary tier increases confidence

---

## Step 3: Resolve Conflicts

| Conflict | Resolution |
|----------|------------|
| Web recommends library X, dependencies show incompatible peer dep | Flag conflict. Note options: upgrade dep, use alternative, or vendor |
| Codebase uses pattern A, web recommends pattern B | Prefer codebase pattern for consistency unless migration is justified |
| Two agents recommend different libraries for same purpose | Present both in approaches with evidence tiers for each |
| MCP tool available but web suggests manual approach | Prefer available tool. Note: "already configured — use it" |

When a conflict can't be cleanly resolved, surface it explicitly as a decision
point in the verdict.

---

## Step 4: Grade Evidence

This is the critical step that distinguishes deep-research from open-ended exploration.

### Evidence quality rules:
1. **A conclusion needs at least one primary or secondary source.** If a conclusion
   rests entirely on speculative findings, flag it: "LOW CONFIDENCE — speculative only."
2. **Primary evidence outweighs secondary.** Code you read > blog post about code.
3. **Multiple secondary sources ≈ one primary source.** Three independent blog posts
   confirming the same thing is credible.
4. **Speculative evidence is context, not proof.** Include it for completeness but
   never let it be the sole basis for a recommendation.
5. **Corroboration across agents increases confidence.** Codebase [primary] + web
   [secondary] confirming the same pattern = high confidence.

### Confidence assessment:
- **High confidence**: Multiple primary sources, or primary + secondary corroboration.
  No credible disconfirming evidence.
- **Medium confidence**: At least one primary or multiple secondary sources.
  Minor uncertainties or untested assumptions.
- **Low confidence**: Mostly secondary/speculative. Significant gaps. Conclusion
  may change with more investigation.

---

## Step 5: Rank

1. **Sort by evidence tier**: primary first, then secondary, then speculative
2. **Within same tier**: sort by relevance (high > medium > low)
3. **Within same relevance**: sort by corroboration count
4. **Drop low-relevance speculative findings** from the user-facing report
   (keep in structured artifact for completeness)

---

## Step 6: Form Preliminary Conclusion

For each hypothesis from Phase 1:

1. Collect all findings tagged with `supports_hypothesis` matching this hypothesis
2. Assess: does the evidence confirm or change the prior belief?
3. State the conclusion with its confidence level and evidence tier breakdown

Format:
```
Hypothesis 1: {question}
Prior belief: {what we expected}
Conclusion: {confirmed|changed|inconclusive}
Evidence: {N} primary, {N} secondary, {N} speculative
Confidence: {high|medium|low}
Summary: {one sentence}
```

---

## Step 7: Generate Approaches

Based on the evidence-graded findings, propose **2-3 approaches**.

### Approach structure:
```
Approach: {name}
Summary: One sentence describing the strategy
Pros: What makes this approach good
Cons: What the downsides are
Evidence: Which findings support this, with tier tags
Relevant files: Code that would be modified or extended
Dependencies needed: New packages, if any
Estimated complexity: Low / Medium / High
```

### Rules:
- **Always include a "leverage existing code" approach** if the codebase agent found
  relevant patterns (with primary evidence). Extending what exists is usually better.
- **Always include at least one alternative** that takes a meaningfully different direction.
- **Minimum 2 approaches**: If findings only support one, add a "build from scratch"
  alternative noting the lack of prior art.
- **Never include more than 3 approaches** — analysis paralysis.
- **Evidence-backed recommendations only**: An approach supported by primary evidence
  ranks higher than one supported only by secondary/speculative.
- If one approach clearly dominates on evidence quality, recommend it.

### When to recommend:
- Strongly recommend when: primary evidence supports it, reuses existing code,
  minimal new dependencies.
- Weakly recommend when: secondary evidence only, or depends on unstated priorities.
- Don't recommend when: evidence is inconclusive — ask the user to decide.

---

## Handling Edge Cases

**No findings at all**: Task may be too novel or vague. Report: "Research found no
directly relevant prior art. Confidence: low. Recommend exploratory implementation
or breaking the task into smaller, more searchable sub-problems."

**All findings speculative**: Flag prominently: "All evidence is speculative — no
primary or secondary sources confirm these findings. Treat conclusions as hypotheses
to test, not validated recommendations."

**One agent dominates**: Note the gap: "No relevant external libraries found —
approaches based on codebase evidence only."

**Conflicting recommendations**: Present both sides as a decision point. Never hide
a conflict to make the recommendation appear cleaner.

**Agent failures**: Note which agents failed in the report. Adjust confidence
downward if a key agent (e.g., codebase for implementation tasks) failed.
