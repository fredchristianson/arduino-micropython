import logging

log = logging.getLogger("fc.hw.pin")
class Pin:
    def __init__(self,pin):
        self._pin = pin
        
class InputPin(Pin):
    def __init__(self,pin):
        super().__init__(pin)
        log.info("create input pin %d",pin)
        
    def on_change(self):
        pass
        
    def on_set(self):
        pass
    
    def on_clear(self):
        pass
    
class OutputPin(Pin):
    def __init__(self,pin):
        super().__init__(pin)
        log.info("create output pin %d",pin)
