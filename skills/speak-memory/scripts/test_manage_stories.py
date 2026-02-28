#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Tests for manage-stories.py."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Import the module under test (hyphenated filename requires importlib)
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "manage_stories", Path(__file__).parent / "manage-stories.py"
)
ms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ms)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sm_dir(tmp_path: Path) -> Path:
    """Create a minimal .speak-memory directory structure."""
    d = tmp_path / ".speak-memory"
    d.mkdir()
    (d / "stories").mkdir()
    (d / "archive").mkdir()
    (d / "index.md").write_text(
        "# Story Index\n\n"
        "| Story | Status | Summary | Updated |\n"
        "|-------|--------|---------|---------|\n",
        encoding="utf-8",
    )
    return d


@pytest.fixture
def make_story(sm_dir: Path):
    """Factory fixture to create a story directory with a story.md file."""

    def _make(
        name: str,
        status: str = "active",
        created: str = "2026-01-01",
        updated: str = "2026-01-15",
        tags: list[str] | None = None,
        objective: str = "Do the thing.",
        checklist: str = "- [ ] First task",
    ) -> Path:
        story_dir = sm_dir / "stories" / name
        story_dir.mkdir(parents=True, exist_ok=True)
        (story_dir / "details").mkdir(exist_ok=True)
        tags_str = json.dumps(tags) if tags else "[]"
        content = (
            f"---\n"
            f"name: {name}\n"
            f"status: {status}\n"
            f"created: {created}\n"
            f"updated: {updated}\n"
            f"tags: {tags_str}\n"
            f"---\n\n"
            f"# Story: {name.replace('-', ' ').title()}\n\n"
            f"## Objective\n\n{objective}\n\n"
            f"## Checklist\n\n{checklist}\n\n"
            f"## Current Context\n\nWorking on it.\n\n"
            f"## Key Decisions\n\n(none yet)\n\n"
            f"## Recent Activity\n\n- [{created}] Story created\n"
        )
        (story_dir / "story.md").write_text(content, encoding="utf-8")
        return story_dir

    return _make


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_valid_frontmatter(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text(
            '---\nname: my-story\nstatus: active\ncreated: 2026-01-01\ntags: [a, b]\n---\n\n# Body',
            encoding="utf-8",
        )
        fm = ms.parse_frontmatter(f)
        assert fm["name"] == "my-story"
        assert fm["status"] == "active"
        assert fm["created"] == "2026-01-01"
        assert fm["tags"] == ["a", "b"]

    def test_quoted_values(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text('---\nname: "quoted-name"\nstatus: \'active\'\n---\n', encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm["name"] == "quoted-name"
        assert fm["status"] == "active"

    def test_no_frontmatter(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("# Just a heading\n\nSome text.\n", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm == {}

    def test_incomplete_frontmatter(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("---\nname: broken\nno closing delimiter\n", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm == {}

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm == {}

    def test_comments_in_frontmatter(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("---\nname: test\n# this is a comment\nstatus: active\n---\n", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm["name"] == "test"
        assert fm["status"] == "active"
        assert "#" not in fm

    def test_empty_tags_list(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("---\nname: test\ntags: []\n---\n", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm["tags"] == []

    def test_tags_with_quotes(self, tmp_path: Path):
        f = tmp_path / "story.md"
        f.write_text("---\ntags: ['auth', \"backend\"]\n---\n", encoding="utf-8")
        fm = ms.parse_frontmatter(f)
        assert fm["tags"] == ["auth", "backend"]


# ---------------------------------------------------------------------------
# get_stories
# ---------------------------------------------------------------------------

class TestGetStories:
    def test_empty_stories_dir(self, sm_dir: Path):
        stories = ms.get_stories(sm_dir)
        assert stories == []

    def test_missing_stories_dir(self, tmp_path: Path):
        sm_dir = tmp_path / ".speak-memory"
        sm_dir.mkdir()
        # No stories/ subdir
        stories = ms.get_stories(sm_dir)
        assert stories == []

    def test_single_story(self, sm_dir: Path, make_story):
        make_story("fix-bug", status="active", tags=["backend"])
        stories = ms.get_stories(sm_dir)
        assert len(stories) == 1
        assert stories[0]["name"] == "fix-bug"
        assert stories[0]["status"] == "active"
        assert stories[0]["tags"] == ["backend"]
        assert stories[0]["disk_bytes"] > 0

    def test_multiple_stories_sorted(self, sm_dir: Path, make_story):
        make_story("zebra-task")
        make_story("alpha-task")
        stories = ms.get_stories(sm_dir)
        assert len(stories) == 2
        # sorted by directory name
        assert stories[0]["name"] == "alpha-task"
        assert stories[1]["name"] == "zebra-task"

    def test_skips_non_directories(self, sm_dir: Path, make_story):
        make_story("real-story")
        (sm_dir / "stories" / "not-a-dir.txt").write_text("junk", encoding="utf-8")
        stories = ms.get_stories(sm_dir)
        assert len(stories) == 1
        assert stories[0]["name"] == "real-story"

    def test_skips_dir_without_story_md(self, sm_dir: Path, make_story):
        make_story("valid-story")
        orphan = sm_dir / "stories" / "orphan-dir"
        orphan.mkdir()
        stories = ms.get_stories(sm_dir)
        assert len(stories) == 1
        assert stories[0]["name"] == "valid-story"

    def test_defaults_for_missing_fields(self, sm_dir: Path):
        story_dir = sm_dir / "stories" / "minimal"
        story_dir.mkdir()
        (story_dir / "story.md").write_text("---\nname: minimal\n---\n# Body\n", encoding="utf-8")
        stories = ms.get_stories(sm_dir)
        assert len(stories) == 1
        assert stories[0]["status"] == "unknown"
        assert stories[0]["created"] == ""
        assert stories[0]["tags"] == []


# ---------------------------------------------------------------------------
# write_index / read_index_stories round-trip
# ---------------------------------------------------------------------------

class TestIndexRoundTrip:
    def test_write_and_read_index(self, sm_dir: Path, make_story):
        make_story("story-one", status="active", updated="2026-02-01")
        make_story("story-two", status="paused", updated="2026-01-20")
        stories = ms.get_stories(sm_dir)
        ms.write_index(sm_dir, stories)

        index_path = sm_dir / "index.md"
        assert index_path.exists()
        names = ms.read_index_stories(index_path)
        assert "story-one" in names
        assert "story-two" in names

    def test_empty_index(self, sm_dir: Path):
        ms.write_index(sm_dir, [])
        names = ms.read_index_stories(sm_dir / "index.md")
        assert names == []

    def test_read_nonexistent_index(self, tmp_path: Path):
        names = ms.read_index_stories(tmp_path / "no-such-file.md")
        assert names == []

    def test_index_contains_objective_summary(self, sm_dir: Path, make_story):
        make_story("my-story", objective="Implement the widget for better UX.")
        stories = ms.get_stories(sm_dir)
        ms.write_index(sm_dir, stories)
        content = (sm_dir / "index.md").read_text(encoding="utf-8")
        assert "Implement the widget" in content


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList:
    def test_list_empty(self, sm_dir: Path, capsys):
        ms.cmd_list(sm_dir)
        out = json.loads(capsys.readouterr().out)
        assert out["total"] == 0
        assert out["stories"] == []
        assert out["by_status"] == {}

    def test_list_with_stories(self, sm_dir: Path, make_story, capsys):
        make_story("task-a", status="active")
        make_story("task-b", status="completed")
        make_story("task-c", status="active")
        ms.cmd_list(sm_dir)
        out = json.loads(capsys.readouterr().out)
        assert out["total"] == 3
        assert out["by_status"]["active"] == 2
        assert out["by_status"]["completed"] == 1


# ---------------------------------------------------------------------------
# cmd_archive
# ---------------------------------------------------------------------------

class TestCmdArchive:
    def test_archive_completed_story(self, sm_dir: Path, make_story, capsys):
        make_story("done-task", status="completed", updated="2026-01-10")
        ms.cmd_archive(sm_dir, "done-task")
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert out["archived"] == "done-task"
        # Story directory removed
        assert not (sm_dir / "stories" / "done-task").exists()
        # Archive file created
        archive_file = sm_dir / "archive" / "done-task.md"
        assert archive_file.exists()
        content = archive_file.read_text(encoding="utf-8")
        assert "Archived Story: done-task" in content
        # Index updated (no more entries)
        names = ms.read_index_stories(sm_dir / "index.md")
        assert "done-task" not in names

    def test_archive_non_completed_fails(self, sm_dir: Path, make_story):
        make_story("wip-task", status="active")
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_archive(sm_dir, "wip-task")
        assert exc_info.value.code == 1
        # Story still exists
        assert (sm_dir / "stories" / "wip-task").exists()

    def test_archive_nonexistent_fails(self, sm_dir: Path):
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_archive(sm_dir, "no-such-story")
        assert exc_info.value.code == 1

    def test_archive_preserves_other_stories_in_index(self, sm_dir: Path, make_story, capsys):
        make_story("keep-me", status="active")
        make_story("archive-me", status="completed")
        ms.cmd_archive(sm_dir, "archive-me")
        capsys.readouterr()  # consume output
        names = ms.read_index_stories(sm_dir / "index.md")
        assert "keep-me" in names
        assert "archive-me" not in names


# ---------------------------------------------------------------------------
# cmd_delete
# ---------------------------------------------------------------------------

class TestCmdDelete:
    def test_delete_story(self, sm_dir: Path, make_story, capsys):
        make_story("trash-task", status="active")
        ms.cmd_delete(sm_dir, "trash-task")
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert not (sm_dir / "stories" / "trash-task").exists()
        # No archive created
        assert not (sm_dir / "archive" / "trash-task.md").exists()

    def test_delete_nonexistent_fails(self, sm_dir: Path):
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_delete(sm_dir, "ghost")
        assert exc_info.value.code == 1

    def test_delete_updates_index(self, sm_dir: Path, make_story, capsys):
        make_story("to-delete", status="paused")
        make_story("to-keep", status="active")
        ms.cmd_delete(sm_dir, "to-delete")
        capsys.readouterr()
        names = ms.read_index_stories(sm_dir / "index.md")
        assert "to-delete" not in names
        assert "to-keep" in names


# ---------------------------------------------------------------------------
# cmd_prune
# ---------------------------------------------------------------------------

class TestCmdPrune:
    def test_prune_old_completed(self, sm_dir: Path, make_story, capsys):
        old_date = (date.today() - timedelta(days=60)).isoformat()
        make_story("old-done", status="completed", updated=old_date)
        make_story("recent-active", status="active", updated=date.today().isoformat())
        ms.cmd_prune(sm_dir, days=30)
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert "old-done" in out["pruned"]
        assert out["count"] == 1
        # Old story archived
        assert (sm_dir / "archive" / "old-done.md").exists()
        assert not (sm_dir / "stories" / "old-done").exists()
        # Active story untouched
        assert (sm_dir / "stories" / "recent-active").exists()

    def test_prune_skips_non_completed(self, sm_dir: Path, make_story, capsys):
        old_date = (date.today() - timedelta(days=60)).isoformat()
        make_story("old-active", status="active", updated=old_date)
        ms.cmd_prune(sm_dir, days=30)
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 0
        assert (sm_dir / "stories" / "old-active").exists()

    def test_prune_skips_recent_completed(self, sm_dir: Path, make_story, capsys):
        recent_date = (date.today() - timedelta(days=5)).isoformat()
        make_story("recent-done", status="completed", updated=recent_date)
        ms.cmd_prune(sm_dir, days=30)
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 0
        assert (sm_dir / "stories" / "recent-done").exists()

    def test_prune_handles_bad_date(self, sm_dir: Path, make_story, capsys):
        make_story("bad-date", status="completed", updated="not-a-date")
        ms.cmd_prune(sm_dir, days=30)
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 0  # skipped due to bad date

    def test_prune_updates_index(self, sm_dir: Path, make_story, capsys):
        old_date = (date.today() - timedelta(days=60)).isoformat()
        make_story("prune-me", status="completed", updated=old_date)
        make_story("keep-me", status="active", updated=date.today().isoformat())
        ms.cmd_prune(sm_dir, days=30)
        capsys.readouterr()
        names = ms.read_index_stories(sm_dir / "index.md")
        assert "prune-me" not in names
        assert "keep-me" in names


# ---------------------------------------------------------------------------
# cmd_rebuild_index
# ---------------------------------------------------------------------------

class TestCmdRebuildIndex:
    def test_rebuild_from_stories(self, sm_dir: Path, make_story, capsys):
        make_story("alpha", status="active")
        make_story("beta", status="paused")
        # Corrupt the index
        (sm_dir / "index.md").write_text("garbage", encoding="utf-8")
        ms.cmd_rebuild_index(sm_dir)
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert out["story_count"] == 2
        assert "alpha" in out["stories"]
        assert "beta" in out["stories"]
        # Index is now valid
        names = ms.read_index_stories(sm_dir / "index.md")
        assert "alpha" in names
        assert "beta" in names

    def test_rebuild_empty(self, sm_dir: Path, capsys):
        ms.cmd_rebuild_index(sm_dir)
        out = json.loads(capsys.readouterr().out)
        assert out["story_count"] == 0


# ---------------------------------------------------------------------------
# create_archive_summary
# ---------------------------------------------------------------------------

class TestCreateArchiveSummary:
    def test_summary_content(self, sm_dir: Path, make_story):
        story_dir = make_story(
            "archive-test",
            status="completed",
            objective="Fix the upload timeout bug.",
            checklist="- [x] Reproduce the issue\n- [x] Apply fix",
        )
        fm = ms.parse_frontmatter(story_dir / "story.md")
        summary = ms.create_archive_summary(story_dir, fm)
        assert "Archived Story: archive-test" in summary
        assert "Fix the upload timeout bug" in summary
        assert "Reproduce the issue" in summary

    def test_summary_with_key_decisions(self, sm_dir: Path):
        story_dir = sm_dir / "stories" / "decisions-test"
        story_dir.mkdir(parents=True)
        (story_dir / "story.md").write_text(
            "---\nname: decisions-test\nstatus: completed\n---\n\n"
            "## Objective\n\nTest objective.\n\n"
            "## Checklist\n\n- [x] Done\n\n"
            "## Key Decisions\n\n- Used approach A because B was too slow\n",
            encoding="utf-8",
        )
        fm = ms.parse_frontmatter(story_dir / "story.md")
        summary = ms.create_archive_summary(story_dir, fm)
        assert "Used approach A" in summary

    def test_summary_counts_detail_files(self, sm_dir: Path, make_story):
        story_dir = make_story("details-test", status="completed")
        details = story_dir / "details"
        (details / "log-001.md").write_text("# Log 1", encoding="utf-8")
        (details / "log-002.md").write_text("# Log 2", encoding="utf-8")
        fm = ms.parse_frontmatter(story_dir / "story.md")
        summary = ms.create_archive_summary(story_dir, fm)
        assert "2 detail files" in summary


# ---------------------------------------------------------------------------
# CLI integration (subprocess)
# ---------------------------------------------------------------------------

class TestCLI:
    def _run(self, *args: str, root: Path) -> dict:
        script = str(Path(__file__).parent / "manage-stories.py")
        result = subprocess.run(
            [sys.executable, script, "--root", str(root), *args],
            capture_output=True,
            text=True,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "json": json.loads(result.stdout) if result.stdout.strip() else None,
        }

    def test_help(self, tmp_path: Path):
        script = str(Path(__file__).parent / "manage-stories.py")
        result = subprocess.run(
            [sys.executable, script, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "manage" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_list_no_speak_memory(self, tmp_path: Path):
        r = self._run("--list", root=tmp_path)
        assert r["returncode"] == 0
        assert r["json"]["total"] == 0

    def test_archive_no_speak_memory(self, tmp_path: Path):
        r = self._run("--archive", "foo", root=tmp_path)
        assert r["returncode"] == 1

    def test_list_with_stories(self, sm_dir: Path, make_story):
        make_story("cli-test", status="active")
        r = self._run("--list", root=sm_dir.parent)
        assert r["returncode"] == 0
        assert r["json"]["total"] == 1

    def test_rebuild_index_via_cli(self, sm_dir: Path, make_story):
        make_story("rebuild-cli")
        r = self._run("--rebuild-index", root=sm_dir.parent)
        assert r["returncode"] == 0
        assert r["json"]["success"] is True

    def test_mutually_exclusive_args(self, tmp_path: Path):
        script = str(Path(__file__).parent / "manage-stories.py")
        result = subprocess.run(
            [sys.executable, script, "--list", "--rebuild-index"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2  # argparse error


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_story_name_with_numbers(self, sm_dir: Path, make_story):
        make_story("fix-bug-2", status="active")
        stories = ms.get_stories(sm_dir)
        assert stories[0]["name"] == "fix-bug-2"

    def test_disk_bytes_includes_details(self, sm_dir: Path, make_story):
        story_dir = make_story("disk-test")
        details = story_dir / "details"
        (details / "big-file.md").write_text("x" * 10000, encoding="utf-8")
        stories = ms.get_stories(sm_dir)
        assert stories[0]["disk_bytes"] > 10000

    def test_path_traversal_delete_blocked(self, sm_dir: Path):
        """Path traversal in --delete should be rejected."""
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_delete(sm_dir, "../..")
        assert exc_info.value.code == 1

    def test_path_traversal_archive_blocked(self, sm_dir: Path):
        """Path traversal in --archive should be rejected."""
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_archive(sm_dir, "../../etc")
        assert exc_info.value.code == 1

    def test_pipe_in_name_does_not_corrupt_index(self, sm_dir: Path):
        """Story names with pipe chars should be escaped in the index table."""
        story_dir = sm_dir / "stories" / "pipe-test"
        story_dir.mkdir()
        # Frontmatter name contains a pipe
        (story_dir / "story.md").write_text(
            "---\nname: fix|bug\nstatus: active\nupdated: 2026-01-01\n---\n\n"
            "## Objective\n\nTest pipe handling.\n",
            encoding="utf-8",
        )
        stories = ms.get_stories(sm_dir)
        ms.write_index(sm_dir, stories)
        content = (sm_dir / "index.md").read_text(encoding="utf-8")
        # The pipe in the name should be escaped for valid markdown tables
        assert "fix\\|bug" in content
        # The link path should use dir_name (no pipe)
        assert "stories/pipe-test/story.md" in content

    def test_prune_negative_days_rejected(self, sm_dir: Path):
        """--days with negative or zero value should fail."""
        with pytest.raises(SystemExit) as exc_info:
            ms.cmd_prune(sm_dir, days=0)
        assert exc_info.value.code == 1

    def test_get_stories_has_dir_name(self, sm_dir: Path, make_story):
        """get_stories should include dir_name for path construction."""
        make_story("my-story")
        stories = ms.get_stories(sm_dir)
        assert stories[0]["dir_name"] == "my-story"

    def test_objective_regex_last_section(self, sm_dir: Path):
        """Objective regex should match even when it's the last section in the file."""
        story_dir = sm_dir / "stories" / "last-section"
        story_dir.mkdir()
        # Objective is the very last section, no ## after it
        (story_dir / "story.md").write_text(
            "---\nname: last-section\nstatus: completed\n---\n\n"
            "## Objective\n\nThis is the final objective.\n",
            encoding="utf-8",
        )
        fm = ms.parse_frontmatter(story_dir / "story.md")
        summary = ms.create_archive_summary(story_dir, fm)
        assert "This is the final objective" in summary

    def test_checklist_regex_last_section(self, sm_dir: Path):
        """Checklist regex should match even when it's the last section."""
        story_dir = sm_dir / "stories" / "cl-last"
        story_dir.mkdir()
        (story_dir / "story.md").write_text(
            "---\nname: cl-last\nstatus: completed\n---\n\n"
            "## Objective\n\nObj text.\n\n"
            "## Checklist\n\n- [x] Final task done\n",
            encoding="utf-8",
        )
        fm = ms.parse_frontmatter(story_dir / "story.md")
        summary = ms.create_archive_summary(story_dir, fm)
        assert "Final task done" in summary

    def test_archive_creates_archive_dir(self, tmp_path: Path):
        """Archive should create archive/ if it doesn't exist."""
        sm_dir = tmp_path / ".speak-memory"
        sm_dir.mkdir()
        (sm_dir / "stories").mkdir()
        (sm_dir / "index.md").write_text(
            "# Story Index\n\n| Story | Status | Summary | Updated |\n|-------|--------|---------|---------|\n",
            encoding="utf-8",
        )
        # No archive/ dir yet
        story_dir = sm_dir / "stories" / "auto-archive"
        story_dir.mkdir()
        (story_dir / "story.md").write_text(
            "---\nname: auto-archive\nstatus: completed\nupdated: 2026-01-01\n---\n\n"
            "## Objective\n\nTest.\n\n## Checklist\n\n- [x] Done\n\n"
            "## Key Decisions\n\n(none)\n",
            encoding="utf-8",
        )
        ms.cmd_archive(sm_dir, "auto-archive")
        assert (sm_dir / "archive" / "auto-archive.md").exists()
