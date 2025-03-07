"""datetime.py
This module only works on time ranges supported by the time module.  For esp32 the epoch is 2000/1/1.
It may be different on different devices.

"""

import time as tmod

tuple_zero_time = tmod.gmtime(0)
seconds_zero_time = tmod.mktime(tuple_zero_time)


class timevalue:
    
    @classmethod
    def create(cls,seconds_since_epoch=0):
        return cls(seconds_since_epoch=seconds_since_epoch)
    
    @classmethod
    def now(cls,gmt_offset = None):
        seconds = tmod.time()
        if gmt_offset:
            seconds = gmt_offset.seconds_since_epoch() + seconds
        return cls(seconds_since_epoch = seconds)
    
    def __init__(self, year=None,month=None,day=None,hour=None,minute=None,second=None,seconds_since_epoch=None,now=False,gmt_offset=None):
        if now:
            #print("get now()")
            seconds_since_epoch = tmod.time()
        if seconds_since_epoch is not None:
            #print(f"seconds_since_epoch {seconds_since_epoch}")
            self._tuple = tmod.gmtime(seconds_since_epoch + (gmt_offset.seconds_since_epoch() if gmt_offset else 0))
            self._seconds_since_epoch = seconds_since_epoch
        else:
            #print(f"ymdhms {year},{month},{day},{hour},{minute},{second}")
            
            self._tuple = (year or 0,month or 0, day or 0,hour or 0,minute or 0, second or 0,-1,-1,-1)
            #print(f"tuple {self._tuple}")
            self._seconds_since_epoch = tmod.mktime(self._tuple) 
            if gmt_offset:
                self._seconds_since_epoch += gmt_offset.seconds_since_epoch()
                self._tuple = tmod.gmtime(self._seconds_since_epoch)
            
    
    def year(self):
        return self._tuple[0]
    
    def month(self):
        return self._tuple[1]
    
    def day(self):
        return self._tuple[2]
    
    def hour(self):
        return self._tuple[3]
    
    def minute(self):
        return self._tuple[4]
    
    def second(self):
        return self._tuple[5]
    
    def __add__(self,other):
        seconds = self._seconds_since_epoch
        if isinstance(other,timevalue):
            #print(f"__add__ {self._seconds_since_epoch} + {other._seconds_since_epoch}")
            seconds = self._seconds_since_epoch + other._seconds_since_epoch
        elif type(other) == int:
            #print(f"__add__ {self._seconds_since_epoch} + {other}")
            
            seconds = self._seconds_since_epoch + other
        sum = self.__class__.create(seconds_since_epoch = seconds)
        return sum
            
    def seconds_since_epoch(self):
        return self._seconds_since_epoch

    def isoformat(self, sep="T"):
        return f"%04d-%02d-%02d%s%02d:%02d:%02d" % (self.year(),self.month(),self.day(),sep,self.hour(),self.minute(),self.second())
   
    def __str__(self):
        return self.isoformat()
    
    def __repr__(self):
        return f"{self.__class__.__name__}: {self.isoformat()}"
            

class timedelta(timevalue):
    """The number of seconds is kept as the seconds since epoch. """
    
    @classmethod
    def create(cls,seconds_since_epoch=0):
        return cls(seconds=seconds_since_epoch)
        
    @classmethod
    def parse(cls,val,name=None):
        """handle value list "06:00"  or "-5:30" or something like that.  '-5' will be -5 hours and '5' is 5 hours"""
        
        sign = 1
        if val[0] == '-':
            sign = -1 
            val = val[1:]
        elif val[0] == '+':
            sign = 1
            val = val[1:]   
        if ':' in val:
            hm = val.split(':')
            val = (int(hm[0])*60+int(hm[1])) * sign
        else:
            val = int(val)*60*sign    
        return cls(minutes=val,name=name)   
         
    def __init__(
        self=None, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0,name=None
    ):
        seconds = (((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds
        super().__init__(seconds_since_epoch=seconds)
        self.name = name if name is not None else f"%02d:%02d" % (self.hour(),abs(self.minute()))

    def total_seconds(self):
        return self._seconds_since_epoch


class date(timevalue):
    
    
    @classmethod
    def create(cls,seconds_since_epoch=0):
        tuple = tmod.gmtime(seconds_since_epoch)
        return cls(tuple[0],tuple[1],tuple[2])
        
    def __init__(self, year, month, day):
       super().__init__(year=year,month=month,day=day)

    @classmethod
    def today(cls):
        return cls(*_tmod.localtime()[:3])


    @classmethod
    def fromisoformat(cls, s):   
        return cls(s[0:4],s[5:7],s[8:10])

    def isoformat(self):
        return "%04d-%02d-%02d" % (self.year(),self.month(),self.day())

    def __repr__(self):
        return f"date: {self.isoformat()}"

    __str__ = isoformat

    def __hash__(self):
        return hash((self.year(),self.month(),self.day()))

class time(timevalue):
    
    @classmethod
    def create(cls,seconds_since_epoch=0):
        tuple = tmod.gmtime(seconds_since_epoch)
        return cls(tuple[3],tuple[4],tuple[5])
            
    
    def __init__(self, hour=0, minute=0, second=0):
        super().__init__(hour=hour,minute=minute,second=second)

    @classmethod
    def fromisoformat(cls, iso):
        t = iso[11:]
        h = int(t[0:2])
        m = int(t[3:5])
        s = int(t[6:8])
        r = t[9:] # rest for microsecond and tz offset

        return cls(h,m,s)

    def isoformat(self):
        return "%02d:%02d:%02d" % (self.hour(),self.minute(),self.second())

    def __repr__(self):
        return f"time: {self.isoformat()}"

    __str__ = isoformat

    def __bool__(self):
        return True

    def __hash__(self):
        return hash((self.hour(),self.minute(),self.second()))

timedelta_zero = timedelta(0,name="GMT")

class datetime(timevalue):
    default_tzoffset = timedelta_zero
    
    @classmethod
    def create(cls,seconds_since_epoch=0):
        tuple = tmod.gmtime(seconds_since_epoch)
        return cls(tuple[0],tuple[1],tuple[2],tuple[3],tuple[4],tuple[5],timedelta_zero)
            
    @classmethod
    def set_tzoffset_minutes(cls,minutes,name=None):
        if isinstance(minutes,timedelta):
            cls.default_tzoffset = minutes
        elif type(minutes) == int:
            cls.default_tzoffset = timedelta(minutes=minutes,name=name)
        elif type(minutes) == str:
            """handle value list "06:00"  or "-5:30" or something like that.  '-5' will be -5 hours and '5' is 5 hours"""
            cls.default_tzoffset = timedelta.parse(minutes)
        else:
            cls.default_tzoffset = timedelta_zero
        
    def __init__(
        self, year=0, month=0, day=0, hour=0, minute=0, second=0,tzoffset_minutes = None,now = False
    ):
        tz = tzoffset_minutes or datetime.default_tzoffset
        super().__init__(year,month,day,hour,minute,second,None,gmt_offset=tz,now=now)

        self._tzoffset_minutes = tz

    @classmethod
    def now(cls,tz=None):
        dt = datetime(now=True,tzoffset_minutes=tz or datetime.default_tzoffset)
        return dt


    def isoformat(self, sep="T"):
        tz = self._tzoffset_minutes.total_seconds()
        tzoffset = f"{'+' if tz>=0 else '-'}{abs(tz)//3600:02d}:{abs(tz)%60:02d}"
        return f"%04d-%02d-%02d%s%02d:%02d:%02d%s" % (self.year(),self.month(),self.day(),sep,self.hour(),self.minute(),self.second(),tzoffset)


    def __repr__(self):
        return f"datetime: {self.isoformat()}"

    def __str__(self):
        return self.isoformat(" ")
    
    def format(self,form="%Y/%m/%d %H:%M:%S"):
        t =self._tuple
        t2 = [('00'+str(v))[-2:] for v in t]
        f = form.replace('%Y',str(t[0]))\
                    .replace('%y',str(t[0]%1000))\
                    .replace('%d',t2[2])\
                    .replace('%m',t2[1])\
                    .replace('%H',t2[3])\
                    .replace('%M',t2[4])\
                    .replace('%S',t2[5])
        return f


