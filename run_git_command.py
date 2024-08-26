import subprocess

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