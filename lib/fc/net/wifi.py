from fc.net.http import HttpServer,HttpRouter
import ubinascii
import socket
import json
import logging
import network
import ure
from network import WLAN
import asyncio

log = logging.getLogger('fc.net.wifi')

class WlanBase(WLAN):
    def __init__(self,mode):
        super().__init__(mode)
        
    def get_ip_addr(self): 
        config = self.ifconfig()
        try:
            return config[0]
        except Exception as ex:
            log.error("Wifi ifconfig failed or is not connected.")
            return None  
        
    def scan_networks(self):
        nets = self.scan()
        return sorted(set((n[0].decode('utf-8') for n in nets if len(n[0].decode('utf-8')) > 0)))      
class WlanStation(WlanBase):
    def __init__(self):
        super().__init__(network.STA_IF)
        log.info("WlanStation created")
        
        
class WlanAccessPoint(WlanBase):
    def __init__(self):
        super().__init__(network.AP_IF)
        log.info("WlanAccessPoint created")
        
station = None
ap = None



class WebConfig:
    def __init__(self):
        global station
        global ap
        self.ssid = None
        self.password = None
        self.server = None
        self.stop_event = asyncio.Event()
        if station is None:
            station = WlanStation()
            ap = WlanAccessPoint()
        self.nets = None
        
    async def get_form(self,req,resp):
        log.debug("get_form")
        nets = self.nets
        radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in nets])
        pw = "<label>Password: <input type='text' name='password'></label> "
        page = f"<form method='POST'><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form>"
        log.debug(f"Page: {page}")
        return page
        
    async def post_form(self,req,resp):
        log.debug("POST form")
        # nets = self.nets
        # radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in nets])
        # pw = "<label>Password: <input type='text' name='password'></label> "
        # page = f"<div>SSID: {req.get('ssid')},  Password: {req.get('password')}<form><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form>"
        self.ssid = req.get('ssid')
        self.password = req.get('password')
        self.stop_event.set()
        return f"selected: {self.ssid}"
        
    async def run(self):
        try:
            log.info("Wifi web config running")
            self.nets = station.scan_networks()
            log.debug(f"Nets: {self.nets}")
            ap.active(True)
            
            essid = "config-"+ubinascii.hexlify(ap.config("mac")).decode('utf-8')
            ap.config(essid=essid,password='',authmode=network.AUTH_OPEN)
            server = HttpServer(port=8080,host='0.0.0.0')
            router = HttpRouter([
                                                        ('GET','/',self.get_form),
                                                        ('POST','/',self.post_form)
                                                        ])

            server.add_router(router)
            log.debug("starting server")
            await server.start()
            log.info("wait for close")
            await self.stop_event.wait()
            log.info(f"got ssid {self.ssid},  password {self.password}")
            await server.stop()
            log.info(f"got ssid {self.ssid.strip()},  password {self.password.strip()}")
            return (self.ssid.strip(),self.password.strip())
        except Exception as ex:
            log.error("cannot create HTTP server for Wifi config")
            log.exception("Exception",exc_info = ex)
            log.info("WebConfig done without SSID/password")
            return None,None
        finally:
            ap.active(False)


class Wifi:
    def __init__(self):
        global station
        global ap
        self.connected = False
        self.reconnect_task = None
        self.ssid = None
        self.password = None
        
        if station is None:
            station = WlanStation()
            ap = WlanAccessPoint()
        
    
    async def _check_connection(self):
        while True:
            await asyncio.sleep(1)
            #log.debug("check wifi connection")
            if not station.isconnected():
                log.error("wifi connection lost.  reconnecting")
                await station.connect()
                
    def load_config(self,filename='data/fc_wifi.json'):
        if not filename:
            log.warning("load_config needs a filename")
        try:
            with open('data/fc_wifi.json') as file:
                config = json.load(file)
                self.ssid = config['ssid'].strip() if 'ssid' in config else None
                self.password = config['password'].strip()
                log.debug(f"wifi ssid={self.ssid} password={self.password}")      
        except Exception as ex:
            log.error(f"cannot read wifi config {filename}")    
            self.ssid = None
            self.password = None
        return self.ssid is not None and type(self.ssid) == str and len(self.ssid)>0
    
    def save_config(self,filename='data/fc_wifi.json'):
        if not filename:
            log.warning("save_config needs a filename")
        try:
            with open('data/fc_wifi.json','w') as file:
                json.dump({
                    "ssid": self.ssid,
                    "password": self.password
                },file)
                config = json.load(file)
                self.ssid = config['ssid'].strip() if 'ssid' in config else None
                self.password = config['password'].strip()
                log.debug(f"wifi ssid={self.ssid} password={self.password}")      
        except Exception as ex:
            log.error(f"cannot read wifi config {filename}")    
            self.ssid = None
            self.password = None
        return self.ssid is not None and type(self.ssid) == str and len(self.ssid)>0
                                            
    async def connect(self,ssid=None, password=None, reconfig=False,config_file='data/fc_wifi.json'):
        station.active(True)
        saved = False
        if ssid is None and self.ssid is None:
            self.load_config(config_file)
            saved = True
            
        while reconfig or not station.isconnected():
            try:
                if reconfig or (self.ssid is None or self.ssid==''):
                    wconfig = WebConfig()
                    self.ssid,self.password = await wconfig.run()
                    log.debug(f"got ssid {self.ssid}, password {self.password}")
                    saved = False
                else: 
                    try:
                        station.connect(self.ssid,self.password)
                    except Exception as ex:
                        log.error(f"cannot connect to wifi {self.ssid}")
                        log.exception("Exception",exc_info = ex)
                        self.ssid = None
                        self.password = None
                        saved = False
                    retry = 0
                    while not station.isconnected() and retry < 10 and self.ssid is not None:
                        log.info("wait for Wifi connection")
                        await asyncio.sleep_ms(2000)
                        log.info("waited 2 seconds")
                    if not station.isconnected():
                        log.error("Wifi connection failed.  run webconfig again")
                        reconfig = True
                    else:
                        reconfig = False
            except Exception as ex:
                log.exception("wifi connect failed",exc_info=ex)
                            
        log.info(f"Wifi connected to {self.ssid}.  ip={station.get_ip_addr()}")
        self.save_config(config_file)
        self.reconnect_task = asyncio.create_task(self._check_connection())
    
    
    ################## old code ##################    
    def create_page(self,ssids):
        log.debug(f"ssids: {ssids}")
        radios = ''.join([f"<label style='display:block'><input type='radio' name='ssid' value='{ssid}'/>{ssid}</label>" for ssid in ssids])
        pw = "<label>Password: <input type='text' name='password'></label> "
        page = f"<form><div>{radios}</div><div>{pw}</div><div><input type='submit'/></div></form>"
        return page
    
    async def handle_requests(self,ap):
        server_socket = None
        nets = ap.scan()
        log.debug(f"Nets: {nets}")
        ssids = sorted(set((n[0].decode('utf-8') for n in nets if len(n[0].decode('utf-8')) > 0)))
        html = self.create_page(ssids)
        try:
            addr = socket.getaddrinfo('0.0.0.0',80)[0][-1]
            server_socket = socket.socket()
            server_socket.bind(addr)
            server_socket.listen(1)
            while self.ssid is None:
                client,caddr = server_socket.accept()
                client.settimeout(5)
                req = ""
                try:
                    req += client.recv(1024).decode('utf-8')
                    log.info(f"got req: {req}")
                    match = ure.search("ssid=([^&]*)&password=(.*)", request)
                                    
                    if match is None:
                        send_response(client, "Parameters not found", status_code=400)
                        return False
                    # version 1.9 compatibility
                    try:
                        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
                        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
                    except Exception:
                        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
                        password = match.group(2).replace("%3F", "?").replace("%21", "!")
                    if 'GET' in req:
                        client.sendall("HTTP/1.0 200 OK\r\n")
                        client.sendall("Content-Type: text/html\r\n")
                        client.sendall(f"Content-Length {len(html)}\r\n\r\n")
                        client.sendall(html)
                except Exception as ex:
                    log.exception("failed to handle request",exc_info=ex)
                finally:
                    client.close()                        
        except Exception as ex:
            log.exception("failed to handle request",exc_info=ex)
        finally:
            if server_socket is not None:
                log.debug("close socket")
                server_socket.close()
        
    async def web_config(self):
        ap = None
        try:
            ap = WLAN(network.AP_IF)
            ap.active(True)
            ssid = "config-"+ubinascii.hexlify(ap.config("mac")).decode('utf-8')
            ap.config(essid=ssid,password='',authmode=network.AUTH_OPEN)
            await self.handle_requests(ap)
        except Exception as ex:
            log.error("cannot create HTTP server for Wifi config")
            log.exception("Exception",exc_info = ex)
        finally:
            ap.active(False)
            ap.disconnect()