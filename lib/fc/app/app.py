import logging;
import asyncio
from machine import WDT

log = logging.getLogger("fc.app")


class App:
    instance = None
    @classmethod
    def get(cls):
        return App.instance
    
    def __init__(self, name="<unnamed app>"):
        log.info("App created")
        App.instance = self
        self.is_set_up = False
        self.name = name
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(lambda loop,context: self.exception_handler(loop,context))
        self._debug = True
        
    def get_name(self):
        return self.name
    def exception_handler(self,loop,context):
        log.error(f"exception: {context}")

       
    async def run(self):
        # run the app
        log.debug("run app")

        asyncio.create_task(self._every_second())
        if not self._debug:
            self._wdt = WDT(timeout=60000)                 
        if not self.is_set_up:
            await self._setup()
        self.is_set_up = True
        self.on_setup_complete()
        self.initialize_devices()
        
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