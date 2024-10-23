
import random
import asyncio
from base_agent import BaseAgent

class ConcreteAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.word_list = [
            "hello", "sun", "world", "space", "moon",
            "crypto", "sky", "ocean", "universe", "human"
        ]

        # Register message handlers
        self.register_handler('default', self.hello_handler)

        # Register behaviors with exact 2-second interval
        self.register_behavior(
            behavior_name='random_messages',
            behavior=self.random_message_behavior,
            interval=2.0
        )

    async def hello_handler(self, message: dict):
        """Filters messages for the keyword 'hello'"""
        if "hello" in message.get('content', '').lower():
            print(f"{message}")

    async def random_message_behavior(self, state: dict):
        """Generates random two-word messages"""
        # Generate random two-word combination
        words = random.sample(self.word_list, 2)
        message = {
            'type': 'default',
            'content': f"{words[0]} {words[1]}",
            'from': self.name
        }
        await self.send_message(message)

    # Remove the execute_behaviors override