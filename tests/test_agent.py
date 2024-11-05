# tests/test_agent.py

import pytest
import asyncio
from datetime import datetime
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import Message, MessageBox, Agent, Behavior, Handler

# Rest of your test code remains the same...

# Setup pytest for async
pytest_plugins = ('pytest_asyncio',)


# Test Message Class
def test_message_creation():
    """Test basic message creation and attributes"""
    message = Message(
        type="test",
        content="test content",
        metadata={"key": "value"}
    )

    assert message.type == "test"
    assert message.content == "test content"
    assert message.metadata == {"key": "value"}
    assert isinstance(message.created_at, datetime)


def test_message_keyword_detection():
    """Test message keyword detection functionality"""
    message = Message(type="test", content="Hello World")

    assert message.contains_keyword("hello")
    assert message.contains_keyword("HELLO")
    assert message.contains_keyword("world")
    assert not message.contains_keyword("python")


def test_message_string_representation():
    """Test message string representation"""
    message = Message(type="test", content="test content")
    assert str(message) == "[test] test content"


# Test MessageBox Class
@pytest.mark.asyncio
async def test_message_box_operations():
    """Test MessageBox put and get operations"""
    box = MessageBox()
    message = Message(type="test", content="test content")

    # Test empty box
    assert box.is_empty()

    # Test put operation
    await box.put(message)
    assert not box.is_empty()

    # Test get operation
    received = await box.get()
    assert received == message
    assert box.is_empty()


@pytest.mark.asyncio
async def test_message_box_clear():
    """Test MessageBox clear functionality"""
    box = MessageBox()

    # Add multiple messages
    for i in range(3):
        await box.put(Message(type="test", content=f"message {i}"))

    assert not box.is_empty()
    await box.clear()
    assert box.is_empty()


# Test Agent Class
class TestBehavior(Behavior):
    """Test behavior implementation"""

    def __init__(self):
        super().__init__(interval=0.1)
        self.execution_count = 0

    async def execute(self):
        self.execution_count += 1
        return Message(type="test", content=f"behavior {self.execution_count}")


class TestHandler(Handler):
    """Test handler implementation"""

    def __init__(self):
        self.handled_messages = []

    async def can_handle(self, message):
        return True

    async def handle(self, message):
        self.handled_messages.append(message)


@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent initialization"""
    agent = Agent("TestAgent")
    assert agent.name == "TestAgent"
    assert not agent.is_running
    assert agent.inbox is not None
    assert agent.outbox is not None
    assert len(agent.handlers) == 0
    assert len(agent.behaviors) == 0


@pytest.mark.asyncio
async def test_agent_behavior_registration():
    """Test behavior registration and execution"""
    agent = Agent("TestAgent")
    behavior = TestBehavior()

    agent.register_behavior(behavior)
    assert len(agent.behaviors) == 1

    # Run agent briefly to test behavior execution
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.3)  # Allow some behaviors to execute
    await agent.stop()
    await agent_task

    assert behavior.execution_count > 0


@pytest.mark.asyncio
async def test_agent_handler_registration():
    """Test handler registration and message processing"""
    agent = Agent("TestAgent")
    handler = TestHandler()

    agent.register_handler(handler)
    assert len(agent.handlers) == 1

    # Test message processing
    message = Message(type="test", content="test message")
    await agent.process_message(message)

    assert len(handler.handled_messages) == 1
    assert handler.handled_messages[0] == message


@pytest.mark.asyncio
async def test_agent_lifecycle():
    """Test agent start/stop lifecycle"""
    agent = Agent("TestAgent")

    # Start the agent
    agent_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.1)  # Give agent time to start
    assert agent.is_running

    # Stop the agent
    await agent.stop()
    await agent_task  # Wait for agent task to complete
    assert not agent.is_running

    # Test async context manager separately
    async with Agent("ContextAgent") as context_agent:
        assert context_agent.is_running
        await asyncio.sleep(0.1)  # Allow some time for agent to run

    # Verify agent stopped after context exit
    assert not context_agent.is_running

@pytest.mark.asyncio
async def test_agent_connection():
    """Test agent connection functionality"""
    agent1 = Agent("Agent1")
    agent2 = Agent("Agent2")

    agent1.connect_to(agent2)
    agent2.connect_to(agent1)

    assert agent1.connected_agent == "Agent2"
    assert agent2.connected_agent == "Agent1"


if __name__ == "__main__":
    pytest.main(["-v", "test_agent.py"])