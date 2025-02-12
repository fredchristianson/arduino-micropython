import logging;
import asyncio


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
        
    def get_name(self):
        return self.name
    def exception_handler(self,loop,context):
        log.error(f"exception: {context}")

       
    async def run(self):
        # run the app
        log.debug("run app")
        if not self.is_set_up:
            await self._setup()
        self.is_set_up = True
        
        log.debug("loop forever")
        asyncio.get_event_loop().run_forever()
    
    async def _setup(self):
        # set up the app
        log.debug("setup app")
    
