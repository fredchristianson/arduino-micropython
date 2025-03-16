from asyncio import StreamWriter
import logging
log = logging.getLogger('fc.net.http.impl.chunk_writer')


class ChunkWriter:
    def __init__(self,writer: StreamWriter, size=1024):
        self.writer = writer
        self.size = size
        self.buffer = bytearray(self.size)
        self.pos = 0
        
    async def write(self,data):
        if data == None or len(data) == 0:
            return
        if type(data) == str:
            data = data.encode('utf-8')
        dlen = len(data)
        dpos = 0
        while dpos < dlen:
            self.buffer[self.pos] = data[dpos]
            self.pos += 1
            dpos += 1
            if self.pos == self.size:
                await self._write_chunk()
                
                
    async def _write_chunk(self):
        if self.pos > 0:
            log.info(f"Write chunk of 0x{self.pos:x} bytes")
            self.writer.write(f"{self.pos:x}\r\n".encode('utf-8'))
        self.writer.write(self.buffer[:self.pos])
        self.writer.write(b"\r\n")
        await self.writer.drain()
        self.pos = 0
    
    async def done(self):
        await self._write_chunk()
        log.info("wrote last chunk")
        self.writer.write(b'0\r\n\r\n')
        log.info("wrote end chunk")
        await self.writer.drain()
        