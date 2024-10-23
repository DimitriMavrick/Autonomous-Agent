
import unittest
import asyncio
from smart_agent import SmartAgent


class TestAgentCharacteristics(unittest.TestCase):

    def test_asynchronous_communication(self):
        """Test asynchronous messaging"""

        async def run_test():
            agent = SmartAgent("TestAgent", "human")

            # Test sending doesn't block
            send_time = time.time()
            await agent.send_message({'content': 'test'})
            time_diff = time.time() - send_time
            self.assertLess(time_diff, 0.1)  # Should be nearly instant

        asyncio.run(run_test())

    def test_reactiveness(self):
        """Test reactive behavior"""

        async def run_test():
            agent = SmartAgent("TestAgent", "human")

            # Send message and check reaction
            message = {'type': 'inquiry', 'content': 'help'}
            await agent.handle_customer_inquiry(message)

            # Check if response was generated
            response = await agent.outbox.get()
            self.assertIn('response', response['type'])

        asyncio.run(run_test())

    def test_proactiveness(self):
        """Test proactive behavior"""

        async def run_test():
            agent = SmartAgent("TestAgent", "thing")

            # Start device status behavior
            task = asyncio.create_task(agent.device_status_behavior())

            # Check if messages are generated without prompting
            message = await agent.outbox.get()
            self.assertIn('status', message['type'])

            # Cleanup
            agent.is_running = False
            task.cancel()

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()