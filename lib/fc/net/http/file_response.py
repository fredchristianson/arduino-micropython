

from .response_content import ResponseContent
from .mime import get_mime_type_from_content
import json


class FileResponse(ResponseContent):
    def __init__(self,filename,buf_size=1024):
        super().__init__()
        self.filename = filename
        self.buf_size = buf_size
        with open(filename,'rb') as f:
            buf = f.read(100)
            self.mime_type = get_mime_type_from_content(buf)
            
    def get_data(self):
        with open(self.filename,'rb') as f:
            chunk = f.read(self.buf_size)
            while chunk:
                yield chunk
                chunk = f.read(self.buf_size)