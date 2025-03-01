      
import urequests
import ntptime
import _thread
from fc.datetime import datetime,timedelta
import logging
import time
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
    retries = 5
    while retries > 0:
        try:
            resp = urequests.get('http://worldtimeapi.org/api/ip') 
            if resp.status_code == 200:
                wtime = resp.json()
                cls.is_dst = wtime['dst']
                cls.dst_offset = timedelta(hours=1) if cls.is_dst else timedelta(hours=0)
                cls.gmt_offset = get_timedelta(wtime['utc_offset'])
                #tz = timezone(cls.gmt_offset,cls.is_dst,wtime['timezone'],wtime['abbreviation'],cls.dst_offset)
                offset = cls.dst_offset + cls.gmt_offset
                log.info(f"gmt offset {cls.gmt_offset}  dstoffset {cls.dst_offset}.  total offset {offset}")
                datetime.set_tzoffset_minutes(offset)
                log.info(f"got datetime offset {offset}")
            else:
                log.error("failed to get http://worldtimeapi.org")
            return 
        except Exception as ex:
            retries = retries - 1
            if retries <= 0:
                log.exception(f"update time failed.  done retrying",exc_info=ex)   
                return
            log.exception(f"update time failed.  will retry {retries} more times",exc_info=ex)   

            time.sleep(2)
            
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