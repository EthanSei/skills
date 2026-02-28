# Story File Format

Each story is stored as `.speak-memory/stories/<story-name>/story.md`.

## Frontmatter (YAML)

```yaml
---
name: <story-name>
status: active | paused | completed
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [optional, list, of, tags]
---
```

### Fields

- **name**: Matches the directory name. Lowercase, hyphenated, max 5 words.
  Auto-generated from the objective if the user does not specify one.
  Examples: `auth-token-refresh`, `setup-ci-pipeline`, `fix-upload-timeout`

- **status**: One of:
  - `active` — Currently being worked on
  - `paused` — Set aside, can be resumed
  - `completed` — All checklist items done

- **created**: Date the story was created (YYYY-MM-DD)

- **updated**: Date of the most recent update (YYYY-MM-DD), refreshed after every interaction

- **tags**: Optional list for categorization. Examples: `[auth, backend]`, `[ui, react]`.
  Useful for future grouping and filtering.

## Body Sections

### `# Story: <Title>`

Human-readable title with proper casing.
Example: `# Story: Fix S3 Upload Timeout on Large Files`

### `## Objective`

One to three sentences describing what this story accomplishes. Should be specific
enough to match against future user requests.

Good: "Fix the S3 upload timeout that occurs when uploading files larger than
100MB by implementing multipart upload with retry logic."

Bad: "Fix a bug."

### `## Checklist`

Markdown checklist tracking sub-tasks:

```markdown
## Checklist
- [x] Reproduce the timeout error locally
- [x] Identify the S3 SDK method causing the issue
- [ ] Implement multipart upload for files > 50MB
- [ ] Add retry logic with exponential backoff
- [ ] Add integration tests
- [ ] Update documentation
```

Guidelines:
- Keep items concrete and verifiable
- Break large items into smaller steps as you learn more
- Completed items stay in the list (they record progress)
- Aim for 5-15 items; if more needed, consider splitting into multiple stories

### `## Current Context`

The "working memory" of the story. This section is **replaced** (not appended to)
after every interaction. Contains:

1. What was just done (1-2 sentences)
2. What the immediate next step is (1-2 sentences)
3. Any blockers or open questions (if applicable)

Maximum: ~5 sentences. If you need more, the context is too broad — break it down.

Example:
```markdown
## Current Context
Implemented multipart upload in `src/upload.ts` using the S3 `CreateMultipartUpload`
API. The upload works for files up to 500MB in local testing. Next step is to add
retry logic — the current implementation fails silently on part upload errors.
```

### `## Key Decisions`

Append-only log of significant decisions with rationale. Never remove entries.

```markdown
## Key Decisions
- Use AWS SDK built-in retry instead of custom: simpler, well-tested, configurable
- Set part size to 10MB: balances memory usage with upload parallelism
```

### `## Recent Activity`

Chronological log, one entry per interaction:

```markdown
## Recent Activity
- [2026-02-25] Reproduced timeout, identified putObject as bottleneck
- [2026-02-26] Implemented multipart upload with 10MB parts
- [2026-02-27] Added retry logic using SDK built-in mechanism
- [2026-02-28] Wrote integration tests, all passing
```

Guidelines:
- One entry per interaction (not per sub-task)
- Keep entries to one line, ~60-100 characters
- Date in `[YYYY-MM-DD]` format
- Subject to auto-compaction (see `compaction-rules.md`)
