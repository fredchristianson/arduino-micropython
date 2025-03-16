from asyncio import StreamWriter, StreamReader
import os
import json
from fc.util import join_path
from .chunk_writer import ChunkWriter
import logging
from fc.net.http.router import RequestHandler

from lib.fc.net.http.impl import chunk_writer
log = logging.getLogger('fc.net.http.http_handler')

def url_decode(s):
    if not s:
        return None
    if type(s) == bytes:
        s = s.decode('utf-8')
    result = ""
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 2 < len(s):
            # Convert the next two hex digits to a character
            try:
                hex_str = s[i+1:i+3]
                result += chr(int(hex_str, 16))
                i += 3
            except ValueError:
                # If invalid hex, treat it as literal
                result += s[i]
                i += 1
        elif s[i] == '+':
            result += ' '
            i+= 1
        else:
            result += s[i]
            i += 1
    return result.strip()

def parse_params(params):
    result = {}
    if params:
        pairs = params.split('&')
        for pair in pairs:
            if '=' in pair:
                key,value = pair.split('=',1)
                result[url_decode(key)] = url_decode(value)
            else:
                params[url_decode(pair)] = True
    return result
                
def parse_req_url(url):
    path = url
    query = None
    params = {}

    if '?' in path:
        path,query = path.split('?',1)
        params = parse_params(query)

    components = {
        'full': url,
        'path': url_decode(path),
        'query': query,
        'params': params
    }
    
    return components

async def parse_req_line(reader):
    req_line = await reader.readline()
    req_line = req_line.decode('utf-8')
    parts = req_line.split()
    method = parts[0].upper()
    url = parse_req_url(parts[1])
    return method,url
    
async def parse_headers(reader):
    headers = {}
    while True:
        line = await reader.readline()
        line = line.decode('utf-8')
        if line == '\r\n':
            break
        key, value = line.split(':', 1)
        headers[url_decode(key)] = url_decode(value)
    return headers

async def parse_form_data(reader,len):
    line = await reader.read(len)
    line = url_decode(line)
    
    data = parse_params(line)
    return data


async def read_request(reader):
    req = {}
    method,url = await parse_req_line(reader)
    req['method'] = method
    req['url'] = url
    req['headers'] = await parse_headers(reader)
    data = {}
    data.update(req['url']['params'])
    req['body_stream'] = reader
    if 'Content-Type' in req['headers']:
        ctype = req['headers']['Content-Type']
        clen = int(req['headers']['Content-Length'])
        if ctype == 'application/x-www-form-urlencoded':
            data.update(await parse_form_data(reader,clen))
        elif ctype == 'application/json':
            len = int(req['headers']['Content-Length'])
            content = await reader.read(len)
            data = json.loads(content)
    req['data'] = data
    return req

async def find_handler(routers,req):
    url = req['url']
    method = req['method']
    path = url['path'].rstrip('/')
    log.info(f"find route {method} {path}")

    for router_def in routers:
        rpath = router_def['path'] if 'path' in router_def else ''
        router = router_def['router']
        for route in router['routes']:
            p=join_path(rpath,route['path']).rstrip('/')
            if p == path and route['method'] == method:
                return route['handler'] if 'handler' in route else route
    return None

mime_types = {
    '.html': 'text/html',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.jpeg': 'image/jpg',
    '.gif': 'image/gif',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml'
}

def get_content_type(path):
    ext = path[path.rfind('.'):]
    if ext in mime_types:
        return mime_types[ext]
    return 'text/plain'
    
class FileReader:
    def __init__(self, path):
        self.path = path
        self.buf_size = 1024
        
    def get_mime_type(self,req):
        # req is HTTP request if called from a request handler        
        return get_content_type(self.path)
    
    def get_data(self,req):
        with open(self.path, 'rb') as f:
            while True:
                buf = f.read(self.buf_size)
                if len(buf) == 0:
                    return
                yield buf
    
    def get_headers(self,req):
        return {
            'test':'test header',
            'abc': 123
        }
        

def find_file_handler(path):
    if not '.' in path:
        path = path+'.html'
    if not path.startswith('/html'):
        path = join_path('/html',path)
    try:
        log.debug(f"Trying to find file {path}")
        os.stat(path)
        return FileReader(path)
    except Exception as ex:
        log.error(f"Cannot find file {path}")
        return None

def find_error_file_handler(status_code):
    if type(status_code) == int:
        err_page = f'{status_code}.html'
    else:
        err_page = status_code
    return find_file_handler(err_page)

def find_default_file_handler(req):
    return find_file_handler('/index.html')


def find_static_file_handler(req):
    return find_file_handler(req['url']['path'])

def error_handler(status_code=500,message='unknown error'):
    return RequestHandler(f"request failed {message}",'text/plain',status_code,message)
    
async def send_headers(req,writer,handler):
    headers = {
        'Transfer-Encoding': 'chunked',
        'Connection': 'close',
        'Cache-Control': 'no-store, no-cache, must-revalidate'
    }
    if hasattr(handler,'headers') and handler.headers is not None:
        log.warning(f"{handler} - {headers}")
        headers.update(handler.headers)
    elif hasattr(handler,'get_headers') and handler.get_headers is not None:
        headers.update(handler.get_headers(req))
    if hasattr(handler,'mime_type') and handler.mime_type is not None:
        headers['Content-Type'] = handler.mime_type
    elif hasattr(handler,'get_mime_type'):
        headers['Content-Type'] = handler.get_mime_type(req)
    status_code,status_text = 200,'OK'
    if hasattr(handler,'get_status'):
        status_code,status_text = handler.get_status(req)
    writer.write(f'HTTP/1.1 {status_code} {status_text}\r\n'.encode('utf-8'))
    for key,value in headers.items():
        writer.write(f'{key}: {value}\r\n'.encode('utf-8'))
    writer.write(b'\r\n') 
    await writer.drain()       
          
    
async def send_body(req,writer,handler):

    chunkwriter = ChunkWriter(writer)
    if hasattr(handler,'get_data'):
        for chunk in handler.get_data(req):
            await chunkwriter.write(chunk)
    elif type(handler) == str:
        # if handler is just a string or implements __str__, send it
        await chunkwriter.write(handler)
    else:
        # if handler is not a string, send it as json
        await chunkwriter.write(json.dumps(handler))
    await chunkwriter.done()
    
async def send_response(req,writer,handler):
    headers_sent = False
    try:
        if callable(handler):
            log.info("call handler")
            handler = handler(req)
               
        await send_headers(req,writer,handler)
        headers_sent = True
        await send_body(req,writer,handler)
    except Exception as ex:
        log.exception(f'error sending response {ex}',exc_info=ex)
        if not headers_sent:
            writer.write(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
        writer.write(b'Internal Server Error\r\n\r\n')
        writer.write(str(ex).encode('utf-8'))
    finally:
            await writer.drain()
        
        
async def handle_request(server,reader, writer):
    try:
        log.info(f'new connection for server {server}')

        routers = server['routers']
        addr = writer.get_extra_info('peername')
        
        log.info('received from %r',  addr)
        req = await read_request(reader)
        
        handler = await find_handler(routers,req)
        
        if not handler:
            handler = find_static_file_handler(req) or find_default_file_handler(req) or find_error_file_handler('404') or error_handler(404,'not found')
        
        await send_response(req,writer,handler)
    except Exception as ex:
        log.exception("Failed to process HTTP request",exc_info=ex)
    finally:
        writer.close()
        await writer.wait_closed()
        