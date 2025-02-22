# boot.py -- run on boot-up
#
# data/logging.json is automatically loaded
#import logging
#logging.config()


from http_test import HttpTestApp
import asyncio


app = HttpTestApp()
asyncio.run(app.run())