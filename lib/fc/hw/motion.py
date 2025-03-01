
from .pin import InputPin
import logging

log = logging.getLogger("fc.hw.motion")

class Motion(InputPin):
    def __init__(self,pin,name="Motion", id=1000):
        super().__init__(pin)
        log.info("create motion %s (%d)",name,id)
        
        self._name = name
        self._id = id
        
    def __str__(self):
        return f"Motion {self._name} ({self._id})  on pin {self._pin}"
        
class CompositeMotion:
    def __init__(self,name,id,component_ids):
        log.info("create composite motion %s (%d)",name,id)
        self._components = []
        self._name = name
        self._id = id
        self._component_ids = component_ids
        
        
    def add(self,component):
        log.info("Add motion %s to composite motion %s",component._name,self._name)
        self._components.append(component)
        return self
        
    def __str__(self):
        return f"CompositeMotion {self._name} ({self._id})"