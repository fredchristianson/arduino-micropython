

from .response_content import ResponseContent
from .mime import get_mime_type_from_content
import json


class Redirect(ResponseContent):
    def __init__(self,to_url, on_sent=None):
        super().__init__(mime_type='text/html',on_sent=on_sent)
        self._to_url = to_url
        self.status_code = 302
        self.status_text = f"Redirect to: {self._to_url}"
            
    def prepare_response(self,req,resp):
        resp.headers.add("Location",self._to_url)

    def get_data(self):
        yield f'<html><body>Redirect to: <a href="{self._to_url}">{self._to_url}</a></body></html>'
         
    def get_mime_type(self):
        return self.mime_type        