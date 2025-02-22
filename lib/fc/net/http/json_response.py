

from .response_content import ResponseContent
import json


class Json(ResponseContent):
    def __init__(self,json_content):
        super().__init__(mime_type="application/json")
        self.json_cotent = json_content
    
    def get_content(self):
        if type(json_content) != str:
            json_content = json.dumps(json_content)
        return json_content