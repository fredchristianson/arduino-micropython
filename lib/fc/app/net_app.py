import logging;
import asyncio
from .app import App
from fc.net.wifi import wifi_connect, wifi_web_configure
from fc.net.html import *
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
            from fc.net.http import HttpServer, HttpRouter
            self._http = HttpServer(port)
            self._sys_router = HttpRouter()
            self._sys_router.GET("/sys/status",self.status_page)
            self._sys_router.GET("/sys/config",self.config_page)
            self._sys_router.POST("/sys/config",self.update_config)
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
        doc = HtmlDoc()
        body=doc.body()
        body.child(Text("hello"))
        return doc
        
    async def config_page(self,req,resp,message = "Configuration"):
        from fc.net.html import HtmlDoc
        config = App.CONFIG
        editables,const = config.list_values()
        #log.debug(f"editables: {editables}")
        doc = HtmlDoc()
        body = doc.body()
        body.h1(message)
        form = body.form()
        table = form.table()
        header = table.header()
        header.cell('Name')
        header.cell("Value")
        i=1
        for e in editables:
            # log.debug(f"{e}")
            definition = e.get('definition',{})
            opts = definition.get('_options',None)
            if opts:
                row = table.row()
                name = f"config--{e['path']}"
                val = e['value']
                row.cell(f"{e['path']}")
                row.cell().select(name,val,opts)
            else:
                row = table.row()
                name = f"config--{e['path']}"
                val = e['value']
                row.cell(e['path'])
                row.cell().input(name,f"{val}")
        form.input("submit","Save","submit")

        body.h2("Not Editable")
        table = body.table()
        header = table.header() 
        header.cell('Name')
        header.cell("Value")
        for e in const:
            #log.debug(f"{e}")
            row = table.row()
            row.cell(e['path'])
            row.cell(str(e['value']))
        
        return doc
        # json = Json({'editable':editables,'const':const})
        
        # for e in editables:
        #     if e['path'].endswith('.pin'):
        #         e['value'] = e['value'] + 1
        # config.update(editables)
        # return json
        
    async def update_config(self,req,resp):
        #log.debug(f"Req data: {req.data}")
        values = {k[8:]:req.data[k] for k in req.data.keys() if k.startswith('config--')}
        log.debug(f"Values: {values}")
        App.CONFIG.update(values)
        return await self.config_page(req,resp,"Configuration Updated")
           
    async def uptime_page(self,req,resp):
        secs = self._uptime_seconds
        min = (secs//60)%60
        hours = (secs//(60*60))%(60*60)
        days = (secs//(24*60*60))%(24*60*60)
        
        return f"<html><body>Uptime: <b>{days} days {hours} hours {min} minutes {secs%60} seconds.  Total seconds = {secs}</body></html"
        
    async def other_page(self,req,resp):
        from fc.net.http import JsonResponse as Json
        value = req.get('name')
        return Json({"name":value, "test":123})