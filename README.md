# Autonomous Agent System

## Overview
A Python-based implementation of autonomous agents that communicate through asynchronous messages. Each agent can process incoming messages, generate outgoing messages, and execute behaviors based on timing or internal state.

## Features
- Asynchronous message processing
- Configurable message handlers
- Time-based behaviors
- Agent-to-agent communication
- Event-driven architecture
- Extensible base agent class


## Components

### 1. Base Agent (base_agent.py)
The foundation class providing core agent functionality:
- Message handling system
- Behavior registration
- Asynchronous processing
- Internal state management

```python
class BaseAgent:
    def register_handler(self, message_type: str, handler: Callable)
    def register_behavior(self, behavior_name: str, behavior: Callable)
    async def process_messages()
    async def execute_behaviors()
```

### 2. Concrete Agent (concrete_agent.py)
Implementation of a specific agent type that:
- Filters messages containing "hello"
- Generates random two-word messages
- Uses a predefined vocabulary
```python
class ConcreteAgent(BaseAgent):
    # Vocabulary
    word_list = ["hello", "sun", "world", "space", "moon",
                 "crypto", "sky", "ocean", "universe", "human"]
```

## Installation

1. Ensure Python 3.7+ is installed:
```bash
python --version
```

2. Clone the repository:
```bash
git clone <repository-url>
cd autonomous-agents
```

3. Install dependencies:
```bash
pip install pytest pytest-asyncio
```

## Usage

### Running the System

1. Start the agent system:
```bash
python main.py
```

2. The system will:
- Create two agents
- Connect their message channels
- Begin message exchange
- Process messages containing "hello"

### Example Output
```
Initializing agents...
Starting agents... Press Ctrl+C to stop

Agent1 sent: {'type': 'default', 'content': 'hello world', 'from': 'Agent1'}
Agent2 received: {'type': 'default', 'content': 'hello world', 'from': 'Agent1'}
...
```

## Development

### Creating a New Agent Type

1. Inherit from BaseAgent:
```python
from base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
```

2. Register handlers and behaviors:
```python
# Register message handler
self.register_handler('my_type', self.my_handler)

# Register behavior
self.register_behavior(
    'my_behavior',
    self.my_behavior,
    interval=1.0
)
```

3. Implement handlers and behaviors:
```python
async def my_handler(self, message: dict):
    # Handle message

async def my_behavior(self, state: dict):
    # Execute behavior
```

## Testing

### Running Tests

1. Run all tests:
```bash
python -m pytest tests/test_agents.py -v
```

2. Run specific test:
```bash
python -m pytest tests/test_agents.py -v -k "test_name"
```

### Test Coverage
- Message handler registration
- Behavior registration
- Random message generation
- Hello message filtering
- Behavior timing
- Agent interaction
- Word distribution
- Error handling

## Architecture

### Message Flow
```
Agent1                     Agent2
  │                         │
  ├─── Generate Message ───►│
  │                        ├─► Process Message
  │                        │
  │◄── Generate Message ───┤
  ├─► Process Message      │
  │                         │
```

### Behavior Execution
1. Time-based:
   - Execute at specified intervals
   - Regular message generation

2. State-based:
   - React to internal state changes
   - Conditional execution

## Configuration

### Agent Settings
```python
# Behavior intervals
interval=2.0  # seconds

# Message types
message_type='default'

# Handler registration
agent.register_handler(message_type, handler)
```

## Error Handling

1. Message Processing Errors:
```python
try:
    await handler(message)
except Exception as e:
    logger.error(f"Error processing message: {e}")
```

2. Behavior Execution Errors:
```python
try:
    await behavior(state)
except Exception as e:
    logger.error(f"Error in behavior: {e}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## Future Enhancements

1. Planned Features:
   - Additional message types
   - More complex behaviors
   - Enhanced state management
   - Web interface

2. Potential Improvements:
   - Performance optimization
   - Extended test coverage
   - Additional agent types
   - Documentation expansion
