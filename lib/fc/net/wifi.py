
import json
import logging
from network import WLAN,STA_IF,AP_IF,AUTH_OPEN
import asyncio
import gc

log = logging.getLogger('fc.net.wifi')

station:WLAN = WLAN(STA_IF)
ap:WLAN = WLAN(AP_IF)
station.active(True)
_ssid=None
_password = None


def get_ip_addr(wlan): 
    config = wlan.ifconfig()
    try:
        return config[0]
    except Exception as ex:
        log.error("Wifi ifconfig failed or is not connected.")
        return None  
        
def scan_networks():
    station.active(True)
    nets = station.scan()
    return sorted(set((n[0].decode('utf-8') for n in nets if len(n[0].decode('utf-8')) > 0)))     
    
def load_config(filename='/data/fc_wifi.json'):
    global _ssid, _password    
    if not filename:
        log.warning("load_config needs a filename")
    try:
        with open('data/fc_wifi.json') as file:
            config = json.load(file)
            _ssid = config['ssid'].strip() if 'ssid' in config else None
            _password = config['password'].strip()
            log.debug(f"wifi ssid={_ssid} password={_password}")      
    except Exception as ex:
        log.error(f"cannot read wifi config {filename}")    
        _ssid = None
        _password = None
    return _ssid

def save_config(filename='/data/fc_wifi.json'):
    global _ssid, _password
    if not filename:
        log.warning("save_config needs a filename")
        return
    try:
        with open(filename,'w') as file:
            data = {
                "ssid": _ssid,
                "password": _password
            }
            log.debug(f"data: {data}")
            jdata = json.dumps(data)
            log.debug(f"json: {jdata}")
            json.dump(data,file)

    except Exception as ex:
        log.error(f"cannot write wifi config {filename}")    
        log.exception("exception",exc_info=ex)
        _ssid = None
        _password = None      
        
async def wifi_connect(app_name,retries=5, delay_seconds=2):
    global _ssid, _password,station
    log.debug("activate wifi station")
    station.active(True)
    
    if not _ssid:
        log.debug("load wifi config")
        load_config()
        
    log.info(f"Connecting wifi.  app={app_name} ssid={_ssid} password={_password} connection={station.isconnected()}")
    if not station.isconnected() and _ssid:
        try:
            log.info(f"connect({_ssid},{_password})  retries={retries} type={type(retries)}  delay={delay_seconds}")
            station.connect(_ssid,_password)
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
        return False
    else:
        save_config()
        return True

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
    global _ssid, _password, _stop_event
    log.debug("POST form")
    # nets = self.nets
    # radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in nets])
    # pw = "<label>Password: <input type='text' name='password'></label> "
    # page = f"<div>SSID: {req.get('ssid')},  Password: {req.get('password')}<form><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form>"
    _ssid = req.get('ssid')
    _password = req.get('password')
    _stop_event.set()
    return f"selected: {_ssid}"
    

async def wifi_web_configure(app_name):
    global _ssid, _password, station,ap,message
    log.info("Wifi Web Configuration")

    try:
        from fc.net.http import HttpServer, HttpRouter
        log.info("Wifi web config running")
        station.active(True)
        ap.active(True)
        essid = f"config-{app_name}-{get_ip_addr(ap)}"
        ap.config(essid=essid,password='',authmode=AUTH_OPEN)
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
        log.info(f"got ssid {_ssid},  password {_password}")
        await server.stop()
        log.info(f"got ssid {_ssid.strip()},  password {_password.strip()}")
        return True
    except Exception as ex:
        log.error("cannot create HTTP server for Wifi config")
        log.exception("Exception",exc_info = ex)
        log.info("WebConfig done without SSID/password")
        return False
    finally:
        ap.active(False)


