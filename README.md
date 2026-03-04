# skills

Agent skills for Claude Code and other AI coding agents.

## What are Agent Skills?

Skills are reusable instruction sets that extend AI coding agent capabilities. Each skill is a directory containing a `SKILL.md` file with YAML frontmatter and markdown instructions, plus optional `scripts/`, `references/`, and `assets/` directories.

Skills follow the open [Agent Skills specification](https://agentskills.io/specification).

## Installation

### Install all skills

```bash
# Via skills.sh CLI (works with 40+ agents)
npx skills add EthanSei/skills

# Via Claude Code plugins
/plugin marketplace add EthanSei/skills
```

### Install a specific skill pack

```bash
# Claude Code — install a named pack
/plugin install <pack-name>@ethansei-skills
```

### Install a single skill

```bash
# Via skills.sh CLI
npx skills add EthanSei/skills --skill <skill-name>
```

### Manual

Copy or symlink a skill directory into `.claude/skills/` (project) or `~/.claude/skills/` (global).

## Skill Packs

Packs are named bundles of related skills that can be installed and removed as a unit. Each pack is defined as a plugin entry in `.claude-plugin/marketplace.json`.

<!-- Update this table as you add packs -->

| Pack | Description | Skills |
|------|-------------|--------|

## Available Skills

<!-- Update this table as you add skills -->

| Skill | Pack | Description |
|-------|------|-------------|
| code-discipline | — | Language-agnostic engineering discipline — minimal changes, no speculative code, clarity over cleverness |
| deep-review | — | Post-execution deep review with auto-heal — spawns specialist agents for quality, security, tests, performance, and consistency; auto-fixes P1 issues, surfaces P0 for confirmation |
| deep-research | — | Hypothesis-driven deep research swarm — forms hypotheses, gathers evidence-graded findings across codebase, web, MCP tools, skills, and dependencies, then adversarially challenges conclusions before delivering a structured verdict |
| speak-memory | — | Persistent story-based memory that tracks work across sessions with auto-compaction (~1.5k tokens) |
| tdd | — | Test-driven development — red-green-refactor cycles with mandatory test runs and closing audit |

## Creating a New Skill

1. Copy the template:
   ```bash
   cp -r template/ skills/my-skill-name/
   ```

2. Edit `skills/my-skill-name/SKILL.md`:
   - Set `name:` to match the directory name (lowercase, hyphens only)
   - Write a clear `description:` that includes trigger keywords
   - Add instructions in the markdown body

3. Optionally add supporting files:
   - `scripts/` — Python scripts using [PEP 723](https://peps.python.org/pep-0723/) inline metadata for deps (run with `uv run`)
   - `references/` — Detailed documentation loaded on demand
   - `assets/` — Templates, data files, schemas

4. Add the skill to a pack in `.claude-plugin/marketplace.json` (or create a new pack)

5. Update the tables in this README

## Creating a New Skill Pack

Packs are defined in `.claude-plugin/marketplace.json` as plugin entries. Add a new entry to the `plugins` array:

```json
{
  "name": "my-pack-name",
  "description": "What this pack is for",
  "source": "./",
  "strict": false,
  "skills": [
    "./skills/skill-one",
    "./skills/skill-two"
  ]
}
```

A skill can belong to multiple packs. Users install a pack with:
```
/plugin install my-pack-name@ethansei-skills
```

## Project Structure

```
.
├── .claude-plugin/
│   └── marketplace.json      # Skill packs and plugin config
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md           # Required: frontmatter + instructions
│       ├── scripts/           # Optional: Python helper scripts
│       ├── references/        # Optional: docs loaded on demand
│       └── assets/            # Optional: templates, data files
├── template/
│   └── SKILL.md               # Starter template for new skills
├── CLAUDE.md                   # Project conventions
├── pyproject.toml              # Python tooling (ruff)
└── LICENSE                     # MIT
```

## License

MIT
