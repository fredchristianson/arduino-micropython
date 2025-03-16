import logging;
import asyncio
from lib.fc.modload.modload import loader

from .app import App

import gc

log = logging.getLogger("fc.app.netapp")


class NetApp(App):

    def __init__(self, name="<unnamed app>"):
        super().__init__(name)
        log.info(f"NetApp created {name}")
        self._http = None
        self._sys_router = None
        self._app_router = None
        self._devices = []
        self._ip_addr = None
   
    def get_http_server(self): 
        return self._http
        
    async def _setup(self):
        log.debug("_setup")
        
        await self._setup_wifi()
        await self._setup_http_server()
        asyncio.create_task(self._check_network())
        asyncio.create_task(self._update_time())
          
        self.is_set_up = True
        log.info("NetApp setup complete")       
         
    async def _update_time(self):
        while True:
            log.debug("update time")
            with loader('fc.net.nettime') as nettime:
                await nettime.update()
            log.debug("update time started. sleep for an hour")
            await asyncio.sleep(60*60)  #update every hour
            log.debug("update_time again")
         
    async def _check_network(self):
        while True:
            #log.debug("check network")
            with loader('fc.net.wifi') as wifimod:
                #log.debug("wifi_loaded")
                self._ip_addr = wifimod.wifi_check_connection()
            await asyncio.sleep(5) 
                    
    async def _setup_wifi(self):
        log.debug("setup_wifi()")
        ip_addr = '-:-:-:-'
        with loader('fc.net.wifi') as wifimod:
            log.debug("wifi_loaded")
            while not await wifimod.connect(15,delay_seconds=4):
                await wifimod.web_configure()
            self._ip_addr = wifimod.get_station_ip()
        log.debug(f"wifi setup done {self._ip_addr}")

    async def _setup_http_server(self):
        port = self.get_http_port()
        if port > 0:
            with loader('fc.net.http.server') as http:
                log.debug("setup http server")
                self._http_server = await http.start_server(port)

                log.debug("setup system routes")
                with loader('fc.app.system_routes') as sysroutes:
                    self._sys_router = await sysroutes.create_routes() 
                    http.add_router(self._http_server,"/sys", self._sys_router)
                
                with loader('fc.net.http.router') as routes:
                    self._app_router = routes.create_router('app')
                    http.add_router(self._http_server,"/", self._app_router)
                    self.setup_routes(self._app_router)
            
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
        
 