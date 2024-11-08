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
            # Forward messages from agent1's outbox to agent2's inbox
            while not agent1.outbox.is_empty():
                if message := await agent1.outbox.get():
                    await agent2.inbox.put(message)
                    logger.info(f"Forwarded message from {agent1.name} to {agent2.name}: {message}")

            # Forward messages from agent2's outbox to agent1's inbox
            while not agent2.outbox.is_empty():
                if message := await agent2.outbox.get():
                    await agent1.inbox.put(message)
                    logger.info(f"Forwarded message from {agent2.name} to {agent1.name}: {message}")

            await asyncio.sleep(0.1)  # Prevent CPU overload

    except Exception as e:
        logger.error(f"Error in connect_agents: {e}")
        raise


async def setup_agents() -> Tuple[Agent, Agent]:
    """
    Create and configure two agents with their behaviors and handlers.

    Returns:
        Tuple[Agent, Agent]: Two configured agents
    """
    try:
        # Load environment variables
        load_dotenv()

        if not all([
            os.getenv("ERC20_CONTRACT_ADDRESS"),
            os.getenv("SOURCE_WALLET_ADDRESS"),
            os.getenv("TARGET_WALLET_ADDRESS"),
            os.getenv("SOURCE_WALLET_PRIVATE_KEY")
        ]):
            raise ValueError("Missing required environment variables")

        # Create agents
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")

        # Create behaviors and handlers
        random_behavior = RandomMessageBehavior()  # Uses default word list
        token_balance_behavior = TokenBalanceBehavior(
            contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
            wallet_address=os.getenv("SOURCE_WALLET_ADDRESS")
        )

        hello_handler = HelloHandler()
        crypto_handler = CryptoTransferHandler(
            contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
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
        await agent1.stop()
        await agent2.stop()
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
        tasks = [
            asyncio.create_task(agent1.run()),
            asyncio.create_task(agent2.run()),
            asyncio.create_task(connect_agents(agent1, agent2))
        ]

        # Wait for all tasks to complete or KeyboardInterrupt
        await asyncio.gather(*tasks)

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