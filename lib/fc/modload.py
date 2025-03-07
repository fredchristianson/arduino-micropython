import sys
import gc

# todo: add ref count to avoid removing from sys.modules too soon.
#       modules can be loaded/unlosded in a loop that calls another function that uses a loader()

class loader:
    def __init__(self, *module_names):
        print(f'load {module_names}')
        self.module_names = module_names 
        self.modules = []

    def __enter__(self):
        # Load the module when entering the context
        for name in self.module_names:
            # need to pass fromlist (3rd arg) but has to be by position
            mod = __import__(name,None,None,('*',))
            self.modules.append(mod)
        return self.modules[0] if len(self.modules) == 1 else self.modules

    def __exit__(self, exc_type, exc_value, traceback):
        # Remove the module from sys.modules when exiting
        
        for name in self.module_names:
            # don't remove logging or modload from sys.modules. remove everything else up the module hierarchy
            remove = [mod for mod in sys.modules.keys() if name.startswith(mod) and name != 'logging' and name != 'modload']
            for r in remove:
                del sys.modules[r]
            # Note: The module may still linger in memory until garbage collected
        self.modules = []
        gc.collect()