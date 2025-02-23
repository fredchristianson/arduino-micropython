# boot.py -- run on boot-up
#
# data/logging.json is automatically loaded
#import logging
#logging.config()


# from http_test import HttpTestApp
# import asyncio


# app = HttpTestApp()
# asyncio.run(app.run())

import network
import time

# WiFi credentials
SSID = "5336iot"      # Replace with your WiFi network name
PASSWORD = "iotcorelli"    # Replace with your WiFi password

def connect_wifi():
    # Create a station interface
    wlan = network.WLAN(network.STA_IF)
    
    # Activate the interface
    wlan.active(True)
    
    # Connect to the WiFi network
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        
        # Wait for connection with timeout
        timeout = 10  # seconds
        start_time = time.time()
        
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                print("Connection timeout!")
                return False
            time.sleep(1)
        
        # Connection successful
        print("Connected to WiFi!")
        print("Network config:", wlan.ifconfig())
        return True
    else:
        print("Already connected!")
        print("Network config:", wlan.ifconfig())
        return True

# Run the connection function
if __name__ == "__main__":
    connect_wifi()