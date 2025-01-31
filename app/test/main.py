from time import sleep
import json
import logging

log = logging.getLogger("main")
log.setLevel(logging.DEBUG)

print("Test main")
def run(name):
    a=1
    while True:
        log.debug(f"log {name}={a}")
        a += 1
        sleep(1)
        
class App:
    def __init__(self,n):
        self.name = n
    
    def run(self):
        run(self.name)
        
#app = App("test")

with open("config.json") as file:
    config = json.load(file)
    log.info(config)
    
log.info("test log message")