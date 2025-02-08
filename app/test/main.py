import asyncio
import network
server = None

def connect_wifi():
    print("connecting to wifi")
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect('5336iot', 'iotcorelli')
    print("connected")
    while not wifi.isconnected():
        asyncio.sleep(1000)
        print("check wifi")
    print('network config:', wifi.ifconfig())

stop_request = asyncio.Event()
    
async def handle_client(reader, writer):
    data = await reader.readline()
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")

    if message.startswith('quit'):
        # Send a response before stopping
        writer.write(b'Server is stopping...\r\n')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        stop_request.set()
    else:
        writer.write(b'got ')
        writer.write(bytearray(message, 'utf-8'))
        await writer.drain()
        writer.close()
        await writer.wait_closed()


   
async def test(stop_request):
    # occasionally stop the server to test it
    while True:
        await asyncio.sleep(1)
        print('requesting stop')
        stop_request.set()


async def main():
    global stop_request
    connect_wifi()
    stop_request.clear()
    #asyncio.create_task(test(stop_request))
    while True:
        print('starting the server')
        tcp_server =  await asyncio.start_server(handle_client, '0.0.0.0',8080)
        
        await stop_request.wait()
        stop_request.clear()
        print('stopping the server')
        tcp_server.close()
        await tcp_server.wait_closed()

asyncio.run(main())