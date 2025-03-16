
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
    

