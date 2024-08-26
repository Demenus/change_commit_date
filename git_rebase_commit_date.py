import os
import time

from run_git_command import run_git_command


class GitCommitDateChanger:
    """Helper class to perform git rebasing and commit date modification."""

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def start_interactive_rebase(self, commit_hash):
        """Starts an interactive rebase from the commit's parent."""
        short_commit_hash = commit_hash[:7]

        sed_command = f"sequence.editor=\"sed -i -e 's/^pick {short_commit_hash}/edit {short_commit_hash}/' \" "
        rebase_command = ["git", "-c", sed_command, "rebase", "-i", f"{commit_hash}^", "--committer-date-is-author-date"]
        run_git_command(self.repo_path, " ".join(rebase_command), shell=True)

    def amend_commit_date(self, new_date):
        """Amends the commit with the new date."""
        d = f"\"{new_date}\""
        amend_command = [
            "git", "commit", "--amend", "--no-edit", "--date", d
        ]
        run_git_command(self.repo_path, amend_command)

    def continue_rebase(self):
        """Continues the rebase process."""
        continue_rebase_command = ["git", "rebase", "--continue"]
        run_git_command(self.repo_path, continue_rebase_command)

    def git_rebase_commit_date(self, commit_hash, new_date):
        """Changes the date of a commit specified by commit_hash to new_date in the specified repository."""
        self.start_interactive_rebase(commit_hash)
        self.amend_commit_date(new_date)
        self.continue_rebase()
        print(f"Commit date {commit_hash} changed to {new_date}.")


def git_rebase_commit_date(repo_path, commit_hash, new_date):
    commit_changer = GitCommitDateChanger(repo_path)
    commit_changer.git_rebase_commit_date(commit_hash, new_date)