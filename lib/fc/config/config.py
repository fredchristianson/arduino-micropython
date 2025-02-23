import logging

log = logging.getLogger("fc.config")

class Config:
    def __init__(self,save_method = None):
        self._values = {}
        self.save_method = save_method
        
    def get(self, key, default=None):
        levels = key.split('.')
        val = self._values
        for level in levels:
            if level in val:
                val = val[level]
            else:
                return default
        return val
    
    def data(self):
        return self._values
    
    def get_editable(self):
        editables = []
        stack = [(self._values,[])]
        while stack:
            val,path = stack.pop()
            if isinstance(val,dict):
                for k,v in val.items():
                    stack.append((v,path+[k]))
            elif isinstance(val,list):
                for i,v in enumerate(val):
                    stack.append((v,path+[i]))
            else:
                editables.append('.'.join(path))
        return editables
    
    def list_values(self):
        editables = []
        const = []
        stack = [(self._values,[])]
        while stack:
            val,path = stack.pop()
            if isinstance(val,dict):
                if '_editable' in val and val['_editable']:
                    for k,v in val.items():
                        if not k.startswith('_'):
                            editables.append({'path':'.'.join(path)+'.'+k,'value':v})
                for k,v in val.items():
                    stack.append((v,path+[k]))
            elif isinstance(val,list):
                for i,v in enumerate(val):
                    stack.append((v,path+[f'[{i}]']))
            elif path:
                log.debug(f"path: {path}")
                const.append({'path':'.'.join(path),'value':val})
        return editables,const
    
    def update_values(self,values):
        editables = []
        vals = {item['path']:item['value'] for item in values}
        stack = [(self._values,[])]
        while stack:
            val,path = stack.pop()
            if isinstance(val,dict):
                if '_editable' in val and val['_editable']:
                    for k,v in val.items():
                        if not k.startswith('_'):
                            editables.append({'path':'.'.join(path)+'.'+k,'value':v})
                for k,v in val.items():
                    stack.append((v,path+[k]))
            elif isinstance(val,list):
                for i,v in enumerate(val):
                    stack.append((v,path+[f'[{i}]']))
            elif path:
                log.debug(f"path: {path}")
                const.append({'path':'.'.join(path),'value':val})
        return editables,const
        
def save_config(config,file="/data/config.json"):
    import json
    try:
        log.debug(f"Saving config file {file}")
        with open(file,'w') as f:
            json.dump(config._values,f)
    except Exception as e:
        log.exception(f"Failed to save config file {file}",e)
        
def load_config(file="/data/config.json"):
    import json
    try:
        log.debug(f"Loading config file {file}")
        with open(file) as f:
            save = lambda config: save_config(config,file)
            config = Config(save)
            config._values = json.load(f)
            log.debug(f"config: {config._values}")
            return config
    except Exception as e:
        log.exception(f"Failed to load config file {file}",e)
        return Config()