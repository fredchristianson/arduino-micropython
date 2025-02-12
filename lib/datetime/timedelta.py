# datetime.py


_DBM = (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
_DIM = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_TIME_SPEC = ("auto", "hours", "minutes", "seconds", "milliseconds", "microseconds")


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _dby(y):
    # year -> number of days before January 1st of year.
    Y = y - 1
    return Y * 365 + Y // 4 - Y // 100 + Y // 400


def _dim(y, m):
    # year, month -> number of days in that month in that year.
    if m == 2 and _leap(y):
        return 29
    return _DIM[m]


def _dbm(y, m):
    # year, month -> number of days in year preceding first day of month.
    return _DBM[m] + (m > 2 and _leap(y))


def _ymd2o(y, m, d):
    # y, month, day -> ordinal, considering 01-Jan-0001 as day 1.
    return _dby(y) + _dbm(y, m) + d


def _o2ymd(n):
    # ordinal -> (year, month, day), considering 01-Jan-0001 as day 1.
    n -= 1
    n400, n = divmod(n, 146_097)
    y = n400 * 400 + 1
    n100, n = divmod(n, 36_524)
    n4, n = divmod(n, 1_461)
    n1, n = divmod(n, 365)
    y += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        return y - 1, 12, 31
    m = (n + 50) >> 5
    prec = _dbm(y, m)
    if prec > n:
        m -= 1
        prec -= _dim(y, m)
    n -= prec
    return y, m, n + 1


MINYEAR = 1
MAXYEAR = 9_999


class timedelta:
    def __init__(
        self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    ):
        s = (((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds
        self._us = round((s * 1000 + milliseconds) * 1000 + microseconds)

    def __repr__(self):
        return "datetime.timedelta(microseconds={})".format(self._us)

    def total_seconds(self):
        return self._us / 1_000_000

    @property
    def days(self):
        return self._tuple(2)[0]

    @property
    def seconds(self):
        return self._tuple(3)[1]

    @property
    def microseconds(self):
        return self._tuple(3)[2]

    def __add__(self, other):
        if isinstance(other, datetime):
            return other.__add__(self)
        else:
            us = other._us
        return timedelta(0, 0, self._us + us)

    def __sub__(self, other):
        return timedelta(0, 0, self._us - other._us)

    def __neg__(self):
        return timedelta(0, 0, -self._us)

    def __pos__(self):
        return self

    def __abs__(self):
        return -self if self._us < 0 else self

    def __mul__(self, other):
        return timedelta(0, 0, round(other * self._us))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, timedelta):
            return self._us / other._us
        else:
            return timedelta(0, 0, round(self._us / other))

    def __floordiv__(self, other):
        if isinstance(other, timedelta):
            return self._us // other._us
        else:
            return timedelta(0, 0, int(self._us // other))

    def __mod__(self, other):
        return timedelta(0, 0, self._us % other._us)

    def __divmod__(self, other):
        q, r = divmod(self._us, other._us)
        return q, timedelta(0, 0, r)

    def __eq__(self, other):
        return self._us == other._us

    def __le__(self, other):
        return self._us <= other._us

    def __lt__(self, other):
        return self._us < other._us

    def __ge__(self, other):
        return self._us >= other._us

    def __gt__(self, other):
        return self._us > other._us

    def __bool__(self):
        return self._us != 0

    def __str__(self):
        return self._format(0x40)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._us)
        return self._hash

    def isoformat(self):
        return self._format(0)

    def _format(self, spec=0):
        if self._us >= 0:
            td = self
            g = ""
        else:
            td = -self
            g = "-"
        d, h, m, s, us = td._tuple(5)
        ms, us = divmod(us, 1000)
        r = ""
        if spec & 0x40:
            spec &= ~0x40
            hr = str(h)
        else:
            hr = f"{h:02d}"
        if spec & 0x20:
            spec &= ~0x20
            spec |= 0x10
            r += "UTC"
        if spec & 0x10:
            spec &= ~0x10
            if not g:
                g = "+"
        if d:
            p = "s" if d > 1 else ""
            r += f"{g}{d} day{p}, "
            g = ""
        if spec == 0:
            spec = 5 if (ms or us) else 3
        if spec >= 1 or h:
            r += f"{g}{hr}"
            if spec >= 2 or m:
                r += f":{m:02d}"
                if spec >= 3 or s:
                    r += f":{s:02d}"
                    if spec >= 4 or ms:
                        r += f".{ms:03d}"
                        if spec >= 5 or us:
                            r += f"{us:03d}"
        return r

    def tuple(self):
        return self._tuple(5)

    def _tuple(self, n):
        d, us = divmod(self._us, 86_400_000_000)
        if n == 2:
            return d, us
        s, us = divmod(us, 1_000_000)
        if n == 3:
            return d, s, us
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return d, h, m, s, us


timedelta.min = timedelta(days=-999_999_999)
timedelta.max = timedelta(days=999_999_999, hours=23, minutes=59, seconds=59, microseconds=999_999)
timedelta.resolution = timedelta(microseconds=1)
