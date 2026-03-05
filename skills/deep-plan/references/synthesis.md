# Deep Plan — Synthesis Rules

How to merge, deduplicate, resolve tensions, rank, and generate a coherent
architecture from the planning swarm's recommendations.

---

## Step 1: Merge

Collect all 5 JSON arrays into a single flat array. Tag each recommendation with
its source agent:

```json
{
  "agent": "api-interface|data-architecture|security-reliability|performance-scalability|testability-maintainability",
  "priority": "critical|important|nice-to-have",
  "concern": "...",
  "recommendation": "...",
  "rationale": "...",
  "trade_offs": "...",
  "affected_files": ["..."],
  "references": ["..."]
}
```

If an agent returned an empty array or failed to respond (invalid output, timeout),
note which agents failed and continue. A synthesis from 3 agents is still valuable.

---

## Step 2: Deduplicate

Two recommendations are duplicates if they address the same architectural decision:
- API agent recommends input validation **and** security agent recommends the same validation
- Data agent recommends an index **and** performance agent recommends the same index
- Multiple agents flag the same module boundary or responsibility split

When merging duplicates:
- Keep the recommendation with the highest priority
- Note corroboration: "Recommended by: api-interface, security-reliability"
- Corroboration from 2+ agents at critical/important priority increases confidence

---

## Step 3: Identify Tensions

Tensions occur when one agent's recommendation conflicts with another's. Common patterns:

| Tension | Example | Resolution Strategy |
|---------|---------|-------------------|
| Performance vs simplicity | Caching adds complexity but improves speed | Defer caching unless performance constraint requires it now |
| Security vs DX | Strict validation adds friction for developers | Default to strict; provide convenience wrappers for common cases |
| Flexibility vs consistency | New pattern would be cleaner but breaks codebase conventions | Follow existing patterns; note the improvement as future tech debt |
| Normalization vs query speed | Normalized schema requires expensive joins | Start normalized; denormalize only where measured bottleneck exists |
| Testability vs minimal code | Dependency injection adds abstraction for testability | Use DI at module boundaries; avoid over-abstracting internals |

### Tension detection heuristics:
1. Two agents recommend different approaches for the same component
2. One agent's recommendation creates a constraint that another's recommendation violates
3. An agent explicitly notes a trade-off that degrades another agent's quality attribute

### When tension is found:
- **Clear winner**: One recommendation has codebase evidence (existing pattern), the other
  is theoretical. Follow the existing pattern and note the alternative.
- **Genuine trade-off**: Both sides have merit. Surface as a decision point in the plan
  with pros/cons for each option. Do not hide trade-offs.
- **Scope conflict**: One agent wants a larger scope than the constraints allow. Defer
  the larger scope to a future iteration.

---

## Step 4: Resolve or Surface

| Resolution | When to use |
|------------|-------------|
| Resolve with rationale | One option clearly dominates on evidence + constraints |
| Surface as decision point | Genuine trade-off that depends on user priorities |
| Defer to later iteration | Recommendation is valid but not essential for initial implementation |
| Discard | Low-priority recommendation that conflicts with a critical one |

Resolved tensions become part of the "Key Decisions" section in the plan.
Surfaced tensions become decision points the user must weigh.
Deferred items go into a "Future Considerations" note.

---

## Step 5: Rank

1. **Sort by priority**: critical first, then important, then nice-to-have
2. **Within same priority**: sort by corroboration count (more agents = higher)
3. **Within same corroboration**: sort by number of affected files (wider impact = higher)
4. **Drop low-priority items** if count exceeds 25 — nice-to-have items first

---

## Step 6: Generate Architecture

Based on the ranked, deduplicated, tension-resolved recommendations, produce
a coherent architecture. This is the critical synthesis step — individual
recommendations must be assembled into a design that works as a whole.

### Architecture structure:
```
Overview: One paragraph describing the architecture
Components:
  - Name, responsibility, interfaces, dependencies
  - For each component: which agent recommendations it implements
Data Model:
  - Entities, relationships, key constraints
  - Migration strategy (if schema changes are needed)
API Surface:
  - Public interfaces, endpoints, or contracts
  - Error handling strategy
Key Decisions:
  - Each major architectural choice
  - Rationale (referencing specialist recommendations)
  - Alternatives considered (from tensions)
  - Trade-offs accepted
```

### Rules:
- **Follow existing codebase patterns** unless a critical recommendation justifies
  diverging. When diverging, state why explicitly.
- **Minimum viable architecture**: Include only what's needed for the stated requirements.
  Everything else is deferred. Three simple components are better than a premature
  microservice split.
- **Every component must have a clear owner** — one agent's concern should dominate
  each component's design, even if others contribute constraints.
- **Include 1-2 alternatives** only for decision points where genuine tensions exist.
  Do not generate alternatives for decisions where one option clearly dominates.
- **Ground in evidence**: Every decision should reference the specialist recommendation(s)
  that support it, with the agent name in brackets.

### Implementation checklist generation:
After the architecture, produce an ordered implementation checklist:
1. Order by dependency: foundational components first, dependent components later
2. Each step specifies: what to build, which files to create/modify, what to test
3. First step should always be the data model or core types (other components depend on them)
4. Last step should be integration testing across components

---

## Handling Edge Cases

**No recommendations at all**: Feature may be too simple for formal planning. Report:
"No architectural concerns identified. This feature appears straightforward enough to
implement directly."

**All recommendations nice-to-have**: No critical architecture decisions needed. Report
as low-priority planning and suggest proceeding with implementation.

**One agent dominates**: Note the gap: "Architecture plan driven primarily by {agent}
analysis. {missing_agent} perspective was empty — consider whether {concern} was
adequately addressed."

**Conflicting critical recommendations**: This is a real architectural tension. Never
auto-resolve critical-vs-critical conflicts. Surface both options with full context
and let the user decide.

**Agent failures**: Note which agents failed in the plan. If a critical-concern agent
(security, data) failed, recommend re-running before implementing.
