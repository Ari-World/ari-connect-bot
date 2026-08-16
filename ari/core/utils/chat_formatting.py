import datetime
from typing import Optional, Sequence, SupportsInt


def humanize_list(items: Sequence[str]) -> str:
    """Join items into a comma-separated list, with 'and' before the last one.

    Examples
    --------
    >>> humanize_list(['One', 'Two', 'Three'])
    'One, Two, and Three'
    >>> humanize_list(['One'])
    'One'
    """
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def humanize_timedelta(
    *,
    timedelta: Optional[datetime.timedelta] = None,
    seconds: Optional[SupportsInt] = None,
    negative_format: Optional[str] = None,
    maximum_units: Optional[int] = None,
) -> str:
    """
    Get a human-readable timedelta representation.

    This works with either a timedelta object or a number of seconds.

    Fractional values will be omitted. Values that are less than 1 second
    but greater than -1 second will be an empty string.

    Parameters
    ----------
    timedelta: Optional[datetime.timedelta]
        A timedelta object
    seconds: Optional[SupportsInt]
        A number of seconds
    negative_format: Optional[str]
        How to format negative timedeltas, using %-formatting rules.
        Defaults to "negative %s"
    maximum_units: Optional[int]
        The maximum number of different units to output in the final string.

    Returns
    -------
    str
        A human-readable representation of the timedelta or seconds.

    Raises
    ------
    ValueError
        The function was called with neither a number of seconds nor a timedelta object,
        or with a maximum_units less than 1.

    Examples
    --------
    >>> humanize_timedelta(seconds=314)
    '5 minutes and 14 seconds'
    >>> humanize_timedelta(timedelta=datetime.timedelta(minutes=3.14), maximum_units=1)
    '3 minutes'
    """
    try:
        obj = seconds if seconds is not None else timedelta.total_seconds()
    except AttributeError:
        raise ValueError("You must provide either a timedelta or a number of seconds")
    if maximum_units is not None and maximum_units < 1:
        raise ValueError("maximum_units must be >= 1")

    periods = [
        ("year", "years", 60 * 60 * 24 * 365),
        ("month", "months", 60 * 60 * 24 * 30),
        ("day", "days", 60 * 60 * 24),
        ("hour", "hours", 60 * 60),
        ("minute", "minutes", 60),
        ("second", "seconds", 1),
    ]
    seconds = int(obj)
    if seconds < 0:
        seconds = -seconds
        if negative_format and "%s" not in negative_format:
            negative_format = negative_format + " %s"
        else:
            negative_format = negative_format or "negative %s"
    else:
        negative_format = "%s"
    strings = []
    maximum_units = maximum_units or len(periods)
    for period_name, plural_period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value == 0:
                continue
            unit = plural_period_name if period_value > 1 else period_name
            strings.append(f"{period_value} {unit}")
            if len(strings) == maximum_units:
                break

    return negative_format % humanize_list(strings)
