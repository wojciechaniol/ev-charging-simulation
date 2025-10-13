"""
EV Driver - Driver client for requesting charging sessions.

Responsibilities:
- Read CP IDs from file or use defaults
- Send charging requests to Central via Kafka
- Wait for status updates and display progress
- Handle multiple sequential requests
"""

import asyncio
import argparse
import sys
from pathlib import Path
from loguru import logger

from evcharging.common.config import DriverConfig, TOPICS
from evcharging.common.kafka import KafkaProducerHelper, KafkaConsumerHelper, ensure_topics
from evcharging.common.messages import DriverRequest, DriverUpdate, MessageStatus
from evcharging.common.utils import generate_id, utc_now


class EVDriver:
    """Driver client for requesting charging sessions."""
    
    def __init__(self, config: DriverConfig):
        self.config = config
        self.driver_id = config.driver_id
        self.producer: KafkaProducerHelper | None = None
        self.consumer: KafkaConsumerHelper | None = None
        self.pending_requests: dict[str, DriverRequest] = {}
        self.completed_requests: list[str] = []
    
    async def start(self):
        """Initialize and start the driver client."""
        logger.info(f"Starting Driver client: {self.driver_id}")
        
        # Ensure Kafka topics exist
        await ensure_topics(
            self.config.kafka_bootstrap,
            list(TOPICS.values())
        )
        
        # Initialize Kafka producer
        self.producer = KafkaProducerHelper(self.config.kafka_bootstrap)
        await self.producer.start()
        
        # Initialize Kafka consumer for updates
        self.consumer = KafkaConsumerHelper(
            self.config.kafka_bootstrap,
            topics=[TOPICS["DRIVER_UPDATES"]],
            group_id=f"driver-{self.driver_id}",
            auto_offset_reset="latest"
        )
        await self.consumer.start()
        
        logger.info(f"Driver {self.driver_id} started successfully")
    
    async def stop(self):
        """Stop the driver client gracefully."""
        logger.info(f"Stopping Driver: {self.driver_id}")
        
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        
        logger.info(f"Driver {self.driver_id} stopped")
    
    def load_cp_ids(self) -> list[str]:
        """Load CP IDs from file or return defaults."""
        if self.config.requests_file:
            try:
                path = Path(self.config.requests_file)
                if path.exists():
                    cp_ids = [
                        line.strip()
                        for line in path.read_text().splitlines()
                        if line.strip() and not line.startswith("#")
                    ]
                    logger.info(f"Loaded {len(cp_ids)} CP IDs from {self.config.requests_file}")
                    return cp_ids
                else:
                    logger.warning(f"Requests file not found: {self.config.requests_file}")
            except Exception as e:
                logger.error(f"Error loading requests file: {e}")
        
        # Default CP IDs if no file
        default_cps = ["CP-001", "CP-002", "CP-001"]
        logger.info(f"Using default CP IDs: {default_cps}")
        return default_cps
    
    async def send_request(self, cp_id: str) -> DriverRequest:
        """Send a charging request for a specific CP."""
        request_id = generate_id("req")
        
        request = DriverRequest(
            request_id=request_id,
            driver_id=self.driver_id,
            cp_id=cp_id,
            ts=utc_now()
        )
        
        self.pending_requests[request_id] = request
        
        await self.producer.send(TOPICS["DRIVER_REQUESTS"], request, key=self.driver_id)
        
        logger.info(
            f"📤 Driver {self.driver_id} requested charging at {cp_id} "
            f"(request_id: {request_id})"
        )
        
        return request
    
    async def handle_update(self, update: DriverUpdate):
        """Process status update from Central."""
        request_id = update.request_id
        
        if request_id not in self.pending_requests:
            return  # Not our request or already completed
        
        request = self.pending_requests[request_id]
        
        status_emoji = {
            MessageStatus.ACCEPTED: "✅",
            MessageStatus.DENIED: "❌",
            MessageStatus.IN_PROGRESS: "🔋",
            MessageStatus.COMPLETED: "✔️",
            MessageStatus.FAILED: "⚠️",
        }.get(update.status, "ℹ️")
        
        logger.info(
            f"{status_emoji} Driver {self.driver_id} | {update.cp_id} | "
            f"{update.status.upper()} | {update.reason or 'No details'}"
        )
        
        # Mark as completed if terminal state
        if update.status in {MessageStatus.COMPLETED, MessageStatus.DENIED, MessageStatus.FAILED}:
            self.completed_requests.append(request_id)
            del self.pending_requests[request_id]
    
    async def process_updates(self):
        """Listen for status updates from Central."""
        async for msg in self.consumer.consume():
            try:
                topic = msg["topic"]
                value = msg["value"]
                
                if topic == TOPICS["DRIVER_UPDATES"]:
                    update = DriverUpdate(**value)
                    
                    # Filter by driver ID
                    if update.driver_id == self.driver_id:
                        await self.handle_update(update)
            
            except Exception as e:
                logger.error(f"Error processing update: {e}")
    
    async def run_requests(self):
        """Execute charging requests from file."""
        cp_ids = self.load_cp_ids()
        
        if not cp_ids:
            logger.warning("No CP IDs to request")
            return
        
        for i, cp_id in enumerate(cp_ids, 1):
            logger.info(f"--- Request {i}/{len(cp_ids)} ---")
            
            # Send request
            request = await self.send_request(cp_id)
            
            # Wait for completion (or timeout)
            timeout = 30  # 30 seconds per request
            start_time = asyncio.get_event_loop().time()
            
            while request.request_id in self.pending_requests:
                await asyncio.sleep(0.5)
                
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Request {request.request_id} timed out after {timeout}s")
                    if request.request_id in self.pending_requests:
                        del self.pending_requests[request.request_id]
                    break
            
            # Wait between requests
            if i < len(cp_ids):
                logger.info(f"Waiting {self.config.request_interval}s before next request...")
                await asyncio.sleep(self.config.request_interval)
        
        logger.info(f"✨ All requests completed. Total: {len(self.completed_requests)}/{len(cp_ids)}")


async def main():
    """Main entry point for Driver client."""
    parser = argparse.ArgumentParser(description="EV Driver Client")
    parser.add_argument("--driver-id", type=str, help="Driver identifier")
    parser.add_argument("--kafka-bootstrap", type=str, help="Kafka bootstrap servers")
    parser.add_argument("--requests-file", type=str, help="File with CP IDs to request")
    parser.add_argument("--request-interval", type=float, help="Interval between requests (seconds)")
    parser.add_argument("--log-level", type=str, help="Log level")
    
    args = parser.parse_args()
    
    # Build config from args (only non-None values), env vars will fill the rest
    config_dict = {k: v for k, v in vars(args).items() if v is not None and k != 'log_level'}
    config = DriverConfig(**config_dict)
    
    # Use log level from args or config
    log_level = args.log_level if args.log_level else config.log_level
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <magenta>Driver:{extra[driver_id]}</magenta> | <level>{message}</level>",
        level=log_level
    )
    logger.configure(extra={"driver_id": config.driver_id})
    
    # Initialize driver
    driver = EVDriver(config)
    
    try:
        await driver.start()
        
        # Start update listener
        update_task = asyncio.create_task(driver.process_updates())
        
        # Run requests
        await driver.run_requests()
        
        # Wait a bit for final updates
        await asyncio.sleep(2)
        
        # Cancel update task
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await driver.stop()


if __name__ == "__main__":
    asyncio.run(main())
