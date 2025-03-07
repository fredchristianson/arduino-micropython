import logging

from fc.modload import loader
# from fc.net.http import Redirect
# import time
# import math
# import gc
# from fc.net.wifi import get_station_ip
# from fc.net.html import *
# from lib.fc.net.http.json_response import JsonResponse
# from .app import App
# from fc.datetime import datetime
# import machine
 
log = logging.getLogger('fc.net.sys')


async def status_page(req,resp):
    with loader('time','fc.net.wifi','math','fc.datetime','fc.net.html','gc') as (time,wifi,math,datetime,html,gc):
        ticks = time.ticks_ms()
        secs =  math.floor(ticks/1000)
        min = math.floor(secs/60)   
        hours = math.floor(min/60)
        days = math.floor(hours/24)
        now = datetime.datetime.now()
        
        doc = html.HtmlDoc()
        body=doc.body()
        table =body.namevalue_table()

        table.add("Time",now.isoformat())
        table.add("Uptime",f"{days} days {hours%24} hours {min%60} minutes {secs%60} seconds")

        table.add("Free Memory",f"{gc.mem_free():,} bytes")
        gc.collect()
        table.add("Free After collect",f"{gc.mem_free():,} bytes")
        table.add("Allocated Memory",f"{gc.mem_alloc():,} bytes")
        table.add("IP Address",f"{wifi.get_station_ip()}")
        return doc
        
async def config_page(req,resp,message = "Configuration"):
    with loader('fc.net.html','.app') as (html,app):
        config = app.App.CONFIG
        doc = html.HtmlDoc()
        body = doc.body()
        body.h1(message)
        form = body.form()
        table = form.table()
        text = config.to_json()
        log.debug(f"Config: {text}")
        form.textarea('config',text,class_='json')
        form.input("submit","Save","submit")
        log.debug("return doc")
        return doc
    
async def update_config(req,resp):
    with loader('fc.app') as app:
        #log.debug(f"Req data: {req.data}")
        json = req.get('config') # {k[8:]:req.data[k] for k in req.data.keys() if k.startswith('config--')}
        log.debug(f"config: {json}")
        app.App.CONFIG.from_json(json)
        #return await self.config_page(req,resp,"Configuration Updated")
        return Redirect('/config_updated.html')

        
async def reboot(req,resp):
    log.debug(f"/sys/reboot")

    req.on_complete(lambda:log.info("rebooting"))
    req.on_complete(lambda:machine.reboot())
    return JsonResponse({"result":'ok','text':'rebooting'})

