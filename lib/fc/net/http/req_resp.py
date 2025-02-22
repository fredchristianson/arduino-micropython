import asyncio
import io
from asyncio import StreamReader, StreamWriter
import logging

from .response_content import ResponseContent
from .mime import get_mime_type_from_content
import gc

log = logging.getLogger("fc.net.http.server.req_resp")

        
def urldecode(encoded_str):
    decoded_str = ""
    i = 0
    while i < len(encoded_str):
        if encoded_str[i] == '%' and i + 2 < len(encoded_str):
            # Decode percent-encoded characters (e.g., %20 -> space)
            hex_value = encoded_str[i+1:i+3]
            decoded_str += chr(int(hex_value, 16))
            i += 3
        elif encoded_str[i] == '+':
            # Decode '+' as space
            decoded_str += ' '
            i += 1
        else:
            # Keep other characters as-is
            decoded_str += encoded_str[i]
            i += 1
    return decoded_str   

class Values:
    def __init__(self):
        self._values = {}
        
    def items(self):
        return self._values.items()
            
    def get(self,name,default_val = None):
        val = self._values[name] if name in self._values else None
        if val is not None and default_val is not None:
            try:
                if type(default_val) == int:
                    return int(val)
                elif type(default_val) == bool:
                    return val.lower() not in ['none','false','0','f','no']
                elif type(default_val) == float:
                    return float(val)
            except Exception:
                return val
        return val

    def set(self,name,val):
        self._values[name] = val
    
    def add(self,name,val):
        if name in self._values:
            old = self._values[name]
            if type(old) != list:
                old = [old]
            old.append(val)
            self._values[name] = old
        else:
            self._values[name] = val
        
    
    def __str__(self):
        return f"{self.__class__.__name__}: {str(self._values)}"
    
    def __repr__(self):
         return f"{self.__class__.__name__}: {str(self._values)}"  
    
class Headers(Values):
    def __init__(self):
        super().__init__()
        

        
    def get_all(self):
        return self._values
    
    def set_default(self,name,val):
        if not name in self._values:
            self._values[name] = val
    
    
class ReqResp:
    """base class for request and response
    """
    
    def __init__(self,server):
        log.debug("create ReqResp")
        self.server = server
        self.request = None
        self.response = None
        self.headers = Headers()
        
    def set_request(self,request):
        self.request = request
        
    def set_response(self,response):
        self.response = response
     
        
class HttpRequest(ReqResp):
    def __init__(self,server):
        super().__init__(server)
        log.debug("create Request")
        self.method = None
        self.uri = None
        self.path = None
        self.query = None
        self.params = Values()
        self.data = Values()
        self.json = None
        self.http_version = None
        self.body = None
        self.path_values = {} # for paths like /test/:type/:id  type and id are path values

        
    def get_method(self):
        return self.method
    
    def get_path(self):
        return self.path    
    
    def set_path(self,path):
        self.path = path
    def set_path_values(self,vals):
        self.path_values = vals or {}
    async def parse_request(self,reader):
        #log.debug(f"parse_request {reader}")
        http = await asyncio.wait_for_ms(reader.readline(),5000)
        log.debug(f"read: {http}")
        log.debug(f"read: {http.decode()}")
        if http is None:
            log.error("request not read")
            return False
        http = http.decode()
        parts = http.split(" ")
        if parts is None or len(parts) <3:
            log.error(f"invalid request: {http}")
            return False
        self.method = parts[0].upper()
        self.uri = parts[1]
        self.http_version = parts[2]
        
        if "?" in self.uri:
            parts = self.uri.split("?")
            self.path = parts[0]
            self.query = parts[1]
            log.debug(f"parse query {self.query}")
            vals = self.query.split("&")
            for val in vals:
                parts = val.split("=")
                self.params.add(urldecode(parts[0]),urldecode(parts[1]))
            log.debug(f"params: {self.params}")
        else:
            self.path = self.uri
        
        next = await   asyncio.wait_for_ms(reader.readline(),5000)
        next = next.decode()
        while next != "\r\n":
            log.debug(f"parse header {next}")
            parts = next.split(":")
            self.headers.set(parts[0].strip(),parts[1].strip())
            next =   await asyncio.wait_for_ms(reader.readline(),5000)
            next = next.decode()
        

            
        clen = self.headers.get("Content-Length",0)
        log.debug(f"content length {clen}")
        if clen is not None:
            log.debug(f"read body len={clen}")
            self.body = await reader.read(clen)
        else:
            self.body = None #await reader.read(10000)
        log.debug("parsed request")
        
        mime = headers =self.headers.get('Content-Type')
        if mime == 'application/x-www-form-urlencoded' and self.body is not None:
            vals = self.body.decode().split("&")
            for val in vals:
                parts = val.split("=")
                self.data.add(urldecode(parts[0]),urldecode(parts[1]))            
            
        return True
    
    def get(self,name,default_value = None):
        """ try to get the name from params, data, headers.  the first value found is returned"""
        val = self.path_values[name] if name in self.path_values else None
        if val is None:
            val = self.params.get(name)
        if val is None:
            val = self.data.get(name)
        if val is None:
            val = self.headers.get(name)
        return val or default_value
        
class HttpResponse(ReqResp):
    def __init__(self,server,writer:StreamWriter):
        super().__init__(server)
        self.writer = writer
        self.headers = Headers()
        self.status_code = 200
        self.status_text = "OK"
        self.content_len = None
        self.mime_type = None
        self.body = None
        
        
    def status(self,status_code,text=None):
        self.status_code = status_code
        self.status_text = text 
        
    def content_type(self,mime_type):
        self.mime_type = mime_type
        
    def content_length(self,len):
        self.content_len = len
        
    async def send_headers(self):
        log.debug('send headers')
        if not self.headers.get('connection'):
            self.headers.set('Connection','close')
        w = self.writer
        w.write(f"HTTP/1.1 {self.status_code} {self.status_text}\r\n".encode("utf-8"))
        await w.drain()
        if self.mime_type is not None:
            self.headers.set_default('Content-Type',self.mime_type )
        if self.content_len is not None:
            self.headers.set_default('Content-Length',self.content_len )
        for name,val in self.headers.items():
            log.info(f"Header:  {name}={val}")
            w.write(f"{name}: {val}\r\n".encode('utf-8'))
        w.write(b"\r\n")       
        log.debug('headers sent') 
        
    async def send_data(self,data):
        log.debug(f"sending {len(data)} bytes of data")
        self.writer.write(data)
        await self.writer.drain()

        
    async def send_content(self,content):
        try:
            log.debug("write: page")
            self.mime_type = content.get_mime_type()       
            data = io.BytesIO(content.get_data())
            log.debug(f"Mime type %s",self.mime_type)
            data_len = content.get_length()
            log.debug(f"Data len %d",data_len)
            self.content_length(data_len)
            log.debug("send headers")
            await self.send_headers()
          
            log.info(f"write binary len {data_len}")
            buflen = 1024 # int(gc.mem_free()/2)
            while data.tell() < data_len:
                # writing needs to allocate memory.  garbage or it can fail
                gc.collect()
                buf = data.read(buflen)
                await self.send_data(buf)
                log.info(f"wrote data len ={len(buf)}")
            content.on_sent()
        except Exception as ex:
            log.exception("Cannot send data",exc_info=ex)
 
        
    async def send(self,content):
        log.info(f"send content: {content[0:20]}")
        if not isinstance(content,ResponseContent):
            content = ResponseContent(content = content)
        await self.send_content(content)
            
    async def send_error(self,code,text="error"):
        log.debug("write error")
        self.status(code,text)
        await self.send(text)

            
    
        