import os

from get_arguments import get_arguments
from get_new_date import get_new_date
from git_rebase_commit_date import git_rebase_commit_date


def main():
    args = get_arguments()
    commit_hash = args.commitHash

    # Convert the provided path to an absolute path
    repo_path = os.path.abspath(args.path)

    if not os.path.isdir(repo_path):
        print(f"The specified path '{repo_path}' is not a valid directory.")
        return

    new_date = get_new_date(args)
    if new_date is None:
        return

    git_rebase_commit_date(repo_path, commit_hash, new_date)


if __name__ == '__main__':
    main()
