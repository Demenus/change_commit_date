import datetime

def get_new_date(args):
    """Gets the new date based on the provided arguments."""
    if args.now:
        return datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y %z")
    elif args.fullDate:
        return args.fullDate
    elif args.todayAt:
        try:
            hour, minute = map(int, args.todayAt.split(':'))
            today = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            return today.strftime("%a %b %d %H:%M:%S %Y %z")
        except ValueError:
            print("The format of --todayAt must be HH:MM in 24-hour format (e.g., '17:00').")
            return None
    else:
        print(
            "You must specify a date with --fullDate, use --now for the current date, or use --todayAt for a specific time of the current day.")
        return None