
from .mime import get_mime_type_from_content


class ResponseContent:
    def __init__(self,content, mime_type=None, status_code = 200, status_text="OK"):
        self.content = memoryview(content if type(content) == bytes else content.encode('utf-8'))
        self.mime_type = get_mime_type_from_content(content) if mime_type is None else mime_type
        self.status_code = status_code
        self.status_text = status_text
       
    def set_status(self,code,text):
        self.status_code = code
        self.status_text = text
         
    def get_mime_type(self):
        return self.mime_type
    
    def get_data(self):
        return self.content 
    
    def get_status(self):
        return self.status_code,self.status_text
    
    def get_length(self):
        return len(self.content)
    
    def on_sent(self):
        pass
    
