import logging;
import asyncio
from .app import App




log = logging.getLogger("fc.netapp")


class NetApp(App):

    def __init__(self, name="<unnamed app>"):
        super().__init__(name)
        log.info(f"NetApp created {name}")
        self._wifi = None
        self._http = None
        self._sys_router = None
        self._app_router = None
   
    def get_wifi(self): 
        return self._wifi
           
    def get_http_server(self): 
        return self._http
        
    async def _setup(self):
        from fc.net import NetTime        
        # set up the app
        log.debug("setup app")
        await self._setup_wifi()
        log.debug("wifi setup done")
        await NetTime.update()
        log.debug("Time setup running")
        port = self.get_http_port()
        if port is not None:
            log.info(f"setup HTTP server on port {port}")
            from fc.net.http import HttpServer, HttpRouter, HttpRoute, Html, Json
            self._http = HttpServer(port)
            self._sys_router = HttpRouter()
            self._sys_router.GET("/sys/status",self.status_page)
            self._sys_router.GET("/sys/:name",self.other_page)
            self._app_router = HttpRouter()
            self.setup_routes(self._app_router)
            await self._http.start()
        self.is_set_up = True
    
    async def _setup_wifi(self):
        from fc.net import Wifi
        self._wifi =  Wifi()
        await self._wifi.connect()   
        
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
        
    def status_page(self,req,resp):
        return Html("test")
        
    def other_page(self,req,resp):
        value = req.get('name')
        return {"name":value, "test":123}