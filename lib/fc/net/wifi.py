import ubinascii
import socket
import json
import logging
import network
import ure
from network import WLAN
import asyncio

log = logging.getLogger('fc.net.wifi')

class Wifi:
    def __init__(self):
        self.connected = False
        self.station = None
        self.reconnect_task = None
        self.ssid = None
        self.password = None
        
    def get_ip_addr(self): 
        config = self.station.ifconfig()
        try:
            return config[0]
        except Exception as ex:
            log.error("Wifi ifconfig failed or is not connected.")
            return None
    
    async def _check_connection(self):
        while True:
            await asyncio.sleep(1)
            #log.debug("check wifi connection")
            if not self.station.isconnected():
                log.error("wifi connection lost.  reconnecting")
                await self.connect()
                
    def load_config(self,filename='data/fc_wifi.json'):
        try:
            with open('data/fc_wifi.json') as file:
                config = json.load(file)
                self.ssid = config['ssid'] if 'ssid' in config else None
                self.password = config['password']
                log.debug(f"wifi ssid={self.ssid} password={self.password}")      
        except Exception as ex:
            log.error(f"cannot read wifi config {filename}")    
            self.ssid = None
            self.password = None
        return self.ssid is not None and type(self.ssid) == str and len(self.ssid)>0
                      
    async def connect(self,ssid=None, password=None):
        self.station = self.station if self.station is not None else WLAN(network.STA_IF)
        self.station.active(True)
        if ssid is None and self.ssid is None:
            self.load_config('data/fc_wifi.json')
            
        while self.station is None or not self.station.isconnected():
            if self.ssid is None:
                await self.web_config()
            else: 
                self.station.connect(ssid,password)
                self.ssid = ssid
                self.password = password
                retry = 0
                while not self.station.isconnected() and retry < 30:
                    log.info("wait for Wifi connection")
                    asyncio.sleep_ms(500)
                if not self.station.isconnected():
                    self.station.active(False)
                    await self.web_config()
        log.info(f"Wifi connected to {ssid}  {self.station.ifconfig()}")
        self.reconnect_task = asyncio.create_task(self._check_connection())
        
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