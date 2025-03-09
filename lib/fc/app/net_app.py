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
   
    def get_http_server(self): 
        return self._http
        
    async def _setup(self):
        log.debug("_setup")
        
        with loader("fc.app.net_app_impl") as impl:
            await impl.setup(self)

        self.is_set_up = True
        log.info("NetApp setup complete")       
         
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
        
 