# Project Conventions

This is a repository of agent skills following the [Agent Skills specification](https://agentskills.io/specification).

## Skill Structure

Each skill lives in `skills/<skill-name>/` and must contain:
- `SKILL.md` — YAML frontmatter (`name`, `description`) + markdown instructions
- The `name` field must match the directory name (lowercase a-z, 0-9, hyphens; no leading/trailing/consecutive hyphens; max 64 chars)
- `description` should include trigger keywords so agents know when to activate the skill (max 1024 chars)
- Keep `SKILL.md` under 500 lines / ~5000 tokens; move detailed docs to `references/`

Optional frontmatter fields: `license`, `compatibility`, `metadata` (key-value map), `allowed-tools`

Optional directories:
- `scripts/` — Python scripts using PEP 723 inline metadata for dependencies (run with `uv run`)
- `references/` — Additional documentation loaded on demand
- `assets/` — Static resources (templates, data files)

## Skill Packs

Packs are named bundles of related skills defined in `.claude-plugin/marketplace.json` as entries in the `plugins` array. Each entry has:
- `name` — Pack identifier (used for installation)
- `description` — What the pack provides
- `skills` — Array of paths to skill directories (e.g., `"./skills/my-skill"`)
- `source` — Always `"./"`
- `strict` — Set to `false` unless the pack should be the exclusive handler for matching tasks

A skill can belong to multiple packs. Users install a pack via `/plugin install <pack-name>@ethansei-skills`.

## Python Scripts

- Use PEP 723 inline script metadata for dependency declarations
- Scripts must be non-interactive (no input prompts)
- Use structured output (JSON) over free-form text
- Include `--help` output
- Support idempotency where possible
- Use meaningful exit codes

## When Adding a New Skill

1. Create `skills/<name>/SKILL.md` with valid frontmatter
2. Add the skill path to at least one pack in `.claude-plugin/marketplace.json`
3. Update both tables in `README.md` (Skill Packs and Available Skills)

## When Creating a New Pack

1. Add a new entry to the `plugins` array in `.claude-plugin/marketplace.json`
2. Update the Skill Packs table in `README.md`
