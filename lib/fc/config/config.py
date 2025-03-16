import logging


log = logging.getLogger("fc.config")



class Config(dict):
    def __init__(self,vals = {},parent=None,depth=0):
        super().__init__()
        tabs = '\t\t\t\t\t\t\t\t'[0:depth]
        log.debug(f"{tabs}Config {vals}")
        self._values = vals
        self._parent = parent
        for k in self._values.keys():
            log.debug(f"{tabs}key {k}")
            if type(self._values[k]) == dict:
                log.debug(f"{tabs}dict")
                self._values[k] = Config(self._values[k],self,depth+1)
            elif type(self._values[k]) == list:
                log.debug(f"{tabs}list")
                for i in range(len(self._values[k])):
                    if type(self._values[k][i]) == dict:
                        self._values[k][i] = Config(self._values[k][i],self,depth+1)
        log.debug(f"{tabs}done")
          
    def save(self):
        self._parent.save()
        
    def get(self, key, default=None):
        levels = key.split('.')
        val = self._values
        for level in levels:
            if level in val:
                val = val[level]
            else:
                return default
        return val
                    
    def set(self, key, value):
        levels = key.split('.')
        val = self._values
        for level in levels[:-1]:
            if level not in val:
                val[level] = {}
            val = val[level]
        val[levels[-1]] = value
    
                    
    def remove(self, key):
        levels = key.split('.')
        val = self._values
        for level in levels[:-1]:
            if level not in val:
                val[level] = {}
            val = val[level]
        if levels[-1] in val:
            del val[levels[-1]]
            
    def keys(self):
        return self._values.keys()
    
    def __getitem__(self,key):
        print(f"get item {key}")
        return self.get(key)
    
    def __setitem__(self,key,val):
        self.set(key,val)
    
    
    def __delitem__(self,key):
        self.remove(key)
        
    def __getattr__(self,name):
        return self.get(name)
    
    def __iter__(self):
        print("iter)")
        return iter(self._values)
    
    def __len__(self):
        return len(self._values)
    
    def __contains__(self,key):
        return key in self._values  
    
    def __repr__(self):
        return repr(self._values)
    
    def __str__(self):
        return f"{self._values}"
   
class RootConfig(Config):
    def __init__(self,values,file):
        super().__init__(values)
        self._filename= file
        
    def save(self,filename=None):
        save(self,filename or self._filename)
        
def save(config,file="/data/config.json"):
    import json
    try:
        log.debug(f"Saving config file {file}")
        with open(file,'w') as f:
            json.dump(config._values,f)
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
            print(f"config: {config._values} .  memfree: {gc.mem_free()}")
            return config
    except Exception as e:
        log.exception(f"Failed to load config file {file}",exc_info=e)
        return Config()