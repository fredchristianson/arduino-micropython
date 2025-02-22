import logging;
import asyncio
from .app import App
from fc.net.wifi import wifi_connect, wifi_web_configure
import gc

log = logging.getLogger("fc.netapp")


class NetApp(App):

    def __init__(self, name="<unnamed app>"):
        super().__init__(name)
        log.info(f"NetApp created {name}")
        self._http = None
        self._sys_router = None
        self._app_router = None
   
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
            self._sys_router.GET("/sys/config",self.config_page)
            self._sys_router.GET("/sys/uptime",self.uptime_page)
            self._sys_router.GET("/sys/:name",self.other_page)
            self._app_router = HttpRouter()
            self._http.add_router(self._sys_router)
            self._http.add_router(self._app_router)
            self.setup_routes(self._app_router)
            await self._http.start()
        self.is_set_up = True
    
    async def _setup_wifi(self):
        log.info("setup wifi")
        gc.collect()
        
        while not await wifi_connect(self.get_name(),15,delay_seconds=2):
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
        
    async def status_page(self,req,resp):
        from fc.net.http import Html
        return Html("test <b>html</b> response")
        
    async def config_page(self,req,resp):
        return "config content <b>goes</b> here"
           
    async def uptime_page(self,req,resp):
        secs = self._uptime_seconds
        min = (secs//60)%60
        hours = (secs//(60*60))%(60*60)
        days = (secs//(24*60*60))%(24*60*60)
        
        return f"<html><body>Uptime: <b>{days} days {hours} hours {min} minutes {secs%60} seconds.  Total seconds = {secs}</body></html"
        
    async def other_page(self,req,resp):
        from fc.net.http import Json
        value = req.get('name')
        return Json({"name":value, "test":123})