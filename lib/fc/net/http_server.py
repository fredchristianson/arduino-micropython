import logging;

log = logging.getLogger("fc.net.http-server")

class HttpServer:
    def __init__(self):
        super().__init__()
        log.info("HttpServer created")
        
    def setup(self):
        # set up the app
        log.debug("setup")
        pass
        
    def run(self):
        # run the app
        log.debug("run")
        pass