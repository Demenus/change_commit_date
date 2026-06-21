"""Command-line interface for Change Commit Date."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from .git import GitError, Repository
from .schedule import DailyWindow, WindowError, plan_dates, parse_time


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan and rewrite Git commit dates.")
    commands = parser.add_subparsers(dest="command", required=True)

    set_parser = commands.add_parser("set", help="Change one commit date.")
    _add_path_and_commit(set_parser)
    date = set_parser.add_mutually_exclusive_group(required=True)
    date.add_argument("--now", action="store_true", help="Use the current local date and time.")
    date.add_argument("--date", help="Use a Git-compatible full date string.")
    date.add_argument("--today-at", metavar="HH:MM", help="Use today at this local time.")
    date.add_argument("--same-day-at", metavar="HH:MM", help="Keep the commit day and set this time.")

    schedule_parser = commands.add_parser("schedule", help="Plan commits into a daily time window.")
    schedule_parser.add_argument("--path", "-p", required=True, help="Target repository path.")
    schedule_parser.add_argument("--window", required=True, metavar="HH:MM-HH:MM")
    source = schedule_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--commits-file", metavar="HASHES", help="One commit hash per line.")
    source.add_argument("--range", dest="revision_range", metavar="A..B", help="Git revision range.")
    schedule_parser.add_argument("--apply", action="store_true", help="Rewrite history after displaying the plan.")
    return parser


def _add_path_and_commit(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", "-p", required=True, help="Target repository path.")
    parser.add_argument("--commit", required=True, help="Commit hash to modify.")


def hashes_from_file(filename: str) -> Iterable[str]:
    try:
        content = Path(filename).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GitError(f"Could not read commits file '{filename}': {exc}") from exc
    for line in content:
        value = line.split("#", 1)[0].strip()
        if value:
            yield value


def _single_date(args, repo: Repository) -> datetime | str:
    if args.now:
        return datetime.now().astimezone()
    if args.date:
        value = args.date[:-1] + "+00:00" if args.date.endswith("Z") else args.date
        for parser in (datetime.fromisoformat, _parse_legacy_date):
            try:
                return parser(value)
            except ValueError:
                continue
        raise GitError("--date must be ISO 8601 or 'Wed Feb 16 14:00:00 2022 +0100'.")
    if args.today_at:
        hour, minute = parse_time(args.today_at)
        return datetime.now().astimezone().replace(hour=hour, minute=minute, second=0, microsecond=0)
    hour, minute = parse_time(args.same_day_at)
    return repo.get_commit(repo.resolve_commit(args.commit)).author_date.replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )


def _parse_legacy_date(value: str) -> datetime:
    return datetime.strptime(value, "%a %b %d %H:%M:%S %Y %z")


def _render_plan(planned) -> None:
    print("hash      original                       planned                        interval change")
    previous_original = previous_planned = None
    for entry in planned:
        if previous_original is None:
            interval_change = "anchor"
        else:
            original_gap = entry.original - previous_original
            planned_gap = entry.planned - previous_planned
            interval_change = str(planned_gap - original_gap)
        print(
            f"{entry.commit_hash[:8]}  {entry.original.isoformat(sep=' ', timespec='seconds')}  "
            f"{entry.planned.isoformat(sep=' ', timespec='seconds')}  {interval_change}"
        )
        previous_original, previous_planned = entry.original, entry.planned


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo = Repository(args.path)
        repo.ensure_safe_to_rewrite()
        if args.command == "set":
            commit_id = repo.resolve_commit(args.commit)
            planned_date = _single_date(args, repo)
            from .schedule import PlannedCommit
            rewritten = repo.rewrite([PlannedCommit(commit_id, repo.get_commit(commit_id).author_date, planned_date)])
            print(f"{commit_id[:8]} -> {rewritten[commit_id][:8]}")
            return 0

        window = DailyWindow.parse(args.window)
        requested = hashes_from_file(args.commits_file) if args.commits_file else repo.commits_in_range(args.revision_range)
        commits = repo.select_linear_commits(requested)
        planned = plan_dates(((commit.commit_hash, commit.author_date) for commit in commits), window)
        _render_plan(planned)
        if not args.apply:
            print("Preview only. Run again with --apply to rewrite history.")
            return 0
        rewritten = repo.rewrite(planned)
        print("Rewritten commits:")
        for entry in planned:
            print(f"{entry.commit_hash} -> {rewritten[entry.commit_hash]}")
        return 0
    except (GitError, WindowError, ValueError) as exc:
        print(f"Error: {exc}", file=__import__("sys").stderr)
        return 2


def main() -> None:
    raise SystemExit(run())
