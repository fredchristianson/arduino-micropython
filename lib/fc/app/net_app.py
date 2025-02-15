import logging;
import asyncio
from .app import App



log = logging.getLogger("fc.netapp")


class NetApp(App):

    def __init__(self, name="<unnamed app>"):
        super().__init__(name)
        log.info(f"NetApp created {name}")
        self.wifi = None
   
    def get_wifi(self): 
        return self.wifi
        
    async def _setup(self):
        from fc.net import NetTime        
        # set up the app
        log.debug("setup app")
        await self._setup_wifi()
        log.debug("wifi setup done")
        await NetTime.update()
        log.debug("Time setup running")
        self.is_set_up = True
    
    async def _setup_wifi(self):
        from fc.net import Wifi
        self.wifi =  Wifi()
        await self.wifi.connect()   
        

        
