# main.py

import asyncio
import logging
import os
from typing import Tuple
from dotenv import load_dotenv
from agent import Agent
from behaviors import RandomMessageBehavior, TokenBalanceBehavior
from handlers import HelloHandler, CryptoTransferHandler
from web3_client import ERC20_ABI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_agents(agent1: Agent, agent2: Agent) -> None:
    """
    Connect two agents by linking their message boxes.
    Continuously forwards messages from each agent's outbox to the other's inbox.
    """
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

        await asyncio.sleep(0.1)


async def setup_agents() -> Tuple[Agent, Agent]:
    """Create and configure two agents with their behaviors and handlers."""
    # Load environment variables
    load_dotenv()

    # Create agents
    agent1 = Agent("Agent1")
    agent2 = Agent("Agent2")

    # Create behaviors and handlers
    random_behavior = RandomMessageBehavior()
    token_balance_behavior = TokenBalanceBehavior(
        web3_provider=os.getenv("TENDERLY_FORK_RPC_URL"),
        contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
        wallet_address=os.getenv("SOURCE_WALLET_ADDRESS"),
        contract_abi=ERC20_ABI
    )

    hello_handler = HelloHandler()
    crypto_handler = CryptoTransferHandler(
        web3_provider=os.getenv("TENDERLY_FORK_RPC_URL"),
        contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
        source_address=os.getenv("SOURCE_WALLET_ADDRESS"),
        target_address=os.getenv("TARGET_WALLET_ADDRESS"),
        private_key=os.getenv("SOURCE_WALLET_PRIVATE_KEY"),
        contract_abi=ERC20_ABI
    )

    # Register behaviors and handlers for both agents
    for agent in [agent1, agent2]:
        agent.register_behavior(random_behavior)
        agent.register_behavior(token_balance_behavior)
        agent.register_handler(hello_handler)
        agent.register_handler(crypto_handler)

    return agent1, agent2


async def main():
    """Main function to run the agent system."""
    try:
        # Setup agents
        agent1, agent2 = await setup_agents()

        logger.info("Starting agents with behaviors and handlers...")
        # Create tasks for agents and connection
        agent1_task = asyncio.create_task(agent1.run())
        agent2_task = asyncio.create_task(agent2.run())
        connection_task = asyncio.create_task(connect_agents(agent1, agent2))

        # Wait for all tasks to complete (or KeyboardInterrupt)
        await asyncio.gather(agent1_task, agent2_task, connection_task)

    except KeyboardInterrupt:
        logger.info("Shutting down agents...")
        await agent1.stop()
        await agent2.stop()
        logger.info("Agents stopped successfully")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())