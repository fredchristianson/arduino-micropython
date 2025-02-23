

from .response_content import ResponseContent


class HtmlResponse(ResponseContent):
    def __init__(self,html):
        super().__init__(mime_type="text/html")
        self.html = html
        
    def get_content(self):
        return self.format(self.html)
    
    def format(self,html):
        html = html.strip()
        if not html.startswith('<html'):
            if not html.startswith('</body'):
                return f'<html><body>{html}</body></html>'
            else:
                return f'<body>{html}</body>'
        return html
    
