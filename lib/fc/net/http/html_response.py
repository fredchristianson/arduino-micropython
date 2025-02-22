

from .response_content import ResponseContent


class Html(ResponseContent):
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
    
class HtmlElement:
    def __init__(self,tag,attrs={}):
        self._tag = tag
        self._attrs = attrs
        self._children = []
        
    def to_html(self):
        return f"<{self._tag} {self.attrs_to_html()}>{self.children_to_html()}</{self._tag}>"
    
    def attrs_to_html(self):
        html = [f"{attr}='{self._attrs[attr]}'" for attr in self._attrs.keys()]
        return ' '.join(html)
        
    def add(self,child):
        self._children.append(child)
        
    def children_to_html(self):
        html = [child.to_html() for child in self._children]
        return ' '.join(html)
        
class Text(HtmlElement):
    def __init__(self,text):
        self._text = text
    
    def to_html(self):
        return self._text
    
class HtmlDoc(HtmlElement,ResponseContent):
    def __init__(self):
        super().__init__('html')
        self._head = HtmlElement('head')
        self._body = HtmlElement('body')
        self.add(self._head)
        self.add(self._body)
        
    def get_content(self):
        return self.to_html()

    def head(self):
        return self._head
                
    def body(self):
        return self._body

        
