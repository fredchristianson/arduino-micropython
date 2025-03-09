import logging
import asyncio
from lib.fc.modload.modload import loader

import gc

log = logging.getLogger("fc.app.netapp_impl")

async def check_wifi(app,check_func):
    while True:
        log.debug("check wifi")
        check_func()
        await asyncio.sleep(5)
    
async def setup_wifi(app):
    log.debug("setup_wifi()")
    ip_addr = '-:-:-:-'
    with loader('fc.net.wifi') as wifimod:
        log.debug("wifi_loaded")
        while not await wifimod.connect(15,delay_seconds=4):
            await wifimod.web_configure()
        ip_addr = wifimod.get_station_ip()
        
        asyncio.create_task(check_wifi(app,wifimod.wifi_check_connection))
    log.debug(f"wifi setup done {ip_addr}")
    return ip_addr
   

async def _check_network_task(app):
    from fc.net.wifi import wifi_check_connection, wifi_web_configure, wifi_check_connection
    from fc.net.mqtt import mqtt_check_connection 
    while True:
        await asyncio.sleep_ms(50)
        await wifi_check_connection()
        await mqtt_check_connection()

async def setup_http_server(app):
    port = app.get_http_port()
    if port > 0:
        with loader('fc.net.http.server') as http:
            log.debug("setup http server")
            app._http_server = await http.start_server(port)

            log.debug("setup system routes")
            with loader('fc.app.system_routes') as sysroutes:
                app._sys_router = await sysroutes.create_routes() 
                http.add_router(app._http_server,"/sys", app._sys_router)
            
            with loader('fc.net.http.route') as routes:
                app._app_router = routes.create_router('app')
                http.add_router(app._http_server,"/", app._sys_router)
                app.setup_routes(app._app_router)

async def setup(app):
    try:
        await setup_wifi(app)
       
        with loader('fc.net.nettime') as nettime:
            await nettime.update()
        log.debug('time update running')
        
        await setup_http_server(app)
        log.debug("setup done")
    except Exception as ex:
        log.exception("Setup failed", exc_info=ex)
    
def notimp(app):
    asyncio.create_task(self._check_network())
    asyncio.create_task(self._update_time())
    self.is_set_up = True
    
async def _update_time(self):
    from fc.net import NetTime        
    while True:
        log.debug("update time")
        await NetTime.update()
        log.debug("update time started. sleep for an hour")
        await asyncio.sleep(60*60)  #update every hour
        log.debug("update_time again")
        

    

    
