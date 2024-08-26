# Change Commit Date

`change_commit_date` is a tool to perform changes on the commit dates from the CLI.


## Requirements

- Python 3.9 or higher
- Git
- `sed` command line tool

## Installation

Clone the repository and navigate to the directory:

```sh
git clone https://github.com/demenus/change_commit_date.git
cd change_commit_date
```

## Usage

```
usage: python3 change_commit_date.py [-h] --commitHash COMMITHASH [--fullDate FULLDATE] [--now] [--todayAt HOUR] --path PATH

Modify the date of a commit in Git.

optional arguments:
  -h, --help            show this help message and exit
  --commitHash COMMITHASH
                        The hash of the commit to modify.
  --fullDate FULLDATE   Full date to set in format (e.g., "Wed Feb 16 14:00 2022 +0100").
  --now                 Use the current date and time.
  --todayAt TODAYAT     Set today's date to a specific time (24-hour format, e.g., "17:00").
  --path PATH, -p PATH  Relative or absolute path to the target repository.
```

## Contributions

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/new-feature`)
3. Make your changes and commit them (`git commit -m 'Add new feature'`)
4. Push your changes to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MPL v2.0 License. See the `LICENSE` file for more details.