import os
import subprocess
import time


class GitCommitDateChanger:
    """Helper class to perform git rebasing and commit date modification."""

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def run_git_command(self, command, background=False, shell=True):
        """Runs a git command in the specified repository and returns the output."""
        if not background:
            result = subprocess.run(command, cwd=self.repo_path, check=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True, shell=shell)
            return result.stdout.strip()
        else:
            return subprocess.Popen(command, cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, shell=shell)

    def wait_for_file(self, filepath, timeout=10, interval=1):
        """Wait for a file to exist for up to `timeout` seconds, checking every `interval` seconds."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(filepath):
                return True
            time.sleep(interval)
        return False

    def status(self):
        command = ["git", "status"]
        self.run_git_command(command, shell=False)

    def start_interactive_rebase(self, commit_hash):
        """Starts an interactive rebase from the commit's parent."""
        rebase_command = ["git", "rebase", "-i", f"{commit_hash}^"]
        self.run_git_command(rebase_command, background=True, shell=False)

    def modify_rebase_todo_file(self, commit_hash):
        """Modifies the rebase todo file to set the commit for editing."""
        rebase_todo_path = os.path.join(self.repo_path, ".git", "rebase-merge", "git-rebase-todo")
        if not self.wait_for_file(rebase_todo_path):
            print(f"Error: The rebase todo file does not exist even after waiting.")
            return False

        with open(rebase_todo_path, 'r') as file:
            lines = file.readlines()

        with open(rebase_todo_path, 'w') as file:
            for line in lines:
                if line.startswith(f"pick {commit_hash}"):
                    file.write(line.replace("pick", "edit"))
                else:
                    file.write(line)
        return True

    def amend_commit_date(self, new_date):
        """Amends the commit with the new date."""
        amend_command = [
            "sh", "-c",
            f'GIT_COMMITTER_DATE="{new_date}" GIT_AUTHOR_DATE="{new_date}" git commit --amend --no-edit'
        ]
        self.run_git_command(amend_command, shell=False)

    def continue_rebase(self):
        """Continues the rebase process."""
        continue_rebase_command = ["git", "rebase", "--continue"]
        self.run_git_command(continue_rebase_command, shell=False)

    def git_rebase_commit_date(self, commit_hash, new_date):
        """Changes the date of a commit specified by commit_hash to new_date in the specified repository."""
        self.status()
        self.start_interactive_rebase(commit_hash)
        if self.modify_rebase_todo_file(commit_hash):
            self.amend_commit_date(new_date)
            self.continue_rebase()
            print(f"Commit date {commit_hash} changed to {new_date}.")
        else:
            print(f"Failed to modify the rebase todo file for commit {commit_hash}.")


def git_rebase_commit_date(repo_path, commit_hash, new_date):
    commit_changer = GitCommitDateChanger(repo_path)
    commit_changer.git_rebase_commit_date(commit_hash, new_date)