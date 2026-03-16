"""
Commit metadata from the repository (e.g. author date).
Uses git to read the current commit information.
"""

import datetime

from run_git_command import run_git_command

# Git format %ai: "2022-02-16 14:00:00 +0100"
GIT_AUTHOR_DATE_FMT = "%Y-%m-%d %H:%M:%S %z"


class CommitInfo:
    """Holds repository path and commit hash; provides commit metadata via git."""

    def __init__(self, repo_path, commit_hash):
        self.repo_path = repo_path
        self.commit_hash = commit_hash

    def get_author_date(self):
        """
        Returns the commit's author date as a timezone-aware datetime.
        Raises Exception if the commit cannot be read (e.g. invalid hash).
        """
        out = run_git_command(
            self.repo_path,
            ["git", "show", "-s", "--format=%ai", self.commit_hash],
        )
        out = out.strip()
        return datetime.datetime.strptime(out, GIT_AUTHOR_DATE_FMT)
