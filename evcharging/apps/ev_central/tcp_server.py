"""
TCP Control Server for EV Central.
Provides a TCP socket interface for control plane operations with message framing.
"""

import asyncio
from loguru import logger

from evcharging.common.framing import MessageFramer, frame_message


class TCPControlServer:
    """Simple TCP server for control plane operations."""
    
    def __init__(self, port: int):
        self.port = port
        self.server = None
        self._running = False
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connections with message framing."""
        addr = writer.get_extra_info('peername')
        logger.info(f"TCP client connected: {addr}")
        
        framer = MessageFramer()
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Add data to framer
                framer.add_data(data)
                
                # Process all complete messages
                messages = framer.get_all_messages()
                for message in messages:
                    logger.debug(f"Received from {addr}: {message}")
                    
                    # Process command (simple echo for now)
                    response_text = f"ACK: {message}"
                    response_framed = frame_message(response_text)
                    
                    writer.write(response_framed)
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
        self._running = True
        
        # Serve until stopped
        try:
            async with self.server:
                await self.server.serve_forever()
        except asyncio.CancelledError:
            logger.info("TCP server cancelled")
    
    async def stop(self):
        """Stop the TCP server gracefully."""
        logger.info("Stopping TCP Control Server...")
        self._running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("TCP Control Server stopped")
