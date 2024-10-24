
import unittest
import time
import queue
from agent import Agent


class TestAgent(unittest.TestCase):
    """Unit tests for Agent"""

    def setUp(self):
        """Create test agent"""
        self.agent = Agent("TestAgent")

    def test_handler_registration(self):
        """Test handler registration"""

        def test_handler(message):
            print(f"Test handler: {message}")

        # Register a handler
        self.agent.register_handler('test', test_handler)
        # Check it was registered
        self.assertIn('test', self.agent.message_handlers)

    def test_behavior_registration(self):
        """Test behavior registration"""

        def test_behavior():
            print("Test behavior running")

        # Register a behavior
        self.agent.register_behavior('test', test_behavior)
        # Check it was registered
        self.assertIn('test', self.agent.behaviors)

    def test_hello_handler(self):
        """Test hello message handling"""
        # Test with hello message
        hello_message = {'content': 'hello world'}
        result = self.agent.hello_handler(hello_message)
        self.assertTrue(result)

        # Test with non-hello message
        other_message = {'content': 'hi world'}
        result = self.agent.hello_handler(other_message)
        self.assertFalse(result)

    def test_message_generation(self):
        """Test random message generation"""
        message = self.agent.generate_message()

        # Check message format
        self.assertIn('type', message)
        self.assertIn('content', message)
        self.assertIn('from', message)

        # Check content
        words = message['content'].split()
        self.assertEqual(len(words), 2)
        self.assertTrue(all(word in self.agent.words for word in words))


class TestAgentIntegration(unittest.TestCase):
    """Integration tests"""

    def test_two_agents_communication(self):
        """Test two agents working together"""
        # Create agents
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")

        # Connect them
        agent1.outbox = agent2.inbox
        agent2.outbox = agent1.inbox

        # Send a test message
        test_message = {
            'type': 'default',
            'content': 'hello test',
            'from': 'Agent1'
        }
        agent1.outbox.put(test_message)

        # Check that agent2 received it
        received = agent2.inbox.get()
        self.assertEqual(received, test_message)

        # Start agents
        agent1.start()
        agent2.start()

        # Let them run briefly
        time.sleep(4)

        # Stop agents
        agent1.stop()
        agent2.stop()


if __name__ == '__main__':
    unittest.main()
