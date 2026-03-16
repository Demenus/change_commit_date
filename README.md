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

Run from the project directory:

```bash
python change_commit_date.py --path <repo_path> --commitHash <hash> <date_option>
```

### Required arguments

| Argument | Description |
|----------|-------------|
| `--path`, `-p` | Relative or absolute path to the target repository. |
| `--commitHash` | Full or short (abbreviated) hash of the commit to modify (e.g. `abc1234` or 40 chars). |

### Date options (pick one)

| Option | Description |
|--------|-------------|
| `--now` | Use the current date and time. |
| `--fullDate` | Full date string (e.g. `"Wed Feb 16 14:00:00 2022 +0100"`). |
| `--todayAt HH:MM` | Today’s date at the given time (24-hour format, e.g. `17:00`). Seconds are randomized. |
| `--sameDayAt HH:MM` | Keep the commit’s date, set only the time (24-hour format). Seconds are randomized. |

### Examples

```bash
# Set commit to current time (short hash)
python change_commit_date.py -p . --commitHash abc1234 --now

# Today at 17:30
python change_commit_date.py -p ./my-repo --commitHash abc1234 --todayAt 17:30

# Same day as the commit, but at 09:00
python change_commit_date.py -p ./my-repo --commitHash abc1234 --sameDayAt 09:00

# Explicit full date
python change_commit_date.py -p ./my-repo --commitHash abc1234 --fullDate "Wed Feb 16 14:00:00 2022 +0100"
```

For full CLI help:

```bash
python change_commit_date.py --help
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