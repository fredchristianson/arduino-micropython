# boot.py -- run on boot-up


import logging
logging.basicConfig(level=logging.DEBUG,force=True)

from  main import App

app = App("test app")
app.run()
