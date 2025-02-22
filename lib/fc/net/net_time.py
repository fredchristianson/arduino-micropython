      
import urequests
import ntptime
import _thread
from fc.datetime import datetime,timedelta
import logging
log = logging.getLogger("fc.time")

def get_timedelta(offset):
    if type(offset) == int:
        return timedelta(minutes = offset)
    elif type(offset) == float:
        hours = int(offset)
        minutes = int((offset-hours)*100)
        return timedelta(hours =hours,minutes = minutes)
    elif type(offset)  == str:
        hm = offset.split(':')
        hours = int(hm[0])
        sign = 1 if hours>=0 else -1
        minutes = sign * int(hm[1]) if len(hm)>1 else 0
        return timedelta(hours =hours,minutes = minutes)



def update_timezone(cls):
    resp = urequests.get('http://worldtimeapi.org/api/ip') 
    if resp.status_code == 200:
        wtime = resp.json()
        cls.is_dst = wtime['dst']
        cls.dst_offset = timedelta(hours=1) if cls.is_dst else timedelta(hours=0)
        cls.gmt_offset = get_timedelta(wtime['utc_offset'])
        tz = timezone(cls.gmt_offset,cls.is_dst,wtime['timezone'],wtime['abbreviation'],cls.dst_offset)
        timezone.set_default(tz)
        log.info(f"got timezone {tz} {tz.isoformat()}")
        cls.tz = tz
    else:
        log.error("failed to get http://worldtimeapi.org")
    
            
def update_time(cls):
    try:
        if cls.tz is None:
            update_timezone(cls)
        ntptime.settime()
        now = datetime.now() 
        log.info(f"Time is configured {now.format()}")
    except Exception as ex:
        log.exception("Failed to update network time",exc_info=ex)
        

        

class NetTime:
    is_dst = None
    dst_offset = None
    gmt_offset = None
    tz = None
    
    @classmethod
    async def update(cls):
        args = (cls,)
        _thread.start_new_thread(update_time,args)