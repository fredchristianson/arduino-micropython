from fc.net.http import HtmlResponse
from fc.util import Path
import logging

log = logging.getLogger("fc.net.html")
    
html_entities = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}
    
def attr_encode(value):
    value = str(value) if type(value) != str else value
    return ''.join(html_entities.get(c,c) for c in value) if value is not None else ''
    
class HtmlElement:
    def __init__(self,tag,**kwargs):
        attrs = kwargs.get('attrs',{})
        children = kwargs.get('children',[])
        if type(children) != list:
            children = [children]
        for key in kwargs.keys():
            if key not in ['attrs','children']:
                attrs[key] = kwargs[key]        
        self._tag = tag
        self._attrs = attrs
        self._is_self_closing = False
        self._parent = None
        
    def set_attrs(self,**kwargs):
        for key in kwargs.keys():
            self._attrs[key] = kwargs[key]
        
    def parent(self):
        return self._parent
        
    def get_data(self):
        yield self.start_tag()
        yield from self.get_inner_data()
        if not self._is_self_closing:
            yield f"</{self._tag}>"
        
    def get_inner_data(self):
        # base class does nothing
        return []
    

    def start_tag(self):
        attrs = [f"{attr}='{attr_encode(self._attrs[attr])}'" for attr in self._attrs.keys() if self._attrs[attr] is not None]
        return f"<{self._tag} {' '.join(attrs)} {'/' if self._is_self_closing else ''}>"
    
class HtmlParentElement(HtmlElement):
    def __init__(self,tag,**args):
        contents = args.get('contents',None)
        if contents:
            args.pop('contents',None)
        super().__init__(tag,**args)
        self._children = []
        self.child()
        if contents:
            if type (contents) != list:
                contents = [contents]
            for c in contents:
                if not isinstance(c,HtmlElement):
                    self.text(str(c))
                else:
                    self.child(c)
        
      
    def child(self,*children):
        for c in children:
            self._children.append(c)
            c._parent = self
        return self
        
    def get_inner_data(self):
        for child in self._children:
            yield from child.get_data()
        
    def div(self,**kwargs):
        div = HtmlParentElement('div',**kwargs)
        self.child(div)
        return div
                
        
    def h1(self,content=None,**kwargs):
        kwargs['contents'] = content
        div = HtmlParentElement('h1',**kwargs)
        self.child(div)
        return div
                
        
    def h2(self,content=None,**kwargs):
        kwargs['contents'] = content
        div = HtmlParentElement('h2',**kwargs)
        self.child(div)
        return div
                                

    def p(self,**kwargs):
        div = HtmlParentElement('p',**kwargs)
        self.child(div)
        return div
        
    def table(self,**kwargs):
        table = HtmlTableElement(**kwargs)
        self.child(table)
        return table
            
    def namevalue_table(self,name_col="Name",val_col="Value",**kwargs):
        table = NameValueTableElement(name_col,val_col,**kwargs)
        self.child(table)
        return table
    
    def text(self,text):
        elem = Text(text)
        self.child(elem)
        return self
    
    def form(self,method="POST",action=None,enctype='application/x-www-form-urlencoded',**kwargs):
        form = HtmlFormElement(method,action,enctype=enctype,**kwargs)
        self.child(form)
        return form
    
    def input(self,name,value,intype=None,**kwargs):
        kwargs['name'] = name
        kwargs['value'] = f'{value}' if value is not None else ''
        if intype is not None:
            kwargs['type'] = intype
        else:
            kwargs['type'] = 'number' if type(value) == int else 'text'
        input = HtmlElement('input',**kwargs)
        self.child(input)
        return input

    def select(self,name,selected, vals,**kwargs):
        select = HtmlSelectElement(name,selected,vals,**kwargs)
        self.child(select)
        return select
        
class HtmlSelectElement(HtmlParentElement):
    def __init__(self,name,selected,vals,**kwargs):
        kwargs['name'] = name
        super().__init__('select',**kwargs)
        self._name = name
        self._selected = selected
        self._vals = vals  
        for val in vals:
            attrs = {'value':val}
            if val == selected:
                attrs['selected'] = 'selected'
            self.child(HtmlParentElement('option',attrs=attrs,contents=val))
               
           
class HtmlFormElement(HtmlParentElement):
    def __init__(self,method="POST",action=None,enctype='application/x-www-form-urlencoded',**kwargs):
        kwargs['method'] = method
        kwargs['action'] = action
        kwargs['enctype'] = enctype
        super().__init__('form',**kwargs)
        
class HtmlTableElement(HtmlParentElement):
    def __init__(self,**kwargs):
        super().__init__('table',**kwargs)
        
    def header(self,**kwargs):
        tr = HtmlTrElement(self,is_header=True,**kwargs)
        self.child(tr)
        return tr
                
    def row(self,contents=None,**kwargs):
        tr = HtmlTrElement(self,**kwargs)
        self.child(tr)
        return tr
    
        
    def table(self,**kwargs):
        table = HtmlTableElement(**kwargs)
        self.child(table)
        return table
      
class NameValueTableElement(HtmlTableElement):
    def __init__(self,name_col,val_col,**kwargs):
        super().__init__(**kwargs)
        self._name_col = name_col
        self._val_col = val_col
        tr = self.header()
        tr.cell(name_col)
        tr.cell(val_col)
        
    def add(self,name,value,**kwargs):
        tr = self.row(**kwargs)
        tr.cell(name)
        tr.cell(value)
        return tr
        
class HtmlTrElement(HtmlParentElement):
    def __init__(self,table,is_header=False,**kwargs):
        super().__init__('tr',**kwargs)
        self._table = table
        self._is_header = is_header
        
    def cell(self,contents=None,**kwargs):
        kwargs['contents'] = contents
        td = HtmlTdElement(self,'td' if not self._is_header else 'th',**kwargs)
        self.child(td)
        return td

    
    def table(self):
        return self._table
        
class HtmlTdElement(HtmlParentElement):
    def __init__(self,tr,tag='td',**kwargs):
        super().__init__(tag,**kwargs)
        self.tr = tr
        
    def row(self):
        return self.tr.table().row()
    
class Text(HtmlElement):
    def __init__(self,text):
        super().__init__("TEXT")
        self._text = text
    
    def get_data(self):
        yield self._text
    
class HtmlHead(HtmlParentElement):
    def __init__(self,**kwargs):
        super().__init__('head',**kwargs)
        
class HtmlBody(HtmlParentElement):
    def __init__(self,**kwargs):
        super().__init__('body',**kwargs)
        
class FileElement(HtmlElement):
    def __init__(self,filepath, html_directory = '/html',buf_size=1024):
        super().__init__("FILE")
        
        self._filename = Path.join(html_directory,filepath)    
        log.info(f"File element: {self._filename}")
        self._buf_size = buf_size
    
    def get_data(self):
        try:
            with open(self._filename,'rb') as f:
                chunk = f.read(self._buf_size)
                while chunk:
                    yield chunk
                    chunk = f.read(self._buf_size)
        except Exception as ex:
            log.exception("File exception: ",exc_info=ex)
            yield ''      
        
class HtmlDoc(HtmlParentElement):
    """The root of an HTML page.  Needs to implement get_mime_type and get_data to work
    as a response content object"""
    
    def __init__(self):
        super().__init__('html')
        self._head = HtmlHead()
        self._body = HtmlBody()
        self.child(self._head)
        self.child(self._body)
        self._head.child(FileElement('hdoc_start.html'))
        self._body.child(FileElement('hdoc_menu.html'))
        self.child(FileElement('hdoc_end.html'))
        
         
    def get_mime_type(self):
        return "text/html"

    def head(self):
        return self._head
                
    def body(self):
        return self._body
    
def dumps(doc):
    return ''.join(doc.get_data())  

        
