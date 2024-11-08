# src/agent.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, List, Type
from queue import Queue
import asyncio
import logging
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    Basic message unit for agent communication.

    Attributes:
        type: Type of message for handler routing
        content: Main message content
        metadata: Optional additional data
        created_at: Message creation timestamp
    """
    type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now()

    def contains_keyword(self, keyword: str) -> bool:
        """Check if message contains specific keyword."""
        return keyword.lower() in self.content.lower()

    def __str__(self) -> str:
        """String representation of message."""
        return f"[{self.type}] {self.content}"


class MessageBox:
    """
    Thread-safe message queue for agent communication.

    Implements both synchronous and asynchronous interfaces for message handling.
    """

    def __init__(self):
        self._queue: Queue[Message] = Queue()
        self._lock = asyncio.Lock()

    async def put(self, message: Message) -> None:
        """
        Add message to queue asynchronously.

        Args:
            message: Message to add
        """
        async with self._lock:
            self._queue.put(message)
            logger.debug(f"Message added to queue: {message}")

    async def get(self) -> Optional[Message]:
        """
        Get next message from queue asynchronously.

        Returns:
            Message if queue not empty, None otherwise
        """
        async with self._lock:
            if not self._queue.empty():
                message = self._queue.get()
                logger.debug(f"Message retrieved from queue: {message}")
                return message
            return None

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    async def clear(self) -> None:
        """Clear all messages from the queue."""
        async with self._lock:
            while not self._queue.empty():
                self._queue.get()


class Handler(ABC):
    """Abstract base class for message handlers."""

    @abstractmethod
    async def can_handle(self, message: Message) -> bool:
        """
        Check if handler can process the message.

        Args:
            message: Message to check

        Returns:
            bool: True if handler can process message
        """
        pass

    @abstractmethod
    async def handle(self, message: Message) -> None:
        """
        Process the message.

        Args:
            message: Message to process
        """
        pass


class Behavior(ABC):
    """Abstract base class for agent behaviors."""

    def __init__(self, interval: float):
        """
        Initialize behavior with execution interval.

        Args:
            interval: Time between behavior executions in seconds
        """
        self.interval = interval
        self.last_execution = datetime.now()
        self.task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if behavior task is running."""
        return self._running and self.task is not None and not self.task.done()

    async def start(self) -> None:
        """Start the behavior task."""
        if not self.is_running:
            self._running = True
            self.task = asyncio.create_task(self._run())
            logger.debug(f"Started behavior task: {self.__class__.__name__}")

    async def stop(self) -> None:
        """Stop the behavior task."""
        self._running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.debug(f"Stopped behavior task: {self.__class__.__name__}")

    async def _run(self) -> None:
        """Internal run loop for the behavior."""
        while self._running:
            try:
                next_execution = self.last_execution.timestamp() + self.interval
                now = datetime.now().timestamp()
                if now >= next_execution:
                    message = await self.execute()
                    if message:
                        if hasattr(self, '_agent_outbox'):
                            await self._agent_outbox.put(message)
                    self.last_execution = datetime.now()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in behavior {self.__class__.__name__}: {e}")
                await asyncio.sleep(1)

    @abstractmethod
    async def execute(self) -> Optional[Message]:
        """
        Execute the behavior.

        Returns:
            Optional[Message]: Message to be sent, if any
        """
        pass


class Agent:
    """
    Base autonomous agent implementation.

    Supports:
    - Asynchronous message processing
    - Handler registration for reactive behavior
    - Behavior registration for proactive actions
    """

    def __init__(self, name: str):
        self.name = name
        self.inbox = MessageBox()
        self.outbox = MessageBox()
        self.handlers: List[Handler] = []
        self.behaviors: List[Behavior] = []
        self.running = False
        self._connection_status = {"connected_to": None}
        self._behavior_tasks: List[asyncio.Task] = []
        logger.info(f"Agent '{name}' initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        # Start the agent when entering context
        self.run_task = asyncio.create_task(self.run())
        await asyncio.sleep(0.1)  # Give agent time to start
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
        if hasattr(self, 'run_task'):
            await self.run_task  # Wait for run task to complete

    def register_handler(self, handler: Handler) -> None:
        """
        Register a new message handler.

        Args:
            handler: Handler instance to register
        """
        self.handlers.append(handler)
        logger.info(f"Handler {handler.__class__.__name__} registered with {self.name}")

    def register_behavior(self, behavior: Behavior) -> None:
        """
        Register a new behavior.

        Args:
            behavior: Behavior instance to register
        """
        behavior._agent_outbox = self.outbox  # Give behavior access to outbox
        self.behaviors.append(behavior)
        logger.info(f"Behavior {behavior.__class__.__name__} registered with {self.name}")

    async def start_behaviors(self) -> None:
        """Start all registered behaviors concurrently."""
        for behavior in self.behaviors:
            await behavior.start()
        logger.debug(f"Started all behaviors for agent {self.name}")

    async def stop_behaviors(self) -> None:
        """Stop all registered behaviors."""
        for behavior in self.behaviors:
            await behavior.stop()
        logger.debug(f"Stopped all behaviors for agent {self.name}")

    async def process_message(self, message: Message) -> None:
        """
        Process a single message through all registered handlers.

        Args:
            message: Message to process
        """
        for handler in self.handlers:
            try:
                if await handler.can_handle(message):
                    await handler.handle(message)
                    logger.debug(f"Message {message} processed by {handler.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error processing message {message} with handler {handler.__class__.__name__}: {e}")

    def connect_to(self, other_agent: 'Agent') -> None:
        """
        Register connection with another agent.

        Args:
            other_agent: Agent to connect to
        """
        self._connection_status["connected_to"] = other_agent.name
        logger.info(f"Agent '{self.name}' connected to '{other_agent.name}'")

    async def send_message(self, message: Message) -> None:
        """
        Send a message to the agent's outbox.

        Args:
            message: Message to send
        """
        await self.outbox.put(message)
        logger.debug(f"Agent '{self.name}' sent message: {message}")

    async def run(self) -> None:
        """
        Main agent loop.

        Continuously:
        1. Processes messages from inbox
        2. Executes registered behaviors
        3. Small delay to prevent CPU overload
        """
        self.running = True
        logger.info(f"Agent '{self.name}' started")

        try:
            # Start all behaviors concurrently
            await self.start_behaviors()

            while self.running:
                # Process inbox messages
                while not self.inbox.is_empty():
                    if message := await self.inbox.get():
                        await self.process_message(message)

                # Prevent CPU overload
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in agent '{self.name}' main loop: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Stop the agent gracefully.
        Ensures all pending messages are processed before stopping.
        """
        if not self.running:
            return

        logger.info(f"Agent '{self.name}' stopping...")
        self.running = False

        # Stop all behaviors
        await self.stop_behaviors()

        # Process remaining messages
        while not self.inbox.is_empty():
            if message := await self.inbox.get():
                await self.process_message(message)

        # Clear message boxes
        await self.inbox.clear()
        await self.outbox.clear()

        logger.info(f"Agent '{self.name}' stopped")

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self.running

    @property
    def connected_agent(self) -> Optional[str]:
        """Get name of connected agent, if any."""
        return self._connection_status["connected_to"]


if __name__ == "__main__":
    # Example usage
    async def example():
        async with Agent("TestAgent") as agent:
            # Register behaviors and handlers
            await agent.run()

    asyncio.run(example())