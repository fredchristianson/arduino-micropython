

from .response_content import ResponseContent


class HtmlResponse(ResponseContent):
    def __init__(self,html):
        self.html = self.format(html)
        super().__init__(mime_type="text/html",content = self.html)

        

    
    def format(self,html):
        html = html.strip()
        if not html.startswith('<html'):
            if not html.startswith('</body'):
                return f'<html><body>{html}</body></html>'
            else:
                return f'<body>{html}</body>'
        return html
    
