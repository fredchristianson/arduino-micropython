
from umqtt.robust import MQTTClient
from machine import unique_id
import logging

log = logging.getLogger('fc.net.mqtt')

MQTT_ID = ":".join("{:02x}".format(b) for b in unique_id())

async def mqtt_connect():
    pass

async def mqtt_check_connection():
    pass

