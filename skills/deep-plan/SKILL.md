---
name: deep-plan
description: >-
  Multi-perspective architecture planning swarm. Spawns 5 specialist agents
  (API design, data architecture, security, performance, maintainability) to
  evaluate trade-offs from different quality-attribute perspectives, then a
  trade-off arbiter stress-tests the plan before producing an implementation-ready
  architecture decision record. Activates on: plan, architect, design, deep plan,
  architecture, system design, technical design, how should I architect,
  implementation plan, API design, data model, component design.
allowed-tools: Read Glob Grep Bash Agent Write Edit WebSearch WebFetch ListMcpResourcesTool ReadMcpResourceTool
metadata:
  version: 0.1.0
---

# Deep Plan

Multi-perspective architecture planning. Spawns specialist agents for different
quality-attribute concerns that evaluate trade-offs before you write code.

## When This Skill Activates

Trigger on architecture and planning requests:
- User says: "plan", "architect", "design", "how should I architect..."
- User asks: "deep plan", "plan the architecture", "technical design"
- User wants pre-implementation architecture evaluation

Do NOT activate on every task. This is for deliberate architecture planning, not
quick feature additions. Simple features don't need a 6-agent swarm.

## Phase 1: Context Gathering

Before spawning agents, establish scope:

1. **Check for deep-research artifact**: Scan recent conversation context for the
   structured JSON artifact from deep-research (contains task, tech_stack, approaches,
   findings, verdict). Validate the artifact has at minimum: `task`, `tech_stack`,
   and at least one approach with a summary. If any required field is missing or
   empty, treat as if no artifact was found and fall through to step 2. If valid,
   use it as primary input — skip step 2 and use the recommended approach as the
   starting architecture to evaluate.
2. **If no artifact**: Gather context manually:
   - Run `git rev-parse --show-toplevel` for `{repo_root}`
   - Check for package manifests to identify `{tech_stack}`. If no manifests are
     found, infer tech_stack from primary file extensions (`.py`, `.ts`, `.go`, etc.)
     or ask the user. Never pass an empty tech_stack to planning agents.
   - Ask the user what they're building and what constraints matter most
   - Read existing code in the affected area to understand current architecture
3. **speak-memory**: If `.speak-memory/index.md` exists and an active story matches,
   read it for context. Skip if `.speak-memory/` does not exist.
4. **Frame the architecture**: State what is being planned:
   - **Feature/System**: What is being designed
   - **Scope**: Which components, modules, or layers are affected
   - **Constraints**: Performance targets, security requirements, compatibility needs
   - **Starting approach**: From deep-research artifact, or from user description
5. **Set scope budget**: "Budget: 5 planning specialists + 1 trade-off arbiter = 6
   agent calls." Present to user:

```
Planning: {feature/system}
Scope: {components affected}
Constraints: {key constraints}
Starting approach: {from research or user}

Agents: API design, data architecture, security, performance, maintainability
        + 1 trade-off arbiter = 6 calls.
Proceed?
```

Wait for user confirmation before spawning agents. If the user declines or asks to
revise, update the scope, constraints, or starting approach and re-present. Do not
spawn agents until the user confirms. If the user cancels entirely, output:
"Planning cancelled by user." and stop.

## Phase 2: Parallel Planning

Spawn all 5 specialist agents **in a single message** (parallel execution). Each
agent analyzes the architecture from their quality-attribute perspective and grounds
recommendations in the existing codebase.

See `references/agent-roles.md` for full prompts.

| Agent | Subagent Type | Model | Perspective |
|-------|---------------|-------|-------------|
| api-interface | Explore | opus | Contracts, boundaries, DX, versioning, error handling |
| data-architecture | Explore | opus | Schema design, storage, migrations, consistency, relationships |
| security-reliability | Explore | opus | Threat model, auth/authz, failure modes, availability |
| performance-scalability | Explore | opus | Bottlenecks, caching, concurrency, resource usage |
| testability-maintainability | Explore | opus | Complexity, testing strategy, extensibility, edge cases |

**Agent tool grants**: All planning agents get `Read, Glob, Grep` (read-only
codebase exploration). They analyze the existing codebase to ground their
recommendations in what already exists.

**Required output format** (every recommendation must include `priority`):
```json
[
  {
    "priority": "critical|important|nice-to-have",
    "concern": "which quality attribute this addresses",
    "recommendation": "what the architecture should do",
    "rationale": "why, grounded in codebase evidence or established practice",
    "trade_offs": "what this costs or constrains",
    "affected_files": ["files that would be created or modified"],
    "references": ["codebase files or patterns referenced"]
  }
]
```

**Priority levels:**
- **critical**: Architecture cannot succeed without this. Missing it causes failure.
- **important**: Significantly improves the architecture. Missing it creates tech debt.
- **nice-to-have**: Good practice but not essential for initial implementation.

Return empty array `[]` if no recommendations for that perspective.

Each agent: max 10 recommendations, prioritized. Never tag nice-to-have as critical.

**Error handling**: If an agent returns non-JSON output, strip code fences and attempt
JSON extraction. If extraction fails or the agent times out, treat as empty array `[]`
and log a warning. Continue with results from agents that succeeded.

## Phase 3: Synthesis

Merge all 5 recommendation arrays. Apply synthesis rules from `references/synthesis.md`:

1. **Merge**: Collect all 5 arrays, tag each with source agent name. Note which
   agents failed or returned empty.
2. **Deduplicate**: Merge overlapping recommendations; note corroboration from
   multiple agents as a confidence signal.
3. **Identify tensions**: Flag where agents' recommendations conflict — Agent A wants
   X but Agent B wants Y and they are mutually exclusive or in friction.
4. **Resolve or surface**: Resolve clear tensions (with rationale). Surface genuine
   trade-offs as explicit decision points the user must weigh.
5. **Rank**: Sort by priority (critical first), then corroboration count.
   Cap at **25 recommendations** — drop low-priority nice-to-have items first.
6. **Generate architecture**: Propose the architecture as a coherent design that
   integrates the ranked recommendations. Include 1-2 alternatives for major decision
   points where unresolved tensions exist.

## Phase 4: Trade-off Arbiter

Spawn one **trade-off arbiter** agent (`subagent_type: "general-purpose"`, `model: "opus"`).

Give it:
- The synthesized architecture from Phase 3
- All unresolved tensions
- The original constraints and scope

The arbiter's job is NOT to disprove the plan (unlike a devil's advocate). It is to:
- Identify **cross-cutting tensions** where improving one quality attribute degrades another
- Find **missing failure modes** — what happens when things go wrong?
- Challenge **complexity assumptions** — is this over-engineered for the actual requirements?
- Suggest **simplifications** — can anything be deferred to a later iteration?

See `references/agent-roles.md` for the full arbiter prompt.

Handle the arbiter result:
- **`plan_sound`**: The architecture holds. Note any flagged tensions as known trade-offs.
  Still integrate non-empty `missing_failure_modes` into the Risks section and
  `codebase_contradictions` as caveats in the relevant Key Decisions.
- **`plan_over_engineered`**: Simplify. For each item in `over_engineering`, remove or
  defer the flagged component from the architecture. Directly rewrite the affected
  architecture sections — do not re-run synthesis or spawn new agents.
- **`plan_has_gaps`**: Critical gaps found. Map arbiter fields to plan sections:
  `missing_failure_modes` → add to Risks and Mitigations table;
  `codebase_contradictions` → add corrective notes to the relevant Key Decisions.
  Mark all additions with "[arbiter]" tags.

If `arbiter_result` is not one of the three recognized values, treat as the arbiter
error case below.

**Error handling**: If the arbiter fails (non-JSON output, timeout, invalid structure,
or unrecognized `arbiter_result`), log a warning: "Trade-off arbiter failed — plan not
stress-tested." Add a risk item to the plan: "Architecture not stress-tested due to
arbiter failure — increased risk of over-engineering or missing failure modes." Set
`metadata.arbiter_completed` to `false` in the structured artifact. Continue to Phase 5.

## Phase 5: Plan Delivery

Output the architecture plan using `assets/plan-template.md` format (MADR-inspired):

1. **Context and problem statement** — what is being built and why
2. **Decision drivers** — constraints and quality attributes that matter most
3. **Architecture overview** — the recommended design (components, data model, API surface)
4. **Key decisions** — each major choice with rationale and alternatives considered
5. **Implementation checklist** — ordered steps for building it
6. **Risks and mitigations** — what could go wrong and how to handle it
7. **Security requirements** — from security-reliability specialist (omit if none apply)
8. **Trade-offs accepted** — known costs of this approach
9. **Trade-off arbiter assessment** — result and any tensions, gaps, or simplifications
10. **Future considerations** — deferred nice-to-have items for later iterations

After the human-readable plan, output the **structured artifact** for downstream skills:

```json
{
  "task": "what is being planned",
  "tech_stack": ["identified technologies"],
  "architecture": {
    "overview": "one-paragraph summary",
    "components": [
      {
        "name": "component name",
        "responsibility": "what it does",
        "interfaces": ["public API surface"],
        "dependencies": ["what it depends on"]
      }
    ],
    "data_model": {
      "entities": [{"name": "...", "fields": ["..."], "relationships": ["..."]}]
    },
    "api_surface": [
      {"endpoint_or_interface": "...", "method": "...", "description": "..."}
    ]
  },
  "decisions": [
    {
      "title": "decision name",
      "decision": "what was decided",
      "rationale": "why",
      "alternatives_considered": ["what else was evaluated"],
      "trade_offs": ["known costs"]
    }
  ],
  "implementation_plan": [
    {
      "step": 1,
      "description": "what to do",
      "files": ["files to create or modify"],
      "tests_needed": ["what to test"],
      "complexity": "low|medium|high"
    }
  ],
  "risks": [
    {
      "risk": "what could go wrong",
      "probability": "low|medium|high",
      "impact": "low|medium|high",
      "mitigation": "how to handle it"
    }
  ],
  "security_requirements": [
    {"requirement": "...", "implementation": "..."}
  ],
  "metadata": {
    "agents_completed": [],
    "agents_failed": [],
    "arbiter_completed": true,
    "total_recommendations": 0,
    "tensions_resolved": 0,
    "tensions_surfaced": 0,
    "timestamp": "ISO-8601"
  }
}
```

**No-recommendations edge case**: If all agents return empty arrays, output the artifact
with empty fields and note: "Planning agents found no specific architectural concerns.
The feature may be straightforward enough to implement directly without formal planning."

**speak-memory**: If an active story was loaded in Phase 1, update it with the
architecture decisions and implementation plan summary.

## Key Constraints

- All agents: **Opus** for maximum planning quality.
- **Agent execution caps**: Planning agents: `max_turns: 30`. Trade-off arbiter: `max_turns: 20`.
- Max **2 levels of nesting**: orchestrator → specialist. Specialists never spawn agents.
- **Scope budget**: 5 planning agents + 1 trade-off arbiter = 6 total. Do not expand.
- **Recommendation cap**: Max 25 recommendations enter synthesis (after merge + dedup).
  Drop low-priority nice-to-have items first.
- All sub-agents are **read-only** — no code modifications, no git changes.
- **Orchestrator write scope**: Write and Edit tools MUST only target paths under
  `.speak-memory/`. Before any Write/Edit call, verify the target path starts with
  `{repo_root}/.speak-memory/`. Bash limited to: `git rev-parse`, package manifest
  reads. No other Bash commands from the orchestrator.
- The structured artifact stays in conversation context — no file writing.
- If deep-research artifact is available, use it. Do not re-run research.

## Closing Checklist

Do not declare the plan done until all boxes are checked:

- [ ] Architecture scope stated with constraints and starting approach
- [ ] All 5 planning agents completed (returned valid JSON) or failed (logged as warning)
- [ ] Every recommendation tagged with priority (critical/important/nice-to-have)
- [ ] Tensions identified and resolved or surfaced as decision points
- [ ] Trade-off arbiter challenged the architecture
- [ ] MADR-inspired plan delivered with structured artifact
- [ ] Implementation checklist is ordered and actionable
- [ ] speak-memory story updated (if applicable)

## Reference Files

Load only when needed:

- `references/agent-roles.md` — Full prompt templates for each planning specialist + trade-off arbiter
- `references/synthesis.md` — Trade-off evaluation, tension resolution, architecture generation
- `assets/plan-template.md` — MADR-inspired plan output format
