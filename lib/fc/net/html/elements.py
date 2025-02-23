from fc.net.http import HtmlResponse
    
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
        
    def append(self,child):
        self._children.append(child)
        
    def children_to_html(self):
        html = [child.to_html() for child in self._children]
        return ' '.join(html)
    
    def get_content(self):
        """return the content as a string to be returned as content in an HTTP response"""
        return self.to_html()    
        
class Text(HtmlElement):
    def __init__(self,text):
        self._text = text
    
    def to_html(self):
        return self._text
    
class HtmlDoc(HtmlElement):
    def __init__(self):
        super().__init__('html')
        self._head = HtmlElement('head')
        self._body = HtmlElement('body')
        self.append(self._head)
        self.append(self._body)
        
    def get_content(self):
        return self.to_html()

    def head(self):
        return self._head
                
    def body(self):
        return self._body

        
