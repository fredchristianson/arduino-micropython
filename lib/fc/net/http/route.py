import logging
import os
from fc.util import Path
from lib.fc.net.http.req_resp import Values
from .mime import get_mime_type_from_ext

log = logging.getLogger("fc.net.http.route")

class RoutePath:
    def __init__(self,path) -> None:
        self.path = path
        self.parts = [p for p in path.strip('/').split("/") if p != '']
        
    def match(self,path):
        """try to match a path.  return None if no match, otherwise return a dictionary of values.
        A route path like '/api/:name/:id' will match '/api/joe/123' and return 
        {'name':'joe','id':'123'}.

        Args:
            path (str): path to match.  may be a partial path if beginning removed by Route

        Returns:
            dict[str,str]: any captured values in the path.  
        """
        values = {}
        if len(self.parts) == 1 and self.parts[0] == '*':
            return values
        parts = [p for p in  path.strip('/').split("/") if p != '']
        log.debug(f"match {parts} to {self.parts}")
        if len(parts) != len(self.parts):
            return None
        for i in range(len(parts)):
            if self.parts[i] == "*":
                continue
            elif len(parts[i])>1 and self.parts[i][0] == ':':
                values[self.parts[i][1:]] = parts[i]
            elif self.parts[i] != parts[i]:
                return None
        log.debug(f"matched: {values}")
        return values
    
    def get_path_values(self,path):
        return self.match(path) if path is not None else {}
    
    def __str__(self):
        return f"RoutePath {self.path} {self.parts}"
    
    def __repr__(self):
        return f"RoutePath {self.path} {self.parts}"

class HttpRoute:
    def __init__(self,path,callback,method="GET") -> None:
        self.path = RoutePath(path)
        self.callback = callback
        self.method = method.upper() if method is not None else "*"
        
    def is_match(self,req):
        path = req.get_path()
        if self.method.upper() != req.get_method():
            return False
        values = self.path.match(path)
        if values is not None:
            req.set_path_values(values)
            return True
        return False
    
    def handle(self,req,resp,path=None):
        values = self.path.get_path_values(path)
        req.set_path_values(values)
        response = self.callback(req,resp)
        log.debug(f"response: {response}")
        return response

        
    def __str__(self):
        return f"HttpRoute {self.path}"        
    def __repr__(self):
        return f"HttpRoute {self.path}"

class HttpRouter:
    def __init__(self,routes=[]):
        """a collection of routes with a common path prefix.
        if routes are provided, they are tuples (method,path,callback)
            method is GET, POST, etc. '*' matches all methods. May be left out and "GET" is assumed.
            route path is the path to match.  Full path is "{path}/{route path}"
            Callback is the function to call.
            
        Routes are processed in order and the first match is used.
        
        If a path component begins with a colon, it is considered a variable and will match any value.
        If a path component is '*', it will match any value and the value will be ignored.

        Args:
            routes (list, tuple): (method,path,callback). Defaults to [].
            path_prefix (str, optional): path prefix for all routes. Defaults to "".
        """


        self.routes = []
        for route in routes:
            if len(route) == 2:
                self.add_route(HttpRoute(route[0],route[1],"GET"))
            else:
                self.add_route(HttpRoute(route[1],route[2],route[0]))
        
    def add_route(self,route):
        self.routes.append(route)
        
    def GET(self,url,callback):
        self.add_route(HttpRoute(url,callback,"GET"))
        
    def POST(self,url,callback):
        self.add_route(HttpRoute(url,callback,"POST"))
        
    async def handle(self,req,resp):
        path = req.get_path()
        log.debug(f"{self.__class__.__name__}: Handle route {path} {resp}")
        for route in self.routes:
            log.debug(f"try {route}")            
            if route.is_match(req):
                log.debug("found match")
                content = await route.handle(req,resp)
                log.info(f"got: {content[0:20]}")
                if content is not None:
                    await resp.send(content)
                return True
        return False
        

class StaticFileRoute(HttpRoute):
    def __init__(self,directory,extensions):
        async def handle(req,resp):
            return await self.send_file(req,resp=resp)
            
        super().__init__("*",handle,"GET")
        self.directory = directory
        self.extensions = extensions
        
    def set_root_path(self,path):
        self.directory = path
        
    def is_match(self,req):
        path = req.get_path()
        log.info(f"StaticFileRoute is_match: {path}")
        if req.get_method() != "GET":
            return False
        if not '.' in path:
            log.error("can only return paths with an extension")
            return False
        ext = path.split('.')[-1]
        if not ext in self.extensions:
            return False
        full_path = Path.join(self.directory,path)
        log.debug(f"full path: {full_path}")
        try:
            os.stat(full_path)
            return True
        except:
            log.error(f"File {full_path} does not exist")
            return False
        
    async def send_file(self,req,resp):
    
        log.debug(f"send file: {req}")

        full_path = Path.join(self.directory,req.get_path())
        values = self.path.get_path_values(full_path)
        req.set_path_values(Values)
        log.debug(f"path {full_path}")
        try:
            dot = full_path.rfind('.')
            if dot is not None and dot >= 0:
                ext = full_path[dot:]
                log.debug(f"ext {ext}, mime {get_mime_type_from_ext(ext)}")
                resp.content_type(get_mime_type_from_ext(ext))
            blen = 1024
            fstat  = os.stat(full_path)
            flen = fstat[6]
            log.debug(f"file flen {flen}.  send to {resp}")
            resp.content_length(flen)
            await resp.send_headers()
            with open(full_path,'rb') as file:
                data = file.read(blen)
                while data:
                    #log.debug(f"send data {data}")
                    #log.debug(f"send len {len(data)}")
                    await resp.send_data(memoryview(data))
                    log.debug(f'sent {len(data)} bytes of data')
                    data = file.read(blen)
                log.debug("file sent")
        except Exception as ex:
            log.error(f"cannot read file {full_path}")
            log.exception("Exception",exc_info = ex)
            await resp.send_error(404,str(ex))
        return None  # HttpRoute should not send anything since already sent
    
class StaticFileRouter(HttpRouter):
    def __init__(self,dir='/html', extensions=['html','css','js','png','jpg','jpeg','gif','ico']):
        super().__init__([])
        self.extensions = extensions
        self.route = StaticFileRoute(dir,extensions)
        self.add_route(self.route)
        
    def set_root_path(self,path):
        self.route.set_root_path(path)
        
        

