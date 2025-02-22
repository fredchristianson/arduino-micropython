

from .response_content import ResponseContent
import json


class Json(ResponseContent):
    def __init__(self,json_content):
        super().__init__(mime_type="application/json")
        self.json_content = json_content
    
    def get_content(self):
        if type(self.json_content) != str:
            self.json_content = json.dumps(self.json_content)
        return self.json_content