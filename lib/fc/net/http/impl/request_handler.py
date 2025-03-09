import asyncio
import logging
log = logging.getLogger('fc.net.http.http_handler')


async def http_request_handler(reader, writer):
    log.info('new connection')
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    log.info('received %r from %r', message, addr)
