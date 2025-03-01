import logging

log = logging.getLogger("fc.hw.led")

class LedStrip:
    def __init__(self,name,id,led_count):
        log.info("create LED %s (%d)",name,id)
        
        self._name = name
        self._id = id
        self._led_count = led_count

    def __str__(self):
        return f"{self.__class__.__name__} {self._name} ({self._id}) with {self._led_count} LEDs on pin {self._pin}"    
class NeoPixelStrip(LedStrip):
    def __init__(self,name,id,pin,led_count):
        super().__init__(name,id,led_count)
        self._pin = pin
        



