import datetime
import random

from commit_info import CommitInfo

DATE_FMT = "%a %b %d %H:%M:%S %Y %z"


def _random_second_and_microsecond():
    """Returns (second, microsecond) with random values for a more realistic look."""
    return random.randint(0, 59), random.randint(0, 999_999)


def _parse_time_hhmm(time_str):
    """Parse HH:MM string, returns (hour, minute) or None on error."""
    try:
        hour, minute = map(int, time_str.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (ValueError, AttributeError):
        pass
    return None


def get_new_date_same_day_at(repo_path, commit_hash, time_str):
    """
    Gets a new date with the commit's own date but the given time (HH:MM).
    """
    parsed = _parse_time_hhmm(time_str)
    if parsed is None:
        print("The format of --sameDayAt must be HH:MM in 24-hour format (e.g., '17:00').")
        return None
    hour, minute = parsed

    try:
        commit = CommitInfo(repo_path, commit_hash)
        author_dt = commit.get_author_date()
    except Exception as e:
        print(f"Could not read commit date: {e}")
        return None

    sec, usec = _random_second_and_microsecond()
    new_dt = author_dt.replace(hour=hour, minute=minute, second=sec, microsecond=usec)
    return new_dt.strftime(DATE_FMT)


def get_new_date(args, repo_path=None, commit_hash=None):
    """Gets the new date based on the provided arguments."""
    if args.now:
        return datetime.datetime.now().strftime(DATE_FMT)
    elif args.fullDate:
        return args.fullDate
    elif args.todayAt:
        parsed = _parse_time_hhmm(args.todayAt)
        if parsed is None:
            print("The format of --todayAt must be HH:MM in 24-hour format (e.g., '17:00').")
            return None
        hour, minute = parsed
        sec, usec = _random_second_and_microsecond()
        today = datetime.datetime.now().replace(hour=hour, minute=minute, second=sec, microsecond=usec)
        return today.strftime(DATE_FMT)
    elif args.sameDayAt:
        if repo_path is None or commit_hash is None:
            print("Internal error: repo_path and commit_hash are required for --sameDayAt.")
            return None
        return get_new_date_same_day_at(repo_path, commit_hash, args.sameDayAt)
    else:
        print(
            "You must specify a date with --fullDate, use --now for the current date, "
            "use --todayAt for a specific time today, or --sameDayAt for a time on the commit's date."
        )
        return None