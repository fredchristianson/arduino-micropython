import asyncio
from lib.fc.modload.modload import loader
import logging
from fc.util import join_path

log=logging.getLogger('fc.net.http.server')

async def test_handler(reader,writer):
    log.info("HTTP handler")

def start_server(port=80,host='0.0.0.0'):
    with loader('fc.net.http.impl.request_handler') as handler:
        server_def = None
        async def handle(reader,writer):
            await handler.handle_request(server_def,reader,writer)
            
        http_server = await asyncio.start_server(
            handle,
            host=host,
            port=port
        )
        with loader('fc.net.wifi') as wifi:
            log.info(f"HTTP listen on {wifi.get_station_ip()}:{port}")
        server_def = {'server':http_server,
                      'host':host,'port':port,
                      'default_url': '/index.html',
                      'routers':[],'routes':{}}
        return server_def

def add_router(server,path,router):
    # add new routes at the front so they are checked first
    # and can override existing routes
    server['routers'].insert(0,{'path':path,'router':router})
    log.debug(f"add routes {path}  {router}")
    for route in router['routes']:
        rpath = join_path(path,route['path'])
        log.debug(f"create route '{rpath}'")
        server['routes'][rpath] = route