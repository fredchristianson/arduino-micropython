import logging


log = logging.getLogger("fc.config")



class Config(dict):
    def __init__(self,vals = {},parent=None):
        super().__init__()
        self.set_values(vals)
        self._parent = parent
        
    def set_values(self,vals):
        log.never(f"Config {vals}")
        for k in vals.keys():
            log.never(f"key {k}")
            if type(vals[k]) == dict:
                log.never(f"dict")
                super().__setitem__(k,Config(vals[k],self))
            elif type(vals[k]) == list:
                log.never(f"list")
                l = []
                super().__setitem__(k,l)
                for i in range(len(vals[k])):
                    if type(vals[k][i]) == dict:
                        l.append(Config(vals[k][i]))
            else:
                super().__setitem__(k,vals[k])
        log.never(f"done")
          
    def save(self):
        self._parent.save()
        
    def get(self, key, default=None):
        if '.' in key:
            first,rest = key.split('.',1)
            child = super().get(first)
            return default if child is None else child.get(key,default)
        else:
            return super().get(key,default)

                    
    def set(self, key, value):
        levels = key.split('.')
        val = self
        for level in levels[:-1]:
            if level not in val:
                val[level] = {}
            val = val[level]
        super().__setitem__(levels[-1],value)
    
                    
    def remove(self, key):
        levels = key.split('.')
        val = self
        for level in levels[:-1]:
            if level not in val:
                val[level] = {}
            val = val[level]
        if levels[-1] in val:
            super().__delitem__(levels[-1])
            
    
    def __getitem__(self,key):
        print(f"get item {key}")
        return self.get(key)
    
    def __setitem__(self,key,val):
        self.set(key,val)
    
    
    def __delitem__(self,key):
        self.remove(key)
        
    def __getattr__(self,name):
        return self.get(name)
    
    
    def __contains__(self,key):
        return key in self.keys()
    

   
class RootConfig(Config):
    def __init__(self,values,file):
        super().__init__(values)
        self._filename= file
        
    def save(self,filename=None):
        save(self,filename or self._filename)
        
    def set_values(self,vals):
        self.clear()
        super().set_values(vals)
        
def save(config,file="/data/config.json"):
    import json
    try:
        log.debug(f"Saving config file {file}")
        with open(file,'w') as f:
            json.dump(config,f)
    except Exception as e:
        log.exception(f"Failed to save config file {file}",e)
        
def load(file="/data/config.json"):
    import json
    import gc
    try:
        log.debug(f"Loading config file {file}.  memfree: {gc.mem_free()}")
        with open(file) as f:
            vals = json.load(f)
            config = RootConfig(vals,file)
            #log.debug(f"config: {config._values} .  memfree: {gc.mem_free()}")
            #print(f"config: {config} .  memfree: {gc.mem_free()}")
            return config
    except Exception as e:
        log.exception(f"Failed to load config file {file}",exc_info=e)
        return Config()