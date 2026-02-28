# Story Lifecycle

Detailed procedures for creating, resuming, pausing, and completing stories.
This file is loaded on demand — only when performing a lifecycle action.

## Creating a Story

### 1. Initialize `.speak-memory/` (first time only)

If `.speak-memory/` does not exist at the project root (the directory containing
`.git/`, or the current working directory if no `.git/` is found):

1. Create the directory structure:
   ```
   .speak-memory/
   ├── index.md
   ├── archive/
   └── stories/
   ```
2. Copy `assets/index-template.md` content into `index.md`.
3. Add `.speak-memory/` to `.gitignore`:
   - If `.gitignore` exists, check if it already contains `.speak-memory/`. Only append if missing.
   - If `.gitignore` does not exist, create it with `.speak-memory/` as the sole entry.
4. Inform the user that `.speak-memory/` was created and gitignored. They can remove
   the gitignore entry if they want to track stories in version control.

### 2. Generate a story name

Auto-generate from the objective:
- Lowercase, hyphenated, max 5 words
- Descriptive and specific
- Examples: `auth-token-refresh`, `migrate-to-postgres`, `fix-upload-timeout`

**Collision handling**: Before creating the directory, check if
`.speak-memory/stories/<name>/` already exists. If it does, append a numeric
suffix: `<name>-2`, `<name>-3`, etc. Increment until a unique name is found.

If the user explicitly provides a name, use it (after normalizing to lowercase
hyphenated format).

### 3. Create story files

1. Add a row to `index.md` FIRST (so the story is discoverable even if the
   session terminates before the next steps complete):
   ```
   | [story-name](stories/story-name/story.md) | active | One-line summary | YYYY-MM-DD |
   ```

2. Create `stories/<story-name>/story.md` using the template from
   `assets/story-template.md`. Replace all `{{PLACEHOLDER}}` tokens:
   - `{{STORY_NAME}}` — the generated/provided name
   - `{{CREATED_DATE}}` — today's date in YYYY-MM-DD format
   - `{{STORY_TITLE}}` — human-readable title (proper casing)
   - `{{OBJECTIVE_TEXT}}` — 1-3 sentence objective
   - `{{FIRST_TASK}}` — first checklist item (add more items if already known)

3. Create the `stories/<story-name>/details/` directory (empty).

### When NOT to create a story

Do not create a story for:
- One-off questions ("what does this function do?")
- Simple single-file edits completable in one interaction
- Informational requests with no implementation component
- Greetings, meta-questions, or non-coding requests

Stories are for work that spans multiple steps or sessions.

## Resuming a Story

1. Read `stories/<story-name>/story.md`
2. Review the Objective, Checklist, and Current Context sections
3. Continue work from where the Current Context left off
4. Do NOT read detail files unless you specifically need historical context
   that is not available in the main story file

## Pausing a Story

When the user switches to different work or ends a session:

1. Update Current Context with a clear handoff note describing:
   - What was just done
   - What the next step should be
   - Any relevant state or blockers
2. Update the checklist (mark completed items, add new discovered items)
3. Append an activity log entry: `- [YYYY-MM-DD] Brief description`
4. Set `status: paused` in story.md frontmatter
5. Update the status column in `index.md` to `paused`
6. Update the `updated` date in both story.md frontmatter and index.md

## Completing a Story

When all checklist items are done:

1. Set `status: completed` in story.md frontmatter
2. Update Current Context with a final summary of what was accomplished
3. Append a final activity entry: `- [YYYY-MM-DD] Story completed`
4. Update index.md: set status to `completed`
5. Update the `updated` date in both story.md frontmatter and index.md
6. Suggest running `scripts/manage-stories.py --archive <name> --root <project-root>`
   to free space

## Multi-Story Overlap

If a user's request could apply to multiple active stories:

- Do NOT load or update multiple stories simultaneously
- One active story per interaction
- Ask the user: "This could relate to [story-a] or [story-b]. Which story
  should I track this under?"
- If the work is truly independent of all stories, proceed without story tracking

## Index Recovery

If `index.md` is missing but `.speak-memory/stories/` exists:

1. Scan all subdirectories in `stories/`
2. For each, read the `story.md` frontmatter (name, status, updated) and
   extract the first line of the Objective section for the Summary column
3. Build a new index table from the collected data
4. Write the rebuilt `index.md`
5. Continue with normal activation

Alternatively, run `scripts/manage-stories.py --rebuild-index --root <project-root>`.

## Stale Index Entries

If `index.md` references a story whose directory no longer exists:

1. Remove that row from `index.md`
2. Continue with normal activation
3. Do not warn the user unless they explicitly ask about that story
