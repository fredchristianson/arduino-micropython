
from .mime import get_mime_type_from_content, mime_types

import logging

log = logging.getLogger("fc.net.http.response_content")

class ResponseContent:
    def __init__(self,mime_type=None, status_code = 200, status_text="OK", content=None,on_sent=None):
        log.debug(f"ResponseContent.  type {type(content)}")
        self.status_code = status_code
        self.status_text = status_text
        self._on_sent = on_sent
        if mime_type is None and content is not None:
            self.mime_type = get_mime_type_from_content(content)
        else:
            self.mime_type = "text/plain" if mime_type is None else mime_type
        if type(content) == bytes:
            self.content = memoryview(content)
        elif type(content) == str:
            self.content = memoryview(content.encode('utf-8'))
        elif type(content) != memoryview:
            self.content = memoryview(str(content).encode('utf-8'))

        
    def on_sent(self):
        if self.on_sent:
            self.on_sent()
            
    
    def set_status(self,code,text):
        self.status_code = code
        self.status_text = text
         
    def get_mime_type(self):
        return self.mime_type
    
    def get_data(self):
        yield self.content
    
    def get_status(self):
        return self.status_code,self.status_text
    

    
        
    def on_sent(self):
        pass
    
