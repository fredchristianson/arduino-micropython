"""datetime.py
This module only works on time ranges supported by the time module.  For esp32 the epoch is 2000/1/1.
It may be different on different devices.

"""

import time as tmod
from fc.modload import loader
from collections import namedtuple

IMPL = 'fc.datetime.impl.datetime'

DateTime = namedtuple('DateTime',['year','month','day','hour','minute','second','tz_offset_minutes'])

default_tz_offset_minutes = None

def parse_tz_offset_minutes(min_str, set_default = True):
    global default_tz_offset_minutes
    print(f"parse tz offset {min_str}")
    minutes = 0
    try:
        with loader(IMPL) as impl:
            minutes = impl.parse_tz_offset_minutes(min_str)
    except Exception as ex:
        print(ex)
        minutes = 0
    if set_default:
        default_tz_offset_minutes = minutes
    print(f"minutes {minutes}")
    return minutes

def datetime(year=0, month=0, day=0, hour=0, minute=0, second=0,tzoffset_minutes = None):  
    global default_tz_offset_minutes
    tz = tzoffset_minutes or default_tz_offset_minutes or 0
    return DateTime(year,month,day,hour,minute,second,tz)

     
def now(tzoffset_minutes = None):  
    global default_tz_offset_minutes
    tz = tzoffset_minutes or default_tz_offset_minutes or 0
    gmt = tmod.gmtime(tmod.time())[0:6] +(tz,)
    return DateTime(*gmt)
        
def fromisoformat(dtstr): 
    dstr = dtstr  
    date = (dstr[0:4],dstr[5:7],dstr[8:10])
    tstr = dtstr[11:]
    tm = (int(tstr[0:2]),int(tstr[3:5]),int(tstr[6:8]))
    sign = 1
    tz_off = 0
    tz=None
    if '-' in tstr:
        tz = tstr.split('-')[-1]
        sign = -1
        print('negative')
    elif '+' in tstr:
        tz=tstr.split('+')[-1]
    if tz:
        hm = tz.split(':')
        print(f'tz {sign} {tz}  {hm}')
        tz_off = int(hm[0])*60 + int(hm[1] if len(hm)>1 else 0)
        tz_off = tz_off*sign
        print(f"offset {tz_off}")
    date = (int(date[0]),int(date[1]),int(date[2]))
    dt = date+tm+(tz_off,)
    return DateTime(*dt)
    
 
def isoformat(dt, sep="T"):
    offset_hour = int(dt.tz_offset_minutes /60)
    offset_min = int(abs(dt.tz_offset_minutes) %60)
    tzstr = "%02d:%02d"%(offset_hour,offset_min)
    vals = dt[0:3]+(sep,)+dt[3:6]+(tzstr,)
    return "%04d-%02d-%02d%s%02d:%02d:%02d%s" % vals
    

    
def format(dt,form="%Y/%m/%d %H:%M:%S"):
    t = dt
    t2 = [('00'+str(v))[-2:] for v in t]
    f = form.replace('%Y',str(t[0]))\
                .replace('%y',str(t[0]%1000))\
                .replace('%d',t2[2])\
                .replace('%m',t2[1])\
                .replace('%H',t2[3])\
                .replace('%M',t2[4])\
                .replace('%S',t2[5])
    return f


