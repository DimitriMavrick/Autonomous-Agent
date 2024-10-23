
import asyncio
import time
from base_agent import BaseAgent

class SmartAgent(BaseAgent):
    """
    This agent represents different types of entities:
    1. Human: Customer Service Representative
    2. Organization: Weather Service
    3. Thing: Smart Device
    """
    def __init__(self, name: str, entity_type: str):
        super().__init__(name)
        self.entity_type = entity_type
        self.state = {}

    # Human-like behavior (Customer Service)
    async def handle_customer_inquiry(self, message):
        if self.entity_type == "human":
            response = {
                'type': 'response',
                'content': f"Hello! This is {self.name}, how can I help you?"
            }
            await self.send_message(response)

    # Organization-like behavior (Weather Service)
    async def weather_update_behavior(self):
        if self.entity_type == "organization":
            while self.is_running:
                update = {
                    'type': 'weather',
                    'content': f"Weather update from {self.name}"
                }
                await self.send_message(update)
                await asyncio.sleep(5)

    # Thing-like behavior (Smart Device)
    async def device_status_behavior(self):
        if self.entity_type == "thing":
            while self.is_running:
                status = {
                    'type': 'status',
                    'content': f"Device {self.name} is operational"
                }
                await self.send_message(status)
                await asyncio.sleep(3)
