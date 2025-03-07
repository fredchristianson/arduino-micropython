
import json
import logging
import asyncio
import gc

log = logging.getLogger('fc.net.wifi')


def get_station():
    from network import WLAN,STA_IF
    return  WLAN(STA_IF)


def get_ap():
    from network import WLAN,AP_IF
    return  WLAN(AP_IF)

def get_station_ip():
    return get_ip_addr(get_station())

def get_ip_addr(wlan): 
    config = wlan.ifconfig()
    try:
        return config[0]
    except Exception as ex:
        log.error("Wifi ifconfig failed or is not connected.")
        return None  
        
def scan_networks():
    station = get_station()
    station.active(True)
    nets = station.scan()
    return sorted(set((n[0].decode('utf-8') for n in nets if len(n[0].decode('utf-8')) > 0)))     
    
def load_config(filename='/data/fc_wifi.json'):
    ssid = None
    password = None
    if not filename:
        log.warning("load_config needs a filename")
    try:
        with open('data/fc_wifi.json') as file:
            config = json.load(file)
            ssid = config['ssid'].strip() if 'ssid' in config else None
            password = config['password'].strip()
            log.debug(f"wifi ssid={ssid} password={password}")      
    except Exception as ex:
        log.error(f"cannot read wifi config {filename}")    
        ssid = None
        password = None
    return ssid,password

def save_config(ssid,password,filename='/data/fc_wifi.json'):
    if not filename:
        log.warning("save_config needs a filename")
        return
    try:
        with open(filename,'w') as file:
            data = {
                "ssid": ssid,
                "password": password
            }
            log.debug(f"data: {data}")
            jdata = json.dumps(data)
            log.debug(f"json: {jdata}")
            json.dump(data,file)

    except Exception as ex:
        log.error(f"cannot write wifi config {filename}")    
        log.exception("exception",exc_info=ex)
        ssid = None
        password = None      
        
async def connect(retries=5, delay_seconds=4):
    station = get_station()
    log.debug(f"activate wifi station {station}")
    station.active(True)
    
    
    ssid,password = load_config()
        
    log.info(f"Connecting wifi.  ssid={ssid} password={password} connection={station.isconnected()}")
    if not station.isconnected() and ssid:
        try:
            log.info(f"connect({ssid},{password})  retries={retries}   delay={delay_seconds}")
            station.connect(ssid,password)
            retry = 0
            while not station.isconnected() and (retry < retries):
                log.info("wait for Wifi connection")
                await asyncio.sleep_ms(delay_seconds*1000)
                log.info(f"waited {delay_seconds} seconds")
                retry += 1
        except Exception as ex:
            station.active(False)
            log.exception("Cannot connect to wifi",exc_info=ex)
            return False
    log.info(f"ip addr: {get_ip_addr(station)}.  connected={station.isconnected()}")
    if not station.isconnected():
        station.active(False)
        return  False    
    else:
        return True       

    
async def wifi_check_connection():
    station = get_station()
    
    while not station.isconnected():
        log.info("Wifi not connected")
        ssid,password = load_config()
        station.connect(ssid,password)
        for i in range(10):
            if station.isconnected():
                log.info("Wifi connected")
                return
            await asyncio.sleep(10)
        await asyncio.sleep(5)

_config_message = "Select SSID"
_stop_event = asyncio.Event()


async def get_form(req,resp):
    global _config_message
    log.debug("get_form")
    nets = scan_networks()
    radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in nets])
    pw = "<label>Password: <input type='text' name='password'></label> "
    msg = f"<div>{_config_message}</div>" if _config_message is not None else ""
    page = f"<html><body>{msg}<form method='POST'><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form></html></body>"
    log.debug(f"Page: {page[0:100]}...")
    return page
    
async def post_form(req,resp):
    global ssid, password, _stop_event
    log.debug("POST form")
    # nets = self.nets
    # radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in nets])
    # pw = "<label>Password: <input type='text' name='password'></label> "
    # page = f"<div>SSID: {req.get('ssid')},  Password: {req.get('password')}<form><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form>"
    ssid = req.get('ssid')
    password = req.get('password')
    _stop_event.set()
    return f"selected: {ssid}"
    

async def web_configure(     ):
    station = get_station()
    ap = get_ap()
    ssid,password = load_config()
    log.info("Wifi Web Configuration")

    try:
        from fc.net.http import HttpServer, HttpRouter
        log.info("Wifi web config running")
        station.active(True)
        ap.active(True)
        essid = f"config-{app_name}-{get_ip_addr(ap)}"
        log.info(f"essid {essid}")
        ap.config(essid=essid,password='',authmode=AUTH_OPEN)
        log.info("create HTTP server")
        server = HttpServer(port=8080,host='0.0.0.0')
        router = HttpRouter([
                                                    ('GET','/',get_form),
                                                    ('POST','/',post_form)
                                                    ])

        server.add_router(router)
        log.debug("starting server")
        await server.start()
        log.info("wait for close")
        await _stop_event.wait()
        log.info(f"got ssid {ssid},  password {password}")
        await server.stop()
        log.info(f"got ssid {ssid.strip()},  password {password.strip()}")
        save_config(ssid.strip(),password.strip())
        return True
    except Exception as ex:
        log.error("cannot create HTTP server for Wifi config")
        log.exception("Exception",exc_info = ex)
        log.info("WebConfig done without SSID/password")
        return False
    finally:
        ap.active(False)


