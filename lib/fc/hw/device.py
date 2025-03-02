
from .led import NeoPixelStrip
from .motion import CompositeMotion, Motion
import logging

log = logging.getLogger("fc.hw.device")

class Device:
    def __init__(self,name,id):
        log.info("create device %s (%d)",name,id)
        self._name = name
        self._id = id
        self._components = []
        
    def add(self,component):
        self._components.append(component)
        
def create_leds(definition):
    if definition is None:
        return []
    elif type(definition) is not list:
        definition = [definition]
    leds = []
    for details in definition:
        name = details.get("name","Unnamed LED")
        id = details.get("id",hash(name))
        pin = details.get("pin",hash(name))
        count = details.get("count",hash(name))
        led = NeoPixelStrip(name,id,pin,count)
        leds.append(led)
    return leds
            
        
def create_motion_sensors(definition):
    if definition is None:
        return []
    elif type(definition) is not list:
        definition = [definition]
    sensors = []
    for details in definition:
        log.debug(f"create motion sensor {details}")
        name = details.get("name","Unnamed LED")
        id = details.get("id",hash(name))
        pin = details.get("pin",None)
        if pin is not None:
            log.debug("pin %s",pin)
            sensor = Motion(pin,name,id)
            sensors.append(sensor)
        else:
            component_ids = details.get("compose",[])
            if component_ids:
                sensor = CompositeMotion(name,id,component_ids)
                sensors.append(sensor)
            
    for sensor in sensors:
        if isinstance(sensor,CompositeMotion):
            for component_id in sensor._component_ids:
                for component in sensors:
                    if component._id == component_id:
                        sensor.add(component)
    return sensors
            
            
        
def create_devices(definition):
    if definition is None:
        return []
    elif type(definition) is not list:
        definition = [definition]
    devices = []
    for details in definition:
        name = details.get("name","Unnamed Device")
        id = details.get("id",hash(name))
        device = Device(name,id)
        devices.append(device)
        for led in details.get("leds",[]):
            device.add(create_leds(led))
        for motion in details.get("motion_sensors",[]):
            device.add(create_motion_sensors(motion))      
    return devices                  
