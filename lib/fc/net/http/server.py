import logging
import asyncio
from .route import StaticFileRouter
from .req_resp import HttpRequest, HttpResponse


log = logging.getLogger("fc.net.http.server")
request_id = 0

class HttpServer:
    def __init__(self,port=80,host='0.0.0.0'):
        super().__init__()
        log.info("HttpServer created")
        self.port = port
        self.host = host
        self.routers = []
        self.static_file_router = StaticFileRouter("/html")
        self.tcp_server = None
        self.connections = set()
       
    def set_static_file_path(self,path):
        self.static_file_router.set_directory_path(path)
     
    def add_router(self,router,path_prefix="/"):
        # new routers go at the front to override earlier routes
        self.routers.insert(0,(path_prefix,router))
                    
    async def process_req(self,reader,writer):
        """Process an incoming request.  """
        self.connections.add(writer)
        try:
            # line = await reader.readline()
            # print(f"got line {line}")
            # print(f"got line {line.decode()}")
            # return
            log.debug("process_req")
            req = HttpRequest(self)
            resp = HttpResponse(self,writer)
            req.set_response(resp)
            resp.set_request(req)
            log.debug("parse request")

            if not await req.parse_request(reader):
                try:
                    writer.write(b'HTTP/1.0 404 not found\r\nContent-Type: text/plain\r\n\r\nFile Not Found\r\n')   
                except Exception as ex:
                    log.exception("cannot write 4040 response",ex)
                    return
            else:
                path = req.get_path()
                orig_path = path
                method = req.get_method()
                log.debug(f"method: {method} path: {path}")
                handled = False
                for router in self.routers:
                    log.debug("try router")
                    path = orig_path
                    rpath = router[0]
                    if rpath != None and len(rpath)>1:
                        if not path.startswith(rpath):
                            log.info(f"{path} not in router path {rpath}")
                            continue
                        path = path[len(rpath):]
                    rhandler = router[1]
                    req.set_path(path)
                    handled = await rhandler.handle(req,resp)
                    if handled:
                        break
                log.info(f"router handled request: {handled}")
                if not handled:
                    if path == '/':
                        path = '/index.html'
                        req.set_path('/index.html')
                    handled = await self.static_file_router.handle(req,resp)
                    log.info(f"static file handled request: {handled}")
                    
                if not handled:
                    req.set_path('/404.html')
                    handled = await self.static_file_router.handle(req,resp)
                    log.info(f"404 handled: {handled}")
                
                if not handled:
                    try:
                        writer.write(b'HTTP/1.0 404 not found\r\nContent-Type: text/plain\r\n\r\nFile Not Found\r\n')   
                    except Exception as ex:
                        log.exception("cannot write 4040 response",ex)
                        return                        
        except Exception as ex:
            log.error("error processing request")
            log.exception("Exception",exc_info = ex)
            writer.write(b'HTTP/1.0 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nInternal Server Error\r\n')
        try:
            await writer.drain()
            log.debug("wait drain")
            await asyncio.sleep(1)
            log.debug("delay done")
            await writer.drain()

            log.debug("close")
            writer.close()
            log.info("wait close")
            await writer.wait_closed()

            log.info("connection done")
        except Exception as ex:
            log.exception("Failed to close connection",exc_info=ex)
        finally:
            self.connections.remove(writer)
                        
                
    async def start(self):
        # run the app
        log.info(f"start server {self.host}:{self.port}")
        handler = self
        async def callback(reader,writer): 
            try:
                log.debug("http callback")
                await handler.process_req(reader,writer)
                log.debug("callback done")
            except Exception as ex:
                log.exception("handler failed ",exc_info=ex)
        self.tcp_server = await  asyncio.start_server(callback, self.host, self.port)

        return self.tcp_server
    
    async def stop(self):
        if self.tcp_server is None:
            log.error("stop called without a running server") 
            return
        for conn in list(self.connections):
            await asyncio.wait_for_ms(conn.wait_closed(),2000)
        self.tcp_server.close()
        await self.tcp_server.wait_closed()
        self.tcp_server = None