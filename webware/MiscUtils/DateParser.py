"""DateParser.py

Convert string representations of dates to Python datetime objects.

If installed, we will use the python-dateutil package to parse dates,
otherwise we try to use the strptime function in the Python standard library
with several frequently used formats.
"""

__all__ = ['parseDateTime', 'parseDate', 'parseTime']

try:

    from dateutil.parser import parse as parseDateTime

except ImportError:  # dateutil not available

    from datetime import datetime

    strpdatetime = datetime.strptime

    def parseDateTime(s):
        """Return a datetime object corresponding to the given string."""
        formats = (
            "%a %b %d %H:%M:%S %Y", "%a, %d-%b-%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
            "%Y%m%d %H:%M:%S", "%Y%m%dT%H:%M:%S",
            "%Y%m%d %H%M%S", "%Y%m%dT%H%M%S",
            "%m/%d/%y %H:%M:%S", "%Y-%m-%d %H:%M",
            "%Y-%m-%d", "%Y%m%d", "%m/%d/%y",
            "%H:%M:%S", "%H:%M", "%c")
        for fmt in formats:
            try:
                return strpdatetime(s, fmt)
            except ValueError:
                pass
        raise ValueError(f'Cannot parse date/time {s}')


def parseDate(s):
    """Return a date object corresponding to the given string."""
    return parseDateTime(s).date()


def parseTime(s):
    """Return a time object corresponding to the given string."""
    return parseDateTime(s).time()
