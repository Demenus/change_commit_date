"""Pure date planning for daily commit windows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterable, List, Tuple


class WindowError(ValueError):
    """Raised when a daily window cannot be interpreted."""


def parse_time(value: str) -> time:
    try:
        hour, minute = (int(part) for part in value.split(":"))
    except (AttributeError, ValueError):
        raise WindowError("Time must use HH:MM in 24-hour format.")
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise WindowError("Time must use HH:MM in 24-hour format.")
    return time(hour=hour, minute=minute)


@dataclass(frozen=True)
class DailyWindow:
    """A half-open daily window [start, end), optionally crossing midnight."""

    start: time
    end: time

    @classmethod
    def parse(cls, value: str) -> "DailyWindow":
        try:
            start_value, end_value = value.split("-", 1)
        except (AttributeError, ValueError):
            raise WindowError("Window must use HH:MM-HH:MM (for example 18:00-03:00).")
        start, end = parse_time(start_value), parse_time(end_value)
        if start == end:
            raise WindowError("Window start and end must be different.")
        return cls(start=start, end=end)

    @property
    def crosses_midnight(self) -> bool:
        return self.start > self.end

    def contains(self, value: datetime) -> bool:
        current = value.timetz().replace(tzinfo=None)
        if self.crosses_midnight:
            return current >= self.start or current < self.end
        return self.start <= current < self.end

    def opening_on(self, value: datetime) -> datetime:
        return value.replace(
            hour=self.start.hour,
            minute=self.start.minute,
            second=0,
            microsecond=0,
        )

    def next_opening_on_or_after(self, value: datetime) -> datetime:
        """Return the first opening at or after *value* (or value when open)."""
        if self.contains(value):
            return value
        opening = self.opening_on(value)
        if opening < value:
            opening += timedelta(days=1)
        return opening

    def first_anchor(self, original: datetime) -> datetime:
        """Place an out-of-window first commit at the next opening naturally.

        Minutes, seconds and microseconds become an offset from the opening.  For
        the common ``18:00`` opening this turns ``10:12:34`` into ``18:12:34``.
        """
        if self.contains(original):
            return original
        opening = self.next_opening_on_or_after(original)
        candidate = opening + timedelta(
            minutes=original.minute,
            seconds=original.second,
            microseconds=original.microsecond,
        )
        return candidate if self.contains(candidate) else opening


@dataclass(frozen=True)
class PlannedCommit:
    commit_hash: str
    original: datetime
    planned: datetime

    @property
    def shift(self) -> timedelta:
        return self.planned - self.original


def plan_dates(
    commits: Iterable[Tuple[str, datetime]], window: DailyWindow
) -> List[PlannedCommit]:
    """Schedule ordered commits into *window*, preserving valid history first.

    A timestamp already inside the window is retained whenever doing so keeps
    the sequence ordered.  For an invalid timestamp we retain its original
    interval only when the translated result is also valid *on that original
    local calendar day*.  Otherwise it is placed at the next opening derived
    from the original timestamp, rather than being dragged into a later day by
    a previous adjustment.
    """
    entries = list(commits)
    if not entries:
        raise ValueError("At least one commit is required.")

    result: List[PlannedCommit] = []
    first_hash, first_original = entries[0]
    result.append(PlannedCommit(first_hash, first_original, window.first_anchor(first_original)))

    previous_original = first_original
    previous_planned = result[0].planned
    for commit_hash, original in entries[1:]:
        minimum = previous_planned + timedelta(microseconds=1)
        if window.contains(original) and original >= minimum:
            planned = original
        else:
            shifted = previous_planned + (original - previous_original)
            if (
                shifted >= minimum
                and shifted.date() == original.date()
                and window.contains(shifted)
            ):
                planned = shifted
            else:
                planned = window.next_opening_on_or_after(max(original, minimum))
        result.append(PlannedCommit(commit_hash, original, planned))
        previous_original, previous_planned = original, planned
    return result
