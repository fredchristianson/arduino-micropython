      
import urequests
import ntptime
import _thread
from fc import datetime
import logging
import time
log = logging.getLogger("fc.time")



def update_timezone():
    retries = 5
    while retries > 0:
        try:
            resp = urequests.get('http://worldtimeapi.org/api/ip') 
            if resp.status_code == 200:
                wtime = resp.json()
                log.debug(f"{wtime}")
                is_dst = wtime['dst']
                dst_offset = 60 if is_dst else 0
                gmt_offset = datetime.parse_tz_offset_minutes(wtime['utc_offset'])
                offset = dst_offset + gmt_offset
                log.info(f"gmt offset {gmt_offset}  dstoffset {dst_offset}.  total offset {offset}")
            else:
                log.error(f"failed to get http://worldtimeapi.org {resp}")
            return 
        except Exception as ex:
            retries = retries - 1
            if retries <= 0:
                log.exception(f"update time failed.  done retrying",exc_info=ex)   
                return
            log.exception(f"update time failed.  will retry {retries} more times",exc_info=ex)   

            time.sleep(2)
            
def update_time():
    try:
        update_timezone()
        ntptime.settime()
        now = datetime.now() 
        log.info(f"Time is configured {now}")
    except Exception as ex:
        log.exception("Failed to update network time",exc_info=ex)
        

        

def update():
    _thread.start_new_thread(update_time,())