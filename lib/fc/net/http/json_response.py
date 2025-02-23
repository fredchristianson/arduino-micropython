

from .response_content import ResponseContent
import json


class JsonResponse(ResponseContent):
    def __init__(self,json_content):
        self.json_content = self.get_json(json_content)

        super().__init__(mime_type="application/json",content = self.json_content)
    
    def get_json(self,json_content):
        if type(json_content) != str:
            json_content = json.dumps(json_content)
        return json_content