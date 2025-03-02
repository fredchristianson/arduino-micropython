import logging;
import asyncio


from .app import App

import gc

log = logging.getLogger("fc.netapp")


class NetApp(App):

    def __init__(self, name="<unnamed app>"):
        super().__init__(name)
        log.info(f"NetApp created {name}")
        self._http = None
        self._sys_router = None
        self._app_router = None
        self._devices = []
   
    def get_http_server(self): 
        return self._http
        
    async def _setup(self):
        from .system_routes import SystemRoutes
        from fc.net.mqtt import mqtt_check_connection     
        from fc.hw.device import create_devices        
        
        # set up the app
        log.debug("setup app")
        await self._setup_wifi()
        log.debug("wifi setup done")
        log.debug("Time setup running")
        port = self.get_http_port()
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
        self._devices = create_devices(self._config.get("devices",None))
        self.is_set_up = True
        
    async def _update_time(self):
        from fc.net import NetTime        
        while True:
            log.debug("update time")
            await NetTime.update()
            log.debug("update time started. sleep for an hour")
            await asyncio.sleep(60*60)  #update every hour
            log.debug("update_time again")
            
    async def _check_network(self):
        from fc.net.wifi import wifi_connect, wifi_web_configure, wifi_check_connection
        from fc.net.mqtt import mqtt_check_connection 
        while True:
            await asyncio.sleep_ms(50)
            await wifi_check_connection()
            await mqtt_check_connection()
    
    async def _setup_wifi(self):
        from fc.net.wifi import wifi_connect, wifi_web_configure, wifi_check_connection
        log.info("setup wifi")
        gc.collect()
        
        while not await wifi_connect(self.get_name(),15,delay_seconds=4):
            await wifi_web_configure(self.get_name())
        
        
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
        
 