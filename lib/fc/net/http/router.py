
import logging
import os
import json

GET='GET'
POST='POST'
PUT='PUT'
DELETE='DELETE'


# dict so 'from route import METHOD' gives all methods to use like METHOD.GET
METHOD={
    GET: 'GET',
    POST: 'POST',
    PUT: 'PUT',
    DELETE: 'DELETE'
}

log = logging.getLogger("fc.net.http.route")

def create_router(name, routes=[]):
    return {'name':name,'routes':routes}

class RequestHandler:
    def __init__(self,content,mime_type=None,status=200,status_text='OK',headers=None):
        self.content = content
        self.mime_type = mime_type
        if mime_type is None:
            self.mime_type = 'text/html' if type(content) is str and '<html' in content else 'application/json' if type(content) is dict else 'text/plain'
        self.status_code = status
        self.status_text = status_text
        self.headers = headers or {}
        
    def get_mime_type(self,req): 
        # req is HTTP request if called from a request handler
        return self.mime_type
    
    def get_status(self,req):
        return self.status_code,self.status_text
    
    def get_headers(self,req):
        return self.headers or {}
    
    def get_data(self,req):
        if hasattr(self.content,'get_data'):
            return self.content.get_data
        elif not isinstance(self.content,str):
            return json.dumps(self.content)
        return self.content
    
class Redirect(RequestHandler):
    def __init__(self,location):
        super().__init__(f"Redirect to <a href='{location}'>{location}</a>",'text/html',302,location,{'Location':location})

def add_route(route_table,method,path,handler):
    """handler can be a string (text/html if it starts with "<html" or text/plain)
    a dict (application/json), 
    or an object with a get_data(req) method.
    if it has get_data(req) it can also return 
        get_mime_type(req) 
        get_status(req)->(code,text)
        get_headers(req)->dict[str,str]
    """
    route_table['routes'].append({'method':method,'path':path,'handler':handler})
    

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
        log.debug(f"{self.__class__.__name__}: Handle route {req.get_method()} {path} {resp}")
        for route in self.routes:
            log.debug(f"try {route}")            
            if route.is_match(req):
                log.debug("found match")
                content = await route.handle(req,resp)
                # if content is None, the handler already send the response
                if content is not None:
                    log.info(f"send content: {type(content)}")
                    await resp.send(content)
                return True
        return False
        

class StaticFileRoute(HttpRoute):
    def __init__(self,directory,extensions):
        async def handle(req,resp):
            path = Path.join(self.directory,req.get_path())
            return FileResponse(path)
            
        super().__init__("*",handle,"GET")
        self.directory = directory
        self.extensions = extensions
        self.filename = None
        
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
        
    
class StaticFileRouter(HttpRouter):
    def __init__(self,dir='/html', extensions=['html','css','js','png','jpg','jpeg','gif','ico']):
        super().__init__([])
        self.extensions = extensions
        self.route = StaticFileRoute(dir,extensions)
        self.add_route(self.route)
        
    def set_root_path(self,path):
        self.route.set_root_path(path)
        
        

