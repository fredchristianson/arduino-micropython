import asyncio
import gc
import network

station = None
ap = None


def setup_wifi():
    print('setup wifi')
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    print('wifi access point running')  
    

def setup_server():
    print('setup server')
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    print('server access point running')    

async def main():
    print('Running')
    print(f'mem {gc.mem_free()}')
    
    setup_wifi()
    
    setup_server()


def run():
    asyncio.run(main())





