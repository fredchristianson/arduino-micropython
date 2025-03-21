import logging;
import asyncio
from machine import WDT
from lib.fc.modload.modload import loader
import gc

log = logging.getLogger("fc.app")

log.always("Loading app========================================")

class App:
    instance = None
    CONFIG = None
    @classmethod
    def get(cls):
        return App.instance
    
    def __init__(self, name="<unnamed app>"):
        from fc.config import load as load_config
        log.info("App created")
        App.instance = self
        self._config = load_config("/data/config.json")
        App.CONFIG = self._config
        log.never(f"config: {App.CONFIG}")
        self.is_set_up = False
        self.name = name
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(lambda loop,context: self.exception_handler(loop,context))
        self._debug = self._config.get('app.debug',False)
        gc.threshold(self._config.get('app.gc_threshold',32*1024))  # allocate when 16k have been freed
        gc.collect()

        
    def get_name(self):
        return self.name
    
    def exception_handler(self,loop,context):
        log.exception(f"exception: {context}",exc_info=context)

       
    async def run(self):
        # run the app
        log.debug("run app")

        asyncio.create_task(self._every_second())
        if not self._debug:
            self._wdt = WDT(timeout=60000)                 
        if not self.is_set_up:
            await self._setup()
        self.is_set_up = True
        self.initialize_devices()
        self.on_setup_complete()
        
        log.debug("loop forever")
        asyncio.get_event_loop().run_forever()
    
    async def _setup(self):
        # set up the app
        log.debug("setup app")
    
    async def _every_second(self):
        while True:
            log.never("every second")
            if not self._debug:
                self._wdt.feed()
            await asyncio.sleep(1)
            
    def on_setup_complete(self):
        """ derived classes can override"""
        pass
    
    def initialize_devices(self):
        """ derived classes can override"""
        pass
    