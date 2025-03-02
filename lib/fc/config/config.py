import logging
import json

log = logging.getLogger("fc.config")

class Config:
    def __init__(self,save_method = None):
        self._values = {}
        self.save_method = save_method
        
    def to_json(self):
        return json.dumps(self._values or {})
    
    def from_json(self,json_text,save=True):
        self._values = json.loads(json_text)
        if save and self.save_method:
            self.save_method(self)
            
    def get(self, key, default=None):
        levels = key.split('.')
        val = self._values
        for level in levels:
            if level in val:
                val = val[level]
            else:
                return default
        return val
    
    def update(self,values,save=True):
        """values is a dictionary of json path to value.  Values are updated or added to the config. 

        Args:
            values (dict): json path to value
            save (bool, optional): if true the config is saved if there is a save method. Defaults to True.
        """
        for path,value in values.items():
            self.set(path,value,save=False)
        if save and self.save_method:
            self.save_method(self)
                    
    def set(self, key, value, save=True):
        levels = key.split('.')
        val = self._values
        for level in levels[:-1]:
            if level not in val:
                val[level] = {}
            val = val[level]
        val[levels[-1]] = value
        if save and self.save_method:
            self.save_method(self)
    
    def data(self):
        return self._values

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
                            editables.append({'path':'.'.join(path)+'.'+k,'value':v,'definition': val})
                for k,v in val.items():
                    stack.append((v,path+[k]))
            elif isinstance(val,list):
                for i,v in enumerate(val):
                    stack.append((v,path+[f'[{i}]']))
            elif path:
                
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
    import gc
    try:
        log.debug(f"Loading config file {file}.  memfree: {gc.mem_free()}")
        with open(file) as f:
            save = lambda config: save_config(config,file)
            config = Config(save)
            config._values = json.load(f)
            log.debug(f"config: {config._values} .  memfree: {gc.mem_free()}")
            return config
    except Exception as e:
        log.exception(f"Failed to load config file {file}",e)
        return Config()