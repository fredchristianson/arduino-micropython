from fc.app import NetApp
import logging

log = logging.getLogger(("HttpTest"))


class HttpTestApp(NetApp):
    def __init__(self):
        super().__init__("HttpTest")
        log.info("App created")