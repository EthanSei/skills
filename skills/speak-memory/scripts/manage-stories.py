#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Manage speak-memory stories: list, archive, delete, prune, and rebuild index.

All output is JSON for structured consumption by agents.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path


def find_speak_memory_dir(root: Path) -> Path:
    return root / ".speak-memory"


def _validate_story_name(story_name: str, stories_dir: Path) -> Path:
    """Validate story name and return resolved path, guarding against path traversal."""
    story_dir = (stories_dir / story_name).resolve()
    if story_dir.parent != stories_dir.resolve():
        print(json.dumps({"error": f"Invalid story name: '{story_name}'", "success": False}))
        sys.exit(1)
    return story_dir


def _escape_table_cell(text: str) -> str:
    """Escape pipe characters for markdown table cells."""
    return text.replace("|", "\\|")


def parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a story.md file (simple key: value only)."""
    text = path.read_text(encoding="utf-8")
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("---", 3)
    if end == -1:
        return fm
    for line in text[3:end].strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            # Strip quotes
            if len(value) >= 2 and (
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
            ):
                value = value[1:-1]
            # Parse simple lists: [a, b, c]
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            fm[key] = value
    return fm


def get_stories(sm_dir: Path) -> list[dict]:
    """Scan stories directory and return metadata for each story."""
    stories_dir = sm_dir / "stories"
    if not stories_dir.is_dir():
        return []
    results = []
    for story_dir in sorted(stories_dir.iterdir()):
        if not story_dir.is_dir():
            continue
        story_file = story_dir / "story.md"
        if not story_file.exists():
            continue
        fm = parse_frontmatter(story_file)
        # Calculate disk usage (handle permission errors gracefully)
        total_bytes = 0
        for f in story_dir.rglob("*"):
            if f.is_file() and not f.is_symlink():
                try:
                    total_bytes += f.stat().st_size
                except OSError:
                    pass
        results.append(
            {
                "name": fm.get("name", story_dir.name),
                "dir_name": story_dir.name,
                "status": fm.get("status", "unknown"),
                "created": fm.get("created", ""),
                "updated": fm.get("updated", ""),
                "tags": fm.get("tags", []),
                "path": str(story_dir),
                "disk_bytes": total_bytes,
            }
        )
    return results


def read_index_stories(index_path: Path) -> list[str]:
    """Read story names from index.md table rows."""
    if not index_path.exists():
        return []
    names = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| Story") or line.startswith("|---"):
            continue
        # Extract story name from first column: | [name](path) | or | name |
        col = line.split("|")[1].strip()
        match = re.match(r"\[([^\]]+)\]", col)
        if match:
            names.append(match.group(1))
        elif col and col != "Story":
            names.append(col)
    return names


def write_index(sm_dir: Path, stories: list[dict]) -> None:
    """Rebuild index.md from story metadata."""
    lines = [
        "# Story Index",
        "",
        "| Story | Status | Summary | Updated |",
        "|-------|--------|---------|---------|",
    ]
    for s in stories:
        dir_name = s.get("dir_name", s["name"])
        display_name = _escape_table_cell(s["name"])
        status = _escape_table_cell(s["status"])
        updated = s.get("updated", "")
        # Try to extract summary from story.md objective
        story_file = sm_dir / "stories" / dir_name / "story.md"
        summary = ""
        if story_file.exists():
            text = story_file.read_text(encoding="utf-8")
            obj_match = re.search(r"## Objective\s*\n+(.+?)(?:\n\n|\n##|\Z)", text, re.DOTALL)
            if obj_match:
                summary = _escape_table_cell(obj_match.group(1).strip().split("\n")[0][:80])
        lines.append(
            f"| [{display_name}](stories/{dir_name}/story.md) | {status} | {summary} | {updated} |"
        )
    lines.append("")
    index_path = sm_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")


def create_archive_summary(story_dir: Path, fm: dict) -> str:
    """Create a single-file summary for archiving."""
    story_file = story_dir / "story.md"
    text = story_file.read_text(encoding="utf-8") if story_file.exists() else ""

    # Extract objective
    obj_match = re.search(r"## Objective\s*\n+(.+?)(?:\n##|\Z)", text, re.DOTALL)
    objective = obj_match.group(1).strip() if obj_match else "No objective found"

    # Extract checklist
    cl_match = re.search(r"## Checklist\s*\n+(.+?)(?:\n##|\Z)", text, re.DOTALL)
    checklist = cl_match.group(1).strip() if cl_match else "No checklist found"

    # Extract key decisions
    kd_match = re.search(r"## Key Decisions\s*\n+(.+?)(?:\n##|\Z)", text, re.DOTALL)
    decisions = kd_match.group(1).strip() if kd_match else "(none)"

    # Count detail files
    details_dir = story_dir / "details"
    detail_count = len(list(details_dir.glob("*.md"))) if details_dir.is_dir() else 0

    return f"""# Archived Story: {fm.get('name', story_dir.name)}

Created: {fm.get('created', 'unknown')}
Completed: {fm.get('updated', 'unknown')}
Tags: {fm.get('tags', [])}

## Objective
{objective}

## Final Checklist
{checklist}

## Key Decisions
{decisions}

## Notes
Archived from {story_dir.name}/ ({detail_count} detail files were present).
"""


def cmd_list(sm_dir: Path) -> None:
    stories = get_stories(sm_dir)
    result = {
        "stories": stories,
        "total": len(stories),
        "by_status": {},
    }
    for s in stories:
        status = s["status"]
        result["by_status"][status] = result["by_status"].get(status, 0) + 1
    print(json.dumps(result, indent=2))


def cmd_archive(sm_dir: Path, story_name: str) -> None:
    stories_dir = sm_dir / "stories"
    story_dir = _validate_story_name(story_name, stories_dir)
    if not story_dir.is_dir():
        print(json.dumps({"error": f"Story '{story_name}' not found", "success": False}))
        sys.exit(1)

    fm = parse_frontmatter(story_dir / "story.md")
    if fm.get("status") != "completed":
        print(
            json.dumps(
                {
                    "error": f"Story '{story_name}' has status '{fm.get('status', 'unknown')}'. "
                    "Only completed stories can be archived.",
                    "success": False,
                }
            )
        )
        sys.exit(1)

    # Create archive
    archive_dir = sm_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{story_name}.md"
    archive_file.write_text(create_archive_summary(story_dir, fm), encoding="utf-8")

    # Remove story directory
    shutil.rmtree(story_dir)

    # Update index
    stories = get_stories(sm_dir)
    write_index(sm_dir, stories)

    print(
        json.dumps(
            {
                "success": True,
                "archived": story_name,
                "archive_path": str(archive_file),
            }
        )
    )


def cmd_delete(sm_dir: Path, story_name: str) -> None:
    stories_dir = sm_dir / "stories"
    story_dir = _validate_story_name(story_name, stories_dir)
    if not story_dir.is_dir():
        print(json.dumps({"error": f"Story '{story_name}' not found", "success": False}))
        sys.exit(1)

    shutil.rmtree(story_dir)

    # Update index
    stories = get_stories(sm_dir)
    write_index(sm_dir, stories)

    print(json.dumps({"success": True, "deleted": story_name}))


def cmd_prune(sm_dir: Path, days: int) -> None:
    if days < 1:
        print(json.dumps({"error": "--days must be a positive integer", "success": False}))
        sys.exit(1)
    cutoff = date.today() - timedelta(days=days)
    stories = get_stories(sm_dir)
    archived = []

    for s in stories:
        if s["status"] != "completed":
            continue
        updated_str = s.get("updated", "")
        try:
            updated_date = date.fromisoformat(updated_str)
        except (ValueError, TypeError):
            continue
        if updated_date <= cutoff:
            story_dir = Path(s["path"])
            fm = parse_frontmatter(story_dir / "story.md")

            archive_dir = sm_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            # Use directory name for archive filename to avoid path issues
            archive_file = archive_dir / f"{s['dir_name']}.md"
            if archive_file.exists():
                # Avoid overwriting existing archive
                n = 2
                while archive_file.exists():
                    archive_file = archive_dir / f"{s['dir_name']}-{n}.md"
                    n += 1
            archive_file.write_text(create_archive_summary(story_dir, fm), encoding="utf-8")

            shutil.rmtree(story_dir)
            archived.append(s["name"])

    # Update index
    if archived:
        stories = get_stories(sm_dir)
        write_index(sm_dir, stories)

    print(
        json.dumps(
            {
                "success": True,
                "pruned": archived,
                "count": len(archived),
                "cutoff_days": days,
                "cutoff_date": cutoff.isoformat(),
            }
        )
    )


def cmd_rebuild_index(sm_dir: Path) -> None:
    stories = get_stories(sm_dir)
    write_index(sm_dir, stories)
    print(
        json.dumps(
            {
                "success": True,
                "rebuilt": True,
                "story_count": len(stories),
                "stories": [s["name"] for s in stories],
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage speak-memory stories: list, archive, delete, prune, rebuild index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --list
  %(prog)s --archive fix-upload-timeout
  %(prog)s --delete old-experiment
  %(prog)s --prune --days 30
  %(prog)s --rebuild-index
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all stories with status and disk usage")
    group.add_argument("--archive", metavar="NAME", help="Archive a completed story")
    group.add_argument("--delete", metavar="NAME", help="Permanently delete a story")
    group.add_argument("--prune", action="store_true", help="Archive completed stories older than --days")
    group.add_argument("--rebuild-index", action="store_true", help="Rebuild index.md from story files")

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days threshold for --prune (default: 30)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()
    sm_dir = find_speak_memory_dir(args.root)

    try:
        if not sm_dir.is_dir():
            if args.list:
                print(json.dumps({"stories": [], "total": 0, "by_status": {}}))
                sys.exit(0)
            print(
                json.dumps(
                    {
                        "error": f"No .speak-memory directory found at {sm_dir}",
                        "success": False,
                    }
                )
            )
            sys.exit(1)

        if args.list:
            cmd_list(sm_dir)
        elif args.archive:
            cmd_archive(sm_dir, args.archive)
        elif args.delete:
            cmd_delete(sm_dir, args.delete)
        elif args.prune:
            cmd_prune(sm_dir, args.days)
        elif args.rebuild_index:
            cmd_rebuild_index(sm_dir)
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({"error": str(exc), "success": False}))
        sys.exit(1)


if __name__ == "__main__":
    main()
