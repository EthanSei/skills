# Activity Log Compaction Rules

The Recent Activity section in `story.md` grows by one entry per interaction.
To keep context efficient, old entries are periodically compacted into detail files.

## Trigger

Compact when Recent Activity exceeds **30 entries**.

Check the entry count after each post-interaction update. If 31 or more, trigger
compaction immediately.

## Procedure

1. **Count entries**: Count lines starting with `- [` in Recent Activity.

2. **Split**: Keep the **last 10 entries** in `story.md`. The rest move to a detail file.

3. **Determine file number**: Ensure `stories/<name>/details/` exists (create it
   if missing). Scan for files matching `log-*.md`. Take the highest existing
   number + 1. If none exist, use 001. Zero-pad to three digits: `log-001.md`,
   `log-002.md`, etc.

4. **Write the compacted log FIRST** (before modifying story.md) at
   `stories/<name>/details/log-NNN.md`:

   ```markdown
   # Activity Log (Compacted)

   Story: <story-name>
   Period: <oldest-date> to <newest-date>
   Entries: <count>

   ## Summary
   <2-4 sentence summary of key accomplishments and themes>

   ## Entries
   - [2026-01-15] Entry text...
   - [2026-01-16] Entry text...
   ...
   ```

5. **Then update story.md**: Replace the Recent Activity section with a compaction
   note followed by the retained entries:

   ```markdown
   ## Recent Activity
   _Earlier activity compacted to details/log-NNN.md_
   - [2026-02-20] Recent entry 1...
   - [2026-02-21] Recent entry 2...
   ...
   ```

   If a compaction note already exists, update it to reference the latest log file.

6. **Summary**: Write a plain-English paragraph summarizing themes — what milestones
   were reached, what direction work took, any significant pivots or blockers.

## Atomicity and Recovery

The write order matters: **log file first, then story.md**.

If a session terminates between steps 4 and 5 (log file written but story.md not
updated), the next activation will find duplicate entries in both locations. To
recover: check if the newest log file contains entries that are also in story.md's
Recent Activity. If so, remove the duplicates from story.md and add the compaction
note.

## Manual Compaction

The user can force compaction via "compact story" at any time. For manual compaction,
keep only the **last 5 entries** (instead of 10). If there are 5 or fewer entries
total, skip compaction (nothing to move to a detail file).

## Edge Cases

- **First compaction**: No prior compaction note. Add the note line before retained entries.
- **Multiple compactions**: Update the note to reference the latest log file (not all of them).
- **Story never reaches 30 entries**: No compaction triggers. This is fine.
- **Very old compacted logs**: Can be cleaned up via `manage-stories.py --archive` after
  the story is completed.
