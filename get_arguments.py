import argparse

def get_arguments():
    """Gets and parses the command line arguments."""
    parser = argparse.ArgumentParser(description="Modify the date of a commit in Git.")
    parser.add_argument('--commitHash', type=str, required=True, help='The hash of the commit to modify.')
    parser.add_argument('--fullDate', type=str,
                        help='Full date to set in format (e.g., "Wed Feb 16 14:00 2022 +0100").')
    parser.add_argument('--now', action='store_true', help='Use the current date and time.')
    parser.add_argument('--todayAt', type=str,
                        help='Set today\'s date to a specific time (24-hour format, e.g., "17:00").')
    parser.add_argument('--path', '-p', type=str, required=True,
                        help='Relative or absolute path to the target repository.')
    return parser.parse_args()

