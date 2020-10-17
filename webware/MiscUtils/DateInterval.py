"""DateInterval.py

Convert interval strings (in the form of 1w2d, etc) to seconds, and back again.
Is not exactly about months or years (leap years in particular).

Accepts (y)ear, (b)month, (w)eek, (d)ay, (h)our, (m)inute, (s)econd.

Exports only timeEncode and timeDecode functions.
"""

__all__ = ['timeEncode', 'timeDecode']

import re

from operator import itemgetter

second = 1
minute = second*60
hour = minute*60
day = hour*24
week = day*7
month = day*30
year = day*365
timeValues = {
    'y': year,
    'b': month,
    'w': week,
    'd': day,
    'h': hour,
    'm': minute,
    's': second,
}
timeOrdered = sorted(timeValues.items(), key=itemgetter(1), reverse=True)


def timeEncode(seconds):
    """Encode a number of seconds (representing a time interval).

    Encode the number into a form like 2d1h3s.
    """
    s = []
    for char, amount in timeOrdered:
        if seconds >= amount:
            i, seconds = divmod(seconds, amount)
            s.append(f'{i}{char}')
    return ''.join(s)


_timeRE = re.compile(r'[0-9]+[a-zA-Z]')


def timeDecode(s):
    """Decode a number in the format 1h4d3m (1 hour, 3 days, 3 minutes).

    Decode the format into a number of seconds.
    """
    time = 0
    for match in _timeRE.findall(s):
        char = match[-1].lower()
        try:
            time += int(match[:-1]) * timeValues[char]
        except KeyError:
            raise ValueError(f'Invalid unit of time: {char}') from None
    return time
