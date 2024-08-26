import subprocess

def run_git_command(repo_path, command, background=False, shell=False):
    """Runs a git command in the specified repository and returns the output."""
    if not shell and not (isinstance(command, list) and all(isinstance(item, str) for item in command)):
        raise ValueError("The command must be a list of strings")
    try:
        if not background:
            result = subprocess.run(command, cwd=repo_path, check=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True, shell=shell)
            return result.stdout.strip()
        else:
            p = subprocess.Popen(command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, shell=shell)
            print(p.stdout.read())
            print(p.stderr.read())
            p.wait()
    except subprocess.CalledProcessError as e:
        raise Exception(e.stderr)