import logging;
import asyncio

from fc.net import Wifi

log = logging.getLogger("fc.app")

THE_APP = None

class App:
    def __init__(self):
        log.info("App created")
        THE_APP = self
        self.is_set_up = False
        self.wifi = None
        
    def get_wifi(self): 
        return self.wifi
       
    async def run(self):
        # run the app
        log.debug("run app")
        if not self.is_set_up:
            await self._setup()
        
        log.debug("loop forever")
        asyncio.get_event_loop().run_forever()
    
    async def _setup(self):
        # set up the app
        log.debug("setup app")
        await self._setup_wifi()
        self.is_set_up = True
    
    async def _setup_wifi(self):
        self.wifi =  Wifi()
        await self.wifi.connect()   