
        
        
import urequests
from datetime import datetime, timedelta, tzinfo,timezone
import ntptime

import logging
log = logging.getLogger("fc.time")

def get_timedelta(offset):
    if type(offset) == int:
        return timedelta(minutes=offset)
    elif type(offset) == float:
        return timedelta(hours=int(offset),minutes=int(offset*100%60))
    elif type(offset) == str:
        hour_min = [int(v) for v in offset.split(':')]
        hour = hour_min[0]
        min = hour_min[1] if hour >= 0 else -hour_min[1]
        return timedelta(hours=hour,minutes= min)
    else:
        log.error(f"unknown timedelta offset {offset}")
        return timedelta(0)
        
class NetTime:
    is_dst = None
    dst_offset = None
    gmt_offset = None
    tz = None
    
    @classmethod
    async def update(cls):
        log.info("update time")
        if timezone is None:
           await cls.update_timezone()
        ntptime.settime()
        now = datetime.now()
        log.info(f"time set to {now}")
        
        
        
            
    @classmethod 
    async def update_timezone(cls):
        resp = urequests.get('http://worldtimeapi.org/api/ip') 
        if resp.status_code == 200:
            log.info(f"worldtime: {resp.json()}")
            wtime = resp.json()
            cls.is_dst = wtime['dst']
            cls.dst_offset = timedelta(hours=1) if cls.is_dst else timedelta(days=0)
            cls.gmt_offset = get_timedelta(wtime['utc_offset'])
            log.info(f"Timezone:  dst={cls.is_dst}  dst_offset={cls.dst_offset.isoformat()}  gmt_offset={cls.gmt_offset().iso_format()}")
            tz = timezone(cls.dst_offset+cls.gmt_offset,wtime['timezone'])
            timezone.set_default(tz)
            cls.tz = tz
        else:
            log.error("failed to get http://worldtimeapi.org")