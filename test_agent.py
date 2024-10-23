
# test_agents.py

import pytest
import asyncio
from unittest.mock import Mock, patch
import time
import logging
from base_agent import BaseAgent
from concrete_agent import ConcreteAgent

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestBaseAgent(BaseAgent):
    """Test implementation of BaseAgent for testing abstract class"""

    def __init__(self, name: str):
        super().__init__(name)


class TestCases:
    """Test cases for the autonomous agent system"""

    @pytest.fixture
    def base_agent(self):
        """Fixture for base agent"""
        return TestBaseAgent("TestBaseAgent")

    @pytest.fixture
    def concrete_agent(self):
        """Fixture for concrete agent"""
        return ConcreteAgent("TestConcreteAgent")

    @pytest.mark.asyncio
    async def test_message_handler_registration(self, base_agent):
        """Test message handler registration"""
        logger.info("Starting message handler registration test")

        # Setup
        async def test_handler(message):
            pass

        # Execute
        base_agent.register_handler("test_type", test_handler)

        # Verify
        assert "test_type" in base_agent.message_handlers, "Handler not registered"
        assert base_agent.message_handlers["test_type"] == test_handler, "Wrong handler registered"

        logger.info("Message handler registration test completed")

    @pytest.mark.asyncio
    async def test_behavior_registration(self, base_agent):
        """Test behavior registration"""
        logger.info("Starting behavior registration test")

        # Setup
        async def test_behavior(state):
            pass

        # Execute
        base_agent.register_behavior(
            "test_behavior",
            test_behavior,
            interval=1.0
        )

        # Verify
        assert "test_behavior" in base_agent.behaviors, "Behavior not registered"
        assert base_agent.behaviors["test_behavior"]["interval"] == 1.0, "Wrong interval"
        assert base_agent.behaviors["test_behavior"]["function"] == test_behavior, "Wrong function"

        logger.info("Behavior registration test completed")

    @pytest.mark.asyncio
    async def test_random_message_generation(self, concrete_agent):
        """Test random message generation"""
        logger.info("Starting random message generation test")

        # Setup
        messages = []

        async def mock_send(message):
            messages.append(message)
            logger.info(f"Message captured: {message}")

        concrete_agent.send_message = mock_send

        # Execute
        await concrete_agent.random_message_behavior({})

        # Verify
        assert len(messages) == 1, "Wrong number of messages generated"
        message = messages[0]
        assert message['type'] == 'default', f"Wrong message type: {message['type']}"

        # Verify content format
        words = message['content'].split()
        assert len(words) == 2, f"Wrong number of words: {len(words)}"
        assert all(word in concrete_agent.word_list for word in words), f"Invalid words: {words}"

        logger.info("Random message generation test completed")

    @pytest.mark.asyncio
    async def test_hello_handler(self, concrete_agent):
        """Test hello message handler"""
        logger.info("Starting hello handler test")

        # Setup
        test_messages = [
            {'type': 'default', 'content': 'hello world', 'from': 'test'},
            {'type': 'default', 'content': 'world space', 'from': 'test'},
            {'type': 'default', 'content': 'HELLO UNIVERSE', 'from': 'test'},
        ]

        # Execute and verify
        for message in test_messages:
            logger.info(f"Testing message: {message}")
            with patch('builtins.print') as mock_print:
                await concrete_agent.hello_handler(message)
                if 'hello' in message['content'].lower():
                    mock_print.assert_called_once()
                    logger.info("Hello message correctly detected")
                else:
                    mock_print.assert_not_called()
                    logger.info("Non-hello message correctly ignored")

        logger.info("Hello handler test completed")

    @pytest.mark.asyncio
    async def test_behavior_timing(self, concrete_agent):
        """Test behavior execution timing"""
        logger.info("Starting behavior timing test")

        # Setup
        execution_times = []

        async def mock_behavior(state):
            current_time = time.time()
            execution_times.append(current_time)
            logger.info(f"Behavior executed at: {current_time}")

        # Register behavior with 2-second interval
        concrete_agent.register_behavior(
            "test_timing",
            mock_behavior,
            interval=2.0
        )

        # Execute
        try:
            task = asyncio.create_task(concrete_agent.execute_behaviors())
            logger.info("Started behavior execution task")

            # Wait for multiple executions
            await asyncio.sleep(7.0)

            # Graceful shutdown
            concrete_agent.is_running = False
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                logger.info("Behavior task cancelled")

            # Verify executions
            assert len(execution_times) >= 3, f"Not enough executions: {len(execution_times)}"

            # Check intervals with tolerance
            intervals = [execution_times[i] - execution_times[i - 1]
                         for i in range(1, len(execution_times))]

            for i, interval in enumerate(intervals):
                assert 1.8 <= interval <= 2.2, f"Interval {i} was {interval}s"
                logger.info(f"Interval {i}: {interval}s")

        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            raise

        logger.info("Behavior timing test completed")

    @pytest.mark.asyncio


    @pytest.mark.asyncio
    async def test_word_distribution(self, concrete_agent):
        """Test random word distribution"""
        logger.info("Starting word distribution test")

        # Setup
        words_used = {word: 0 for word in concrete_agent.word_list}
        messages = []

        async def mock_send(message):
            messages.append(message)

        concrete_agent.send_message = mock_send

        # Execute
        for i in range(1000):
            await concrete_agent.random_message_behavior({})
            if i % 100 == 0:
                logger.info(f"Generated {i} messages")

        # Count word usage
        for message in messages:
            for word in message['content'].split():
                words_used[word] += 1

        # Verify distribution
        total_words = sum(words_used.values())
        expected_frequency = total_words / len(concrete_agent.word_list)
        tolerance = 0.2 * expected_frequency

        for word, count in words_used.items():
            assert abs(count - expected_frequency) <= tolerance, \
                f"Word '{word}' frequency ({count}) deviates too much from expected ({expected_frequency})"
            logger.info(f"Word '{word}' frequency: {count}")

        logger.info("Word distribution test completed")

    @pytest.mark.asyncio
    async def test_error_handling(self, concrete_agent):
        """Test error handling in message processing and behaviors"""
        logger.info("Starting error handling test")

        # Setup
        async def failing_handler(message):
            raise Exception("Test error")

        concrete_agent.register_handler("error", failing_handler)

        # Test message handling error
        with patch('builtins.print') as mock_print:
            logger.info("Testing error handling in message processing")
            task = asyncio.create_task(concrete_agent.process_messages())
            message = {'type': 'error', 'content': 'test'}
            await concrete_agent.inbox.put(message)
            await asyncio.sleep(0.1)

            concrete_agent.is_running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            mock_print.assert_called()
            logger.info("Error was handled correctly")

        logger.info("Error handling test completed")


if __name__ == "__main__":
    pytest.main(["-v"])
