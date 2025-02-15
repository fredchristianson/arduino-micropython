

from .response_content import ResponseContent


class Html(ResponseContent):
    def __init__(self,html):
        super().__init__(html)