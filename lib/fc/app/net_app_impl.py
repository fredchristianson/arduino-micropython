import logging
import asyncio
from fc.modload import loader

import gc

log = logging.getLogger("fc.app.netapp_impl")

async def check_wifi(app,check_func):
    while True:
        log.debug("check wifi")
        check_func()
        await asyncio.sleep(5)
    
async def setup_wifi(app):
    log.debug("setup_wifi()")
    with loader('fc.net.wifi') as wifimod:
        log.debug("wifi_loaded")
        while not await wifimod.connect(15,delay_seconds=4):
            await wifimod.web_configure()
        
        
        asyncio.create_task(check_wifi(app,wifimod.wifi_check_connection))
    log.debug("wifi setup done")
    
async def setup_system_routes(app):
    log.debug("setup system routes")
    with loader('fc.app.system_routes') as sysroutes:
        app._sys_router = await sysroutes.create_routes()    

async def _check_network_task(app):
    from fc.net.wifi import wifi_check_connection, wifi_web_configure, wifi_check_connection
    from fc.net.mqtt import mqtt_check_connection 
    while True:
        await asyncio.sleep_ms(50)
        await wifi_check_connection()
        await mqtt_check_connection()


async def setup(app):
    try:
        await setup_wifi(app)
        await setup_system_routes(app)

        log.debug('start time update')
        
        with loader('fc.net.nettime') as net:
            await net.update()
        log.debug('time update running')
        log.debug("setup done")
    except Exception as ex:
        log.exception("Setup failed", exc_info=ex)
    
def notimp(app):
    app.get_http_port()
    if port is not None:       
        log.info(f"setup HTTP server on port {port}")
        from fc.net.http import HttpServer, HttpRouter
        self._http = HttpServer(port)
        self._sys_router = SystemRoutes()
        self._http.add_router(self._sys_router,"/sys")

        self._app_router = HttpRouter()
        self._http.add_router(self._app_router)
        self.setup_routes(self._app_router)
        await self._http.start()
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
        

    
def get_http_port(self):
    """derived class can override to change the port

    Returns:
        int|None:  the port number or None if an http server should not be created
    """
    return 80

def setup_routes(self,router):
    """derived classes can setup routes in the default router.
    if needed, they can use get_http_server() to get the server and add additional routers"""
    pass
    
