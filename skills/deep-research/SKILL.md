---
name: deep-research
description: >-
  On-demand deep research swarm. Spawns 5 specialist sub-agents in parallel
  to investigate a task across codebase patterns, web sources, MCP tools,
  installed skills, and project dependencies. Synthesizes findings into a
  report with 2-3 recommended approaches. Activates on: research, investigate,
  discover, deep research, how should I, what's the best way, explore options,
  analyze approaches, scout, reconnaissance, prior art, feasibility.
allowed-tools: Read Glob Grep Bash Agent WebSearch WebFetch ListMcpResourcesTool ReadMcpResourceTool
metadata:
  version: 0.1.0
---

# Deep Research

On-demand research swarm. Spawns specialist agents to investigate a task from
every available angle, then synthesizes findings and recommends approaches.

## When This Skill Activates

Trigger on explicit research requests:
- User says: "research", "investigate", "discover", "how should I approach..."
- User asks: "what's the best way to...", "explore options for...", "deep research"
- User wants prior art, feasibility analysis, or approach comparison

Do NOT activate automatically on every task. This is an on-demand tool, not a gate.

## Phase 1: Context Gathering

Before spawning agents, establish what we're researching:

1. **Parse the task**: Extract the core question or goal. If ambiguous, ask the user
   to clarify before proceeding. Identify technology keywords (languages, frameworks,
   libraries mentioned or implied by the codebase).
2. **Identify repo context**: Run `git rev-parse --show-toplevel` to get `{repo_root}`.
   Check for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc. to identify
   the language/framework stack. Pass this as `{tech_stack}` to agents.
3. **speak-memory**: If `.speak-memory/index.md` exists and an active story matches
   the current work, read it. Use the story's context to focus the research scope.
   If `.speak-memory/` does not exist, skip this step.

Announce: "Starting deep research on: {task_summary}"

## Phase 2: Research Swarm

Spawn all 5 agents **in a single message** (parallel Agent tool calls). Each agent
returns a JSON findings array — see `references/agent-roles.md` for full prompts.

| Agent | Subagent Type | Model | Focus |
|-------|---------------|-------|-------|
| codebase | Explore | opus | Existing patterns, utilities, similar implementations, conventions |
| web-research | general-purpose | opus | Solutions, libraries, best practices, documentation |
| tools-mcp | general-purpose | opus | Available MCP servers, tools, and resources |
| skills | general-purpose | opus | Installed skills and marketplace matches |
| dependencies | general-purpose | opus | Installed packages, version constraints, compatibility |

**Agent tool grants:**
- **codebase**: `Read, Glob, Grep` (read-only codebase exploration)
- **web-research**: `WebSearch, WebFetch` (external research)
- **tools-mcp**: `ListMcpResourcesTool, ReadMcpResourceTool` (tool discovery)
- **skills**: `Read, Glob, Grep, Bash` (read skills + `npx skills find`)
- **dependencies**: `Read, Glob, Grep, Bash` (read manifests + `npm ls`/`pip list`/`cargo tree`)

**Required output format** (instruct each agent to return exactly this):
```json
[
  {
    "relevance": "high|medium|low",
    "source": "where this was found (file path, URL, tool name)",
    "finding": "what was discovered",
    "recommendation": "how this finding applies to the task",
    "references": ["file paths or URLs for further reading"]
  }
]
```

Return empty array `[]` if no relevant findings in that domain.

## Phase 3: Synthesis

Merge all 5 finding arrays. Apply the synthesis rules from `references/synthesis.md`:

1. **Deduplicate**: If multiple agents found the same library, pattern, or approach,
   merge into a single finding and note which sources corroborated it.
2. **Resolve conflicts**: If web-research recommends a library that conflicts with
   installed dependencies, flag the conflict and note the resolution.
3. **Filter**: Drop `low` relevance findings from the summary. Include them in the
   structured artifact but not the user-facing report.
4. **Rank**: Sort remaining findings by relevance (high first), then by number of
   corroborating sources.
5. **Generate approaches**: Based on the ranked findings, propose **2-3 approaches**
   with trade-offs. Recommend one. Each approach should reference the findings that
   support it.

## Phase 4: Report

Output a concise report to the user (use `assets/report-template.md` for formatting):
- Task restatement
- Key findings by domain (only high/medium relevance)
- 2-3 approaches with pros/cons
- Recommended approach with reasoning
- Relevant files, tools, and skills discovered

**Structured artifact**: After the user-facing report, output a JSON block that
downstream skills (e.g., `deep-plan`) can consume:

```json
{
  "task": "original task description",
  "tech_stack": ["identified technologies"],
  "findings": [... merged findings array ...],
  "approaches": [
    {
      "name": "Approach A",
      "summary": "one-line description",
      "pros": ["..."],
      "cons": ["..."],
      "recommended": true,
      "relevant_files": ["paths from codebase agent"],
      "relevant_tools": ["MCP tools/skills discovered"],
      "dependencies_needed": ["new packages, if any"]
    }
  ]
}
```

**speak-memory**: If an active story was loaded in Phase 1, use Write/Edit to update
the story file — append to Recent Activity and update Current Context.

## Key Constraints

- All research agents: **Opus** (`model: "opus"`) for maximum research quality.
- Max **2 levels of nesting**: orchestrator → specialist. Specialists never spawn agents.
- All agents are **read-only** — no code modifications, no file writes, no git changes.
- Bash limited to dependency queries and skill search — no builds, no installs.
- If an agent returns no findings (empty array), that's fine — not every task needs
  all 5 research dimensions.
- The structured artifact stays in conversation context — no file writing.

## Closing Checklist

Do not declare the research done until all boxes are checked:

- [ ] All 5 research agents completed (or returned empty)
- [ ] Findings deduplicated and conflicts resolved
- [ ] 2-3 approaches presented with trade-offs and recommendation
- [ ] Structured artifact output for downstream consumption
- [ ] speak-memory story updated (if applicable)

## Reference Files

Load only when needed:

- `references/agent-roles.md` — Full prompt templates for each research agent
- `references/synthesis.md` — Dedup, conflict resolution, ranking, and approach generation
- `assets/report-template.md` — Report format
