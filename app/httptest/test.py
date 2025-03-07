import sys
import gc
import machine
import network
import time
from network import WLAN,STA_IF,AP_IF


mf = gc.mem_free
mods = sys.modules

print(sys.modules)
gc.collect()
print(gc.mem_free())

def rmod(mod):
    for m in sys.modules:
        if m.startswith(mod):
            del sys.modules[m]
            
def log(msg=''):
    gc.collect()
    print(f"{msg}  mem={mf()}")

            
def wifi():
    log("get station")
    station = WLAN(STA_IF)
    log("activate")
    station.active(True)
    log("collect")
    station.connect('5336iot','iotcorelli')
    log("wait for connected")
    while not station.isconnected():
        time.sleep(2)
        log("retry connection")
       
def run(): 
    log('import HttpTestApp')
    from http_test import HttpTestApp
    log('create HttpTestApp')
    app = HttpTestApp()
 
    import asyncio
    log('run HttpTestApp')
    
    asyncio.run(app.run())