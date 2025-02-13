# datetime.py

import time as _tmod

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


class tzinfo:
    # abstract class
    def tzname(self, dt):
        raise NotImplementedError

    def utcoffset(self):
        raise NotImplementedError

    def dst(self, dt):
        raise NotImplementedError

    def fromutc(self, dt):
        if dt._tz is not self:
            raise ValueError

        # See original datetime.py for an explanation of this algorithm.
        dtoff = dt.utcoffset()
        dtdst = dt.dst()
        delta = dtoff - dtdst
        if delta:
            dt += delta
            dtdst = dt.dst()
        return dt + dtdst

    def isoformat(self, dt):
        return self.utcoffset()._format(0x12)


class timezone(tzinfo):
    utc = None
    default = None
    
    @classmethod
    def set_default(cls,tz):
        cls.default = tz
        
    @classmethod
    def get_default(cls):
        return cls.default or cls.utc
    
    def __init__(self, offset,is_dst=False, name=None,abbrev=None,dst_offset=timedelta(hours=1)):
        if not (abs(offset._us) < 86_400_000_000):
            raise ValueError
        self._offset = offset
        self._is_dst = is_dst
        self._dst_offset = dst_offset
        self._name = name
        self._abbrev = abbrev
        if timezone.default == None:
            timezone.default = self
            

    def __repr__(self):
        return "datetime.timezone({}, {})".format(repr(self._offset), repr(self._name))

    def __eq__(self, other):
        if isinstance(other, timezone):
            return self._offset == other._offset
        return NotImplemented

    def __str__(self):
        return self.tzname()

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._offset, self._name))
        return self._hash

    def utcoffset(self):
        if self._is_dst:
            return self._offset + self._dst_offset
        return self._offset
    
    def utcoffset_seconds(self):
        return self.utcoffset().total_seconds()

    def is_dst(self):
        return self._is_dst

    def tzname(self):
        if self._name:
            return self._name
        return self._offset._format(0x22)

    def fromutc(self, dt):
        return dt + self.utcoffset()
    
    def isoformat(self):
        return self.utcoffset()._format(2)
    


timezone.utc = timezone(timedelta(0),abbrev="gmt")


def _date(y, m, d):
    if MINYEAR <= y <= MAXYEAR and 1 <= m <= 12 and 1 <= d <= _dim(y, m):
        return _ymd2o(y, m, d)
    elif y == 0 and m == 0 and 1 <= d <= 3_652_059:
        return d
    else:
        raise ValueError


def _iso2d(s):  # ISO -> date
    if len(s) < 10 or s[4] != "-" or s[7] != "-":
        raise ValueError
    return int(s[0:4]), int(s[5:7]), int(s[8:10])


def _d2iso(o):  # date -> ISO
    return "%04d-%02d-%02d" % _o2ymd(o)


class date:
    def __init__(self, year, month, day):
        self._ord = _date(year, month, day)

    @classmethod
    def fromtimestamp(cls, ts):
        return cls(*_tmod.localtime(ts)[:3])

    @classmethod
    def today(cls):
        return cls(*_tmod.localtime()[:3])


    @classmethod
    def fromisoformat(cls, s):
        return cls(*_iso2d(s))

    @property
    def year(self):
        return self.tuple()[0]

    @property
    def month(self):
        return self.tuple()[1]

    @property
    def day(self):
        return self.tuple()[2]

    def toordinal(self):
        return self._ord

    def timetuple(self):
        y, m, d = self.tuple()
        yday = _dbm(y, m) + d
        return (y, m, d, 0, 0, 0, self.weekday(), yday, -1)

    def replace(self, year=None, month=None, day=None):
        year_, month_, day_ = self.tuple()
        if year is None:
            year = year_
        if month is None:
            month = month_
        if day is None:
            day = day_
        return date(year, month, day)


    def __eq__(self, other):
        if isinstance(other, date):
            return self._ord == other._ord
        else:
            return False

    def __le__(self, other):
        return self._ord <= other._ord

    def __lt__(self, other):
        return self._ord < other._ord

    def __ge__(self, other):
        return self._ord >= other._ord

    def __gt__(self, other):
        return self._ord > other._ord

    def weekday(self):
        return (self._ord + 6) % 7

    def isoweekday(self):
        return self._ord % 7 or 7

    def isoformat(self):
        return _d2iso(self._ord)

    def __repr__(self):
        return "datetime.date(0, 0, {})".format(self._ord)

    __str__ = isoformat

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._ord)
        return self._hash

    def tuple(self):
        return _o2ymd(self._ord)


date.min = date(MINYEAR, 1, 1)
date.max = date(MAXYEAR, 12, 31)
date.resolution = timedelta(days=1)


def _time(h, m, s, us):
    if (
        0 <= h < 24
        and 0 <= m < 60
        and 0 <= s < 60
        and 0 <= us < 1_000_000
    ) or (h == 0 and m == 0 and s == 0 and 0 < us < 86_400_000_000):
        return timedelta(0, s, us, 0, m, h)
    else:
        raise ValueError


def _iso2t(s):
    raise NotImplementedError()
    



def _t2iso(td, timespec, dt, tz):
    s = td._format(_TIME_SPEC.index(timespec))
    if tz is not None:
        s += tz.isoformat()
    return s


class time:
    def __init__(self, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
        self._td = _time(hour, minute, second, microsecond)
        self._tz = tzinfo

    @classmethod
    def fromisoformat(cls, s):
        return cls(*_iso2t(s))

    @property
    def hour(self):
        return self.tuple()[0]

    @property
    def minute(self):
        return self.tuple()[1]

    @property
    def second(self):
        return self.tuple()[2]

    @property
    def microsecond(self):
        return self.tuple()[3]

    @property
    def tzinfo(self):
        return self._tz


    def replace(
        self, hour=None, minute=None, second=None, microsecond=None, tzinfo=True
    ):
        h, m, s, us, tz = self.tuple()
        if hour is None:
            hour = h
        if minute is None:
            minute = m
        if second is None:
            second = s
        if microsecond is None:
            microsecond = us
        if tzinfo is True:
            tzinfo = tz

        return time(hour, minute, second, microsecond, tzinfo, fold=fold)

    def isoformat(self, timespec="auto"):
        return _t2iso(self._td, timespec, None, self._tz)

    def __repr__(self):
        return "datetime.time(microsecond={}, tzinfo={}, fold={})".format(
            self._td._us, repr(self._tz), self._fd
        )

    __str__ = isoformat

    def __bool__(self):
        return True

    def __eq__(self, other):
        if (self._tz == None) ^ (other._tz == None):
            return False
        return self._sub(other) == 0

    def __le__(self, other):
        return self._sub(other) <= 0

    def __lt__(self, other):
        return self._sub(other) < 0

    def __ge__(self, other):
        return self._sub(other) >= 0

    def __gt__(self, other):
        return self._sub(other) > 0

    def _sub(self, other):
        tz1 = self._tz
        if (tz1 is None) ^ (other._tz is None):
            raise TypeError
        us1 = self._td._us
        us2 = other._td._us
        if tz1 is not None:
            os1 = self.utcoffset()._us
            os2 = other.utcoffset()._us
            if os1 != os2:
                us1 -= os1
                us2 -= os2
        return us1 - us2

    def __hash__(self):
        if not hasattr(self, "_hash"):
            # fold doesn't make any difference
            self._hash = hash((self._td, self._tz))
        return self._hash

    def utcoffset(self):
        return None if self._tz is None else self._tz.utcoffset(None)

    def dst(self):
        return None if self._tz is None else self._tz.dst(None)

    def tzname(self):
        return None if self._tz is None else self._tz.tzname(None)

    def tuple(self):
        d, h, m, s, us = self._td.tuple()
        return h, m, s, us, self._tz


time.min = time(0)
time.max = time(23, 59, 59, 999_999)
time.resolution = timedelta.resolution


class datetime:
    def __init__(
        self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    ):
        self._d = _date(year, month, day)
        self._t = _time(hour, minute, second, microsecond)
        self._tz = tzinfo or timezone.get_default()

    @classmethod
    def fromtimestamp(cls, ts, tz=None):
        if tz is None:
            tz = timezone.get_default()
        if isinstance(ts, float):
            ts, us = divmod(round(ts * 1_000_000), 1_000_000)
        else:
            us = 0
        if tz is None:
            raise NotImplementedError
        else:
            dt = cls(*_tmod.gmtime(ts)[:6], microsecond=us, tzinfo=tz)
            dt = tz.fromutc(dt)
        return dt

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            tz = timezone.get_default()        
        return cls.fromtimestamp(_tmod.time(), tz)


    def toordinal(self):
        return self._d

    def isoformat(self, sep="T", timespec="auto"):
        return _d2iso(self._d) + sep + _t2iso(self._t, timespec, self, self._tz)

    def __repr__(self):
        Y, M, D, h, m, s, us, tz = self.tuple()
        tz = repr(tz)
        return "datetime.datetime({}, {}, {}, {}, {}, {}, {}, {})".format(
            Y, M, D, h, m, s, us, tz
        )

    def __str__(self):
        return self.isoformat(" ")

    def tuple(self):
        d = _o2ymd(self._d)
        t = self._t.tuple()[1:]
        return d + t + (self._tz.utcoffset_seconds())
    
    def __add__(self, other):
        us = self._t._us + other._us
        d, us = divmod(us, 86_400_000_000)
        d += self._d
        return datetime(0, 0, d, 0, 0, 0, us, self._tz)    


