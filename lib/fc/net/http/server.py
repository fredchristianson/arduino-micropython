import asyncio
from lib.fc.modload.modload import loader
import logging

log=logging.getLogger('fc.net.http.server')

async def test_handler(reader,writer):
    log.info("HTTP handler")

def start_server(port=80,host='0.0.0.0'):
    with loader('fc.net.http.impl.request_handler') as handler:
        http_server = await asyncio.start_server(
            test_handler, #handler.http_request_handler,
            host=host,
            port=port
        )
        with loader('fc.net.wifi') as wifi:
            log.info(f"HTTP listen on {wifi.get_station_ip()}:{port}")
        return {'server':http_server,'host':host,'port':port,'routers':[]}

def add_router(server,path,router):
    server['routers'].append({'path':path,'router':router})