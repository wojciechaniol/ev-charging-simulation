"""
TCP Message Framing Protocol Implementation.
Implements <STX><DATA><ETX><LRC> framing for reliable message transmission.

Format:
- STX (0x02): Start of text marker
- DATA: Message payload (JSON or text)
- ETX (0x03): End of text marker
- LRC: Longitudinal Redundancy Check (XOR of all DATA bytes)
"""

from typing import Optional


# Control characters
STX = b'\x02'  # Start of Text
ETX = b'\x03'  # End of Text


def calculate_lrc(data: bytes) -> int:
    """
    Calculate Longitudinal Redundancy Check.
    LRC is the XOR of all data bytes.
    
    Args:
        data: Bytes to calculate LRC for
        
    Returns:
        LRC value as integer
    """
    lrc = 0
    for byte in data:
        lrc ^= byte
    return lrc


def frame_message(message: str) -> bytes:
    """
    Frame a message with STX, ETX, and LRC.
    
    Format: <STX><DATA><ETX><LRC>
    
    Args:
        message: String message to frame
        
    Returns:
        Framed message as bytes
    """
    data = message.encode('utf-8')
    lrc = calculate_lrc(data)
    
    return STX + data + ETX + bytes([lrc])


def parse_framed_message(buffer: bytes) -> tuple[Optional[str], bytes]:
    """
    Parse a framed message from a buffer.
    
    Args:
        buffer: Buffer containing potentially framed messages
        
    Returns:
        Tuple of (message, remaining_buffer)
        - message is None if no complete frame found
        - remaining_buffer contains unparsed bytes
    """
    # Look for STX
    stx_idx = buffer.find(STX)
    if stx_idx == -1:
        # No STX found, discard buffer up to this point
        return None, buffer[-100:]  # Keep last 100 bytes in case STX was split
    
    # Look for ETX after STX
    search_start = stx_idx + 1
    etx_idx = buffer.find(ETX, search_start)
    
    if etx_idx == -1:
        # No complete frame yet
        return None, buffer[stx_idx:]
    
    # Check if we have the LRC byte
    if len(buffer) < etx_idx + 2:
        # LRC not received yet
        return None, buffer[stx_idx:]
    
    # Extract components
    data = buffer[stx_idx + 1:etx_idx]
    received_lrc = buffer[etx_idx + 1]
    
    # Verify LRC
    calculated_lrc = calculate_lrc(data)
    if calculated_lrc != received_lrc:
        # LRC mismatch - frame corrupted
        # Discard this frame and continue searching
        remaining = buffer[etx_idx + 2:]
        return parse_framed_message(remaining)
    
    # Valid frame found
    try:
        message = data.decode('utf-8')
        remaining = buffer[etx_idx + 2:]
        return message, remaining
    except UnicodeDecodeError:
        # Invalid UTF-8 - discard frame
        remaining = buffer[etx_idx + 2:]
        return parse_framed_message(remaining)


class MessageFramer:
    """Helper class for framing/parsing messages in a stateful way."""
    
    def __init__(self):
        self.buffer = b''
    
    def add_data(self, data: bytes):
        """Add received data to internal buffer."""
        self.buffer += data
        
        # Limit buffer size to prevent memory issues
        if len(self.buffer) > 10000:
            # Keep only last 1000 bytes
            self.buffer = self.buffer[-1000:]
    
    def get_message(self) -> Optional[str]:
        """
        Try to extract a complete message from the buffer.
        
        Returns:
            Message string if a complete frame is available, None otherwise
        """
        message, self.buffer = parse_framed_message(self.buffer)
        return message
    
    def get_all_messages(self) -> list[str]:
        """
        Extract all complete messages from the buffer.
        
        Returns:
            List of message strings
        """
        messages = []
        while True:
            message = self.get_message()
            if message is None:
                break
            messages.append(message)
        return messages


# Example usage
if __name__ == "__main__":
    # Frame a message
    original = "Hello, TCP!"
    framed = frame_message(original)
    print(f"Original: {original}")
    print(f"Framed: {framed.hex()}")
    
    # Parse it back
    message, remaining = parse_framed_message(framed)
    print(f"Parsed: {message}")
    print(f"Remaining: {remaining}")
    
    # Test with multiple messages
    msg1 = frame_message("First")
    msg2 = frame_message("Second")
    combined = msg1 + msg2
    
    framer = MessageFramer()
    framer.add_data(combined)
    messages = framer.get_all_messages()
    print(f"Multiple messages: {messages}")
