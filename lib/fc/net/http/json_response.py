

from .response_content import ResponseContent
import json


class Json(ResponseContent):
    def __init__(self,json_content):
        if type(json_content) != str:
            json_content = json.dumps(json_content)
        super().__init__(json_content,mime_type="application/json")