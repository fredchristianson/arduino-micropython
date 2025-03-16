      
import urequests
import ntptime
import _thread
from fc import datetime
import logging
import time
log = logging.getLogger("fc.net.time")



def update_timezone():
    retries = 10
    while retries > 0:
        try:
            resp = urequests.get('http://worldtimeapi.org/api/ip') 
            if resp.status_code == 200:
                wtime = resp.json()
                log.debug(f"{wtime}")
                gmt_offset = datetime.parse_tz_offset_minutes(wtime['utc_offset'])
                log.info(f"gmt offset {gmt_offset} ")
            else:
                log.error(f"failed to get http://worldtimeapi.org {resp}")
            return 
        except Exception as ex:
            retries = retries - 1
            if retries <= 0:
                log.exception(f"update time failed.  done retrying",exc_info=ex)   
                return
            log.info(f"update time failed.  will retry {retries} more times")   
            time.sleep(4)
            
def update_time():
    try:
        update_timezone()
        ntptime.settime()
        now = datetime.now() 
        log.info(f"Time is configured {now}")
    except Exception as ex:
        log.exception("Failed to update network time",exc_info=ex)
        

        

async def update():
    _thread.start_new_thread(update_time,())