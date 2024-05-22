


from contextvars import ContextVar
import datetime
import functools
from typing import Callable, Iterator, List, Optional, Sequence, SupportsInt, Union

import babel
from babel.lists import format_list as babel_list
from babel.numbers import format_decimal
from discord import Locale

from ..i18n import Translator, get_babel_locale



_current_locale = ContextVar("_current_locale", default="en-US")

_ = Translator("UtilsChatFormatting", __file__)


def humanize_list(
    items: Sequence[str], *, locale: Optional[str] = None, style: str = "standard"
) -> str:
    """Get comma-separated list, with the last element joined with *and*.

    Parameters
    ----------
    items : Sequence[str]
        The items of the list to join together.
    locale : Optional[str]
        The locale to convert, if not specified it defaults to the bot's locale.
    style : str
        The style to format the list with.

        Note: Not all styles are necessarily available in all locales,
        see documentation of `babel.lists.format_list` for more details.

        standard
            A typical 'and' list for arbitrary placeholders.
            eg. "January, February, and March"
        standard-short
             A short version of a 'and' list, suitable for use with short or
             abbreviated placeholder values.
             eg. "Jan., Feb., and Mar."
        or
            A typical 'or' list for arbitrary placeholders.
            eg. "January, February, or March"
        or-short
            A short version of an 'or' list.
            eg. "Jan., Feb., or Mar."
        unit
            A list suitable for wide units.
            eg. "3 feet, 7 inches"
        unit-short
            A list suitable for short units
            eg. "3 ft, 7 in"
        unit-narrow
            A list suitable for narrow units, where space on the screen is very limited.
            eg. "3′ 7″"

    Raises
    ------
    ValueError
        The locale does not support the specified style.

    Examples
    --------
    .. testsetup::

        from redbot.core.utils.chat_formatting import humanize_list

    .. doctest::

        >>> humanize_list(['One', 'Two', 'Three'])
        'One, Two, and Three'
        >>> humanize_list(['One'])
        'One'
        >>> humanize_list(['omena', 'peruna', 'aplari'], style='or', locale='fi')
        'omena, peruna tai aplari'

    """

    return babel_list(items, style=style, locale=get_babel_locale(locale))

def humanize_timedelta(
    *,
    timedelta: Optional[datetime.timedelta] = None,
    seconds: Optional[SupportsInt] = None,
    negative_format: Optional[str] = None,
    maximum_units: Optional[int] = None,
) -> str:
    """
    Get a locale aware human timedelta representation.

    This works with either a timedelta object or a number of seconds.

    Fractional values will be omitted.

    Values that are less than 1 second but greater than -1 second
    will be an empty string.

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
        A locale aware representation of the timedelta or seconds.

    Raises
    ------
    ValueError
        The function was called with neither a number of seconds nor a timedelta object,
        or with a maximum_units less than 1.

    Examples
    --------
    .. testsetup::

        from datetime import timedelta
        from redbot.core.utils.chat_formatting import humanize_timedelta

    .. doctest::

        >>> humanize_timedelta(seconds=314)
        '5 minutes, 14 seconds'
        >>> humanize_timedelta(timedelta=timedelta(minutes=3.14), maximum_units=1)
        '3 minutes'
        >>> humanize_timedelta(timedelta=timedelta(days=-3.14), negative_format="%s ago", maximum_units=3)
        '3 days, 3 hours, 21 minutes ago'
    """

    try:
        obj = seconds if seconds is not None else timedelta.total_seconds()
    except AttributeError:
        raise ValueError("You must provide either a timedelta or a number of seconds")
    if maximum_units is not None and maximum_units < 1:
        raise ValueError("maximum_units must be >= 1")

    periods = [
        (_("year"), _("years"), 60 * 60 * 24 * 365),
        (_("month"), _("months"), 60 * 60 * 24 * 30),
        (_("day"), _("days"), 60 * 60 * 24),
        (_("hour"), _("hours"), 60 * 60),
        (_("minute"), _("minutes"), 60),
        (_("second"), _("seconds"), 1),
    ]
    seconds = int(obj)
    if seconds < 0:
        seconds = -seconds
        if negative_format and "%s" not in negative_format:
            negative_format = negative_format + " %s"
        else:
            negative_format = negative_format or (_("negative") + " %s")
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

    return negative_format % humanize_list(strings, style="unit")