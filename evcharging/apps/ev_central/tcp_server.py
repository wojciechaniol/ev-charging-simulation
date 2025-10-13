"""
TCP Control Server for EV Central.
Provides a TCP socket interface for control plane operations.
"""

import asyncio
from loguru import logger


class TCPControlServer:
    """Simple TCP server for control plane operations."""
    
    def __init__(self, port: int):
        self.port = port
        self.server = None
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connections."""
        addr = writer.get_extra_info('peername')
        logger.info(f"TCP client connected: {addr}")
        
        try:
            # TODO: Implement command protocol with <STX><DATA><ETX><LRC> framing
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                logger.debug(f"Received from {addr}: {message}")
                
                # Echo response for now
                response = f"ACK: {message}\n"
                writer.write(response.encode('utf-8'))
                await writer.drain()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling TCP client {addr}: {e}")
        finally:
            logger.info(f"TCP client disconnected: {addr}")
            writer.close()
            await writer.wait_closed()
    
    async def start(self):
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"TCP Control Server listening on {addr}")
        
        async with self.server:
            await self.server.serve_forever()
