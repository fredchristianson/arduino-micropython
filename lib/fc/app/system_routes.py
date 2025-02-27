import logging
from fc.net.http.route import HttpRouter
import time
import math
import gc
from fc.net.wifi import get_station_ip
from fc.net.html import *
from .app import App
 
log = logging.getLogger('fc.net.mqtt')

class SystemRoutes(HttpRouter):
    def __init__(self):
        super().__init__()
        self.GET("/status",self.status_page)
        self.GET("/config",self.config_page)   
        self.POST("/config",self.update_config)
        
    async def status_page(self,req,resp):
        ticks = time.ticks_ms()
        secs =  math.floor(ticks/1000)
        min = math.floor(secs/60)   
        hours = math.floor(min/60)
        days = math.floor(hours/24)
            
        doc = HtmlDoc()
        body=doc.body()
        table =body.namevalue_table()

        table.add("Uptime",f"{days} days {hours%24} hours {min%60} minutes {secs%60} seconds")

        table.add("Free Memory",f"{gc.mem_free():,} bytes")
        gc.collect()
        table.add("Free After collect",f"{gc.mem_free():,} bytes")
        table.add("Allocated Memory",f"{gc.mem_alloc():,} bytes")
        table.add("IP Address",f"{get_station_ip()}")
        return doc
        
    async def config_page(self,req,resp,message = "Configuration"):
        from fc.net.html import HtmlDoc
        from .app import App
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
        
    async def update_config(self,req,resp):
        #log.debug(f"Req data: {req.data}")
        values = {k[8:]:req.data[k] for k in req.data.keys() if k.startswith('config--')}
        log.debug(f"Values: {values}")
        App.CONFIG.update(values)
        return await self.config_page(req,resp,"Configuration Updated")
