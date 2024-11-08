# main.py

import asyncio
import logging
import os
from typing import Tuple
from dotenv import load_dotenv
from agent import Agent
from behaviors import RandomMessageBehavior, TokenBalanceBehavior
from handlers import HelloHandler, CryptoTransferHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def connect_agents(agent1: Agent, agent2: Agent) -> None:
    """
    Connect two agents by linking their message boxes.
    Continuously forwards messages from each agent's outbox to the other's inbox.

    Args:
        agent1: First agent
        agent2: Second agent
    """
    try:
        # Connect agents
        agent1.connect_to(agent2)
        agent2.connect_to(agent1)

        while True:
            # Process messages from both agents concurrently
            await asyncio.gather(
                forward_messages(agent1, agent2),
                forward_messages(agent2, agent1)
            )
            
            # Small delay to prevent CPU overload
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in connect_agents: {e}")
        raise


async def forward_messages(from_agent: Agent, to_agent: Agent) -> None:
    """
    Forward messages from one agent to another asynchronously.
    
    Args:
        from_agent: Source agent
        to_agent: Destination agent
    """
    while not from_agent.outbox.is_empty():
        if message := await from_agent.outbox.get():
            await to_agent.inbox.put(message)
            logger.debug(f"Forwarded message from {from_agent.name} to {to_agent.name}: {message}")


async def setup_agents() -> Tuple[Agent, Agent]:
    """
    Create and configure two agents with their behaviors and handlers.
    Uses environment variables for configuration.

    Returns:
        Tuple[Agent, Agent]: Two configured agents
    """
    try:
        # Load environment variables
        load_dotenv()

        # Validate required environment variables
        required_vars = [
            "TOKEN_ADDRESS",
            "SOURCE_WALLET_ADDRESS",
            "TARGET_WALLET_ADDRESS",
            "SOURCE_WALLET_PRIVATE_KEY",
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Create agents with unique names
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")

        # Initialize behaviors with configuration
        random_behavior = RandomMessageBehavior()
        token_balance_behavior = TokenBalanceBehavior(
            contract_address=os.getenv("TOKEN_ADDRESS"),
            wallet_address=os.getenv("SOURCE_WALLET_ADDRESS")
        )

        # Initialize handlers with configuration
        hello_handler = HelloHandler()
        crypto_handler = CryptoTransferHandler(
            contract_address=os.getenv("TOKEN_ADDRESS"),
            source_address=os.getenv("SOURCE_WALLET_ADDRESS"),
            target_address=os.getenv("TARGET_WALLET_ADDRESS"),
            private_key=os.getenv("SOURCE_WALLET_PRIVATE_KEY")
        )

        # Register behaviors and handlers for both agents
        for agent in [agent1, agent2]:
            agent.register_behavior(random_behavior)
            agent.register_behavior(token_balance_behavior)
            agent.register_handler(hello_handler)
            agent.register_handler(crypto_handler)

        logger.info("Agents configured successfully")
        return agent1, agent2

    except Exception as e:
        logger.error(f"Error in setup_agents: {e}")
        raise


async def cleanup_agents(agent1: Agent, agent2: Agent) -> None:
    """
    Clean up agents gracefully.

    Args:
        agent1: First agent to clean up
        agent2: Second agent to clean up
    """
    try:
        await asyncio.gather(
            agent1.stop(),
            agent2.stop()
        )
        logger.info("Agents stopped successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


async def main():
    """
    Main function to run the agent system.
    Sets up agents, connects them, and handles cleanup.
    """
    agent1 = None
    agent2 = None

    try:
        logger.info("Starting agent system...")

        # Setup agents
        agent1, agent2 = await setup_agents()

        # Create tasks for agents and connection
        agent_tasks = [
            asyncio.create_task(agent1.run()),
            asyncio.create_task(agent2.run()),
            asyncio.create_task(connect_agents(agent1, agent2))
        ]

        # Wait for all tasks to complete or KeyboardInterrupt
        await asyncio.gather(*agent_tasks)

    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if agent1 or agent2:
            await cleanup_agents(agent1, agent2)
        logger.info("Agent system shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise