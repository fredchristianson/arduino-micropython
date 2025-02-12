# datetime.py
from .timedelta import timedelta

class tzinfo:
    # abstract class
    def tzname(self, dt):
        raise NotImplementedError

    def utcoffset(self, dt):
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
        return self.utcoffset(dt)._format(0x12)


class timezone(tzinfo):
    utc = None
    default = None
    
    @classmethod
    def set_default(cls,tz):
        cls.default = tz
        
    @classmethod
    def get_default(cls):
        return cls.default or cls.utc
    
    def __init__(self, offset, name=None):
        if not (abs(offset._us) < 86_400_000_000):
            raise ValueError
        self._offset = offset
        self._name = name
        if timezone.default == None:
            timezone.default = self
            

    def __repr__(self):
        return "datetime.timezone({}, {})".format(repr(self._offset), repr(self._name))

    def __eq__(self, other):
        if isinstance(other, timezone):
            return self._offset == other._offset
        return NotImplemented

    def __str__(self):
        return self.tzname(None)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._offset, self._name))
        return self._hash

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return None

    def tzname(self, dt):
        if self._name:
            return self._name
        return self._offset._format(0x22)

    def fromutc(self, dt):
        return dt + self._offset


timezone.utc = timezone(timedelta(0))
