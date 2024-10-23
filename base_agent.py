
import asyncio
import time
from typing import Dict, Callable, Any
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Base agent with:
    - Message type handler registration
    - State/time-based behavior registration
    """

    def __init__(self, name: str):
        self.name = name
        self.is_running = True

        # Communication channels
        self.inbox = asyncio.Queue()
        self.outbox = asyncio.Queue()

        # Registration systems
        self.message_handlers: Dict[str, Callable] = {}  # Type-specific handlers
        self.behaviors: Dict[str, Dict] = {}  # Behaviors with state

        # Internal state tracking
        self.internal_state: Dict[str, Any] = {}
        self.last_behavior_time: Dict[str, float] = {}

    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for a specific message type.

        Args:
            message_type: Type of message this handler processes
            handler: Async function(message) to handle this type
        """
        self.message_handlers[message_type] = handler
        print(f"{self.name} registered handler for message type: {message_type}")

    def register_behavior(self,
                          behavior_name: str,
                          behavior: Callable,
                          interval: float = None,
                          initial_state: Dict[str, Any] = None):
        """
        Register a proactive behavior with timing and state.

        Args:
            behavior_name: Name of the behavior
            behavior: Async function to execute
            interval: Time interval between executions (if time-based)
            initial_state: Initial state for this behavior
        """
        self.behaviors[behavior_name] = {
            'function': behavior,
            'interval': interval,
            'state': initial_state or {}
        }
        self.last_behavior_time[behavior_name] = time.time()
        self.internal_state[behavior_name] = initial_state or {}
        print(f"{self.name} registered behavior: {behavior_name}")

    async def process_messages(self):
        """Process incoming messages based on their type."""
        while self.is_running:
            try:
                # Get and identify message type
                message = await self.inbox.get()
                message_type = message.get('type', 'default')

                # Find and execute appropriate handler
                if handler := self.message_handlers.get(message_type):
                    await handler(message)
                else:
                    print(f"{self.name}: No handler for message type: {message_type}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"{self.name} - Error processing message: {e}")

    async def execute_behaviors(self):
        """Execute behaviors based on their timing/state conditions."""
        while self.is_running:
            try:
                current_time = time.time()

                # Check each behavior
                for name, behavior_info in self.behaviors.items():
                    behavior_func = behavior_info['function']
                    interval = behavior_info['interval']
                    state = behavior_info['state']
                    last_time = self.last_behavior_time[name]

                    # Execute if:
                    # 1. It's time-based and interval has passed, or
                    # 2. It's state-based and conditions are met
                    if (interval is not None and
                            current_time - last_time >= interval):
                        await behavior_func(state)
                        self.last_behavior_time[name] = current_time

                await asyncio.sleep(0.1)  # Prevent CPU overuse

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"{self.name} - Error in behaviors: {e}")

    async def send_message(self, message: Dict[str, Any]):
        """Send a message to outbox."""
        await self.outbox.put(message)
        print(f"{self.name} sent: {message}")

    async def run(self):
        """Run message processing and behaviors concurrently."""
        try:
            await asyncio.gather(
                self.process_messages(),
                self.execute_behaviors()
            )
        except asyncio.CancelledError:
            self.is_running = False
