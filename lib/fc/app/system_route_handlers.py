import logging
import machine
import json
from fc.modload.modload import loader
from fc.net.http.router import Redirect
from .app import App
# from fc.net.http import Redirect
# import time
# import math
# import gc
# from fc.net.wifi import get_station_ip
# from fc.html.elements import *
# from lib.fc.net.http.json_response import JsonResponse
# from .app import App
# from fc.datetime import datetime
# import machine
 
log = logging.getLogger('fc.app.http.sys')


def status_page(req):
    with loader('time','fc.net.wifi','math','fc.datetime','fc.html.elements','gc') as (time,wifi,math,datetime,html,gc):
        ticks = time.ticks_ms()
        secs =  math.floor(ticks/1000)
        min = math.floor(secs/60)   
        hours = math.floor(min/60)
        days = math.floor(hours/24)
        now = datetime.now()
        
        doc = html.HtmlDoc()
        body=doc.body()
        table =body.namevalue_table()

        table.add("Time",datetime.isoformat(now))
        table.add("Uptime",f"{days} days {hours%24} hours {min%60} minutes {secs%60} seconds")

        table.add("Free Memory",f"{gc.mem_free():,} bytes")
        gc.collect()
        table.add("Free After collect",f"{gc.mem_free():,} bytes")
        table.add("Allocated Memory",f"{gc.mem_alloc():,} bytes")
        table.add("IP Address",f"{wifi.get_station_ip()}")
        return doc
        
def config_page(req):
    with loader('fc.html.elements','json') as (html,json):
        if 'message' in req['url']['params']:
            message = req['url']['params']['message']
        else:
            message = "Configuration"
        config = App.CONFIG
        doc = html.HtmlDoc()
        body = doc.body()
        body.h1(message)
        form = body.form()
        text = json.dumps(config)
        form.textarea('config',text,class_='json')
        form.input("submit","Save","submit")
        return doc
    
def update_config(req):
    with loader('fc.app') as app:
        config = req['data']['config'] # {k[8:]:req.data[k] for k in req.data.keys() if k.startswith('config--')}
        vals = json.loads(config)
        app.App.CONFIG.set_values(vals)
        #return await self.config_page(req,"Configuration Updated")
        return Redirect('/config_updated.html')

        
def reboot(req):
    log.debug(f"/sys/reboot")

    req.on_complete(lambda:log.info("rebooting"))
    req.on_complete(lambda:machine.reboot())
    return {"result":'ok','text':'rebooting'}

