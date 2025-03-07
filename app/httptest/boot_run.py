# boot.py -- run on boot-up
#
# data/logging.json is automatically loaded
print("boot config logging")
import logging

from http_test import HttpTestApp
app = HttpTestApp()


# Run the connection function
if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run())