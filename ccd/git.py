"""Git access and controlled history rewriting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import Dict, Iterable, List, Mapping, Sequence

from .schedule import PlannedCommit


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Commit:
    commit_hash: str
    parents: Sequence[str]
    author_date: datetime


class Repository:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def _run(self, args: Sequence[str], *, env=None, check=True) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                list(args), cwd=self.path, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, env=env, check=check,
            )
        except FileNotFoundError as exc:
            raise GitError("Git is not installed or is not available in PATH.") from exc
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip()
            raise GitError(detail or "Git command failed.") from exc

    def output(self, args: Sequence[str]) -> str:
        return self._run(args).stdout.strip()

    def ensure_safe_to_rewrite(self) -> None:
        if self.output(["git", "rev-parse", "--is-inside-work-tree"]) != "true":
            raise GitError(f"'{self.path}' is not a Git working tree.")
        if self.output(["git", "status", "--porcelain"]):
            raise GitError("Working tree is not clean. Commit, stash, or discard changes first.")
        for name in ("rebase-merge", "rebase-apply"):
            state_path = self.output(["git", "rev-parse", "--git-path", name])
            if os.path.exists(os.path.join(self.path, state_path)):
                raise GitError("A rebase is already in progress. Finish or abort it first.")

    def head(self) -> str:
        return self.output(["git", "rev-parse", "HEAD"])

    def resolve_commit(self, value: str) -> str:
        return self.output(["git", "rev-parse", "--verify", f"{value}^{{commit}}"])

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        result = self._run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant], check=False
        )
        return result.returncode == 0

    def get_commit(self, commit_hash: str) -> Commit:
        data = self.output(["git", "show", "-s", "--format=%H%x00%P%x00%aI", commit_hash])
        commit_id, parents, author_date = data.split("\x00", 2)
        # Python 3.9's fromisoformat does not accept Git's ``Z`` UTC suffix.
        if author_date.endswith("Z"):
            author_date = author_date[:-1] + "+00:00"
        return Commit(commit_id, tuple(filter(None, parents.split())), datetime.fromisoformat(author_date))

    def commits_after(self, base: str) -> List[str]:
        return self.output(["git", "rev-list", "--reverse", "--topo-order", f"{base}..HEAD"]).splitlines()

    def commits_in_range(self, revision_range: str) -> List[str]:
        return self.output(["git", "rev-list", "--reverse", "--topo-order", revision_range]).splitlines()

    def select_linear_commits(self, requested: Iterable[str]) -> List[Commit]:
        requested_ids = {self.resolve_commit(value) for value in requested}
        if not requested_ids:
            raise GitError("No commits were selected.")
        head = self.head()
        invalid = [commit_id for commit_id in requested_ids if not self.is_ancestor(commit_id, head)]
        if invalid:
            raise GitError("Every selected commit must be an ancestor of HEAD.")
        commits = [self.get_commit(commit_id) for commit_id in requested_ids]
        earliest = next(
            commit for commit in commits if not any(
                commit.commit_hash != other.commit_hash
                and self.is_ancestor(other.commit_hash, commit.commit_hash)
                for other in commits
            )
        )
        if not earliest.parents:
            raise GitError("The root commit cannot be rewritten by this version.")
        chain = self.commits_after(earliest.parents[0])
        if any(len(self.get_commit(commit_id).parents) > 1 for commit_id in chain):
            raise GitError("Merge commits are not supported by schedule in this version.")
        return [self.get_commit(commit_id) for commit_id in chain if commit_id in requested_ids]

    def rewrite(self, planned: Sequence[PlannedCommit]) -> Mapping[str, str]:
        """Rewrite planned commits in one interactive rebase and return old/new ids."""
        if not planned:
            return {}
        selected = [entry.commit_hash for entry in planned]
        first = self.get_commit(selected[0])
        if not first.parents:
            raise GitError("The root commit cannot be rewritten by this version.")

        with tempfile.TemporaryDirectory(prefix="change-commit-date-") as temp_dir:
            editor_path = Path(temp_dir) / "sequence_editor.py"
            editor_path.write_text(_sequence_editor_source(selected), encoding="utf-8")
            editor_path.chmod(editor_path.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["GIT_SEQUENCE_EDITOR"] = (
                f"{shlex.quote(sys.executable)} {shlex.quote(str(editor_path))}"
            )
            env["GIT_EDITOR"] = "true"
            result = self._run(
                [
                    "git", "-c", "commit.gpgSign=false", "rebase", "-i",
                    "--committer-date-is-author-date", first.parents[0],
                ],
                env=env,
                check=False,
            )
            if not self._rebase_active():
                raise GitError(result.stderr.strip() or "Rebase did not stop at a selected commit.")

            rewritten: Dict[str, str] = {}
            for index, entry in enumerate(planned):
                self._ensure_rebase_can_amend()
                date_value = entry.planned.isoformat(sep=" ", timespec="microseconds")
                amend_env = os.environ.copy()
                amend_env["GIT_AUTHOR_DATE"] = date_value
                amend_env["GIT_COMMITTER_DATE"] = date_value
                amend_env["GIT_EDITOR"] = "true"
                self._run(
                    ["git", "commit", "--amend", "--no-edit", "--no-gpg-sign", "--date", date_value],
                    env=amend_env,
                )
                rewritten[entry.commit_hash] = self.head()
                result = self._run(["git", "rebase", "--continue"], env=amend_env, check=False)
                if index == len(planned) - 1:
                    if result.returncode != 0 or self._rebase_active():
                        raise GitError(result.stderr.strip() or "Could not finish the rebase.")
                elif not self._rebase_active():
                    raise GitError(result.stderr.strip() or "Rebase stopped before the next selected commit.")
            return rewritten

    def _rebase_active(self) -> bool:
        for name in ("rebase-merge", "rebase-apply"):
            state_path = self.output(["git", "rev-parse", "--git-path", name])
            if os.path.exists(os.path.join(self.path, state_path)):
                return True
        return False

    def _ensure_rebase_can_amend(self) -> None:
        unresolved = self._run(
            ["git", "diff", "--name-only", "--diff-filter=U"], check=False
        ).stdout.strip()
        if unresolved:
            raise GitError("Rebase has conflicts. Resolve them or run 'git rebase --abort'.")
        head = self._run(["git", "rev-parse", "--verify", "REBASE_HEAD"], check=False)
        if head.returncode != 0:
            raise GitError("Rebase did not pause at a selected commit.")


def _sequence_editor_source(selected: Sequence[str]) -> str:
    encoded = json.dumps(list(selected))
    return f'''#!{sys.executable}
import sys

selected = {encoded}
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    lines = handle.readlines()
with open(path, "w", encoding="utf-8") as handle:
    for line in lines:
        parts = line.split(maxsplit=2)
        if len(parts) >= 2 and parts[0] == "pick" and any(value.startswith(parts[1]) for value in selected):
            line = "edit " + line[len("pick "):]
        handle.write(line)
'''
