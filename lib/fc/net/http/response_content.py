
from .mime import get_mime_type_from_content
import logging

log = logging.getLogger("fc.net.http.response_content")

class ResponseContent:
    def __init__(self,mime_type=None, status_code = 200, status_text="OK", content=None):
        log.debug(f"ResponseContent.  type {type(content)}")
        self.mime_type = mime_type
        self.status_code = status_code
        self.status_text = status_text
        self.length = None
        self.content = content
       
    def set_status(self,code,text):
        self.status_code = code
        self.status_text = text
         
    def get_mime_type(self):
        if self.mime_type == None:
            self.get_data()
        return self.mime_type
    
    def get_data(self):
        content = self.get_content() 

        if self.mime_type == None:
            self.mime_type = get_mime_type_from_content(content)
        self.content = content
        if type(content) == bytes:
            self.content = memoryview(content)
        elif type(content) == str:
            return memoryview(content.encode('utf-8'))
        else:
            self.content = memoryview(str(content).encode('utf-8'))
        if self.length == None:
            self.length = len(self.content)
        return self.content
    
    def get_status(self):
        return self.status_code,self.status_text
    
    def set_length(self,length):
        self.length = length
        
    def get_length(self):
        if self.length == None:
            if self.content == None:
                self.get_data()  
            else:
                self.length = len(self.content)
        return self.length
    
    def get_content(self):
        from fc.net.html import HtmlElement
        if isinstance(self.content ,HtmlElement):
            self.content = self.content.to_html()
            self.mime_type = 'text/html'
        
        return self.content if self.content is not None else "No content to return."
        
    def on_sent(self):
        pass
    
