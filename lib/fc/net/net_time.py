      
import urequests
import ntptime
from datetime import datetime,timezone,timedelta
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
        
        
        

class NetTime:
    is_dst = None
    dst_offset = None
    gmt_offset = None
    tz = None
    
    @classmethod
    async def update(cls):
        log.info("update time")
        if cls.tz is None:
           await cls.update_timezone()
        ntptime.settime()
        now = datetime.now()
        log.info(f"time set to {now}")
        
        
        
            
    @classmethod 
    async def update_timezone(cls):
        resp = urequests.get('http://worldtimeapi.org/api/ip') 
        if resp.status_code == 200:
            wtime = resp.json()
            cls.is_dst = wtime['dst']
            cls.dst_offset = timedelta(hours=1) if cls.is_dst else timedelta(hours=0)
            cls.gmt_offset = get_timedelta(wtime['utc_offset'])
            log.info(f"Timezone:  dst={cls.is_dst}  dst_offset={cls.dst_offset.isoformat()}  gmt_offset={cls.gmt_offset.isoformat()}")
            tz = timezone(cls.gmt_offset,cls.is_dst,wtime['timezone'],wtime['abbreviation'],cls.dst_offset)
            timezone.set_default(tz)
            cls.tz = tz
        else:
            log.error("failed to get http://worldtimeapi.org")