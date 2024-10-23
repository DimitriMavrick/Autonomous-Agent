
import asyncio
from concrete_agent import ConcreteAgent


async def main():
    """
    Main function to run two concrete agents that communicate with each other.
    The agents will:
    1. Generate random messages every 2 seconds
    2. Process messages from each other
    3. React to 'hello' messages
    """
    print("Initializing agents...")

    # Create two agents
    agent1 = ConcreteAgent("Agent1")
    agent2 = ConcreteAgent("Agent2")

    # Connect their inboxes and outboxes
    agent1.outbox = agent2.inbox
    agent2.outbox = agent1.inbox

    print("Starting agents... Press Ctrl+C to stop")

    try:
        # Create tasks for both agents
        tasks = [
            asyncio.create_task(agent1.run()),  # This runs both process_messages and execute_behaviors
            asyncio.create_task(agent2.run())  # This runs both process_messages and execute_behaviors
        ]

        # Wait for tasks to complete (will run until interrupted)
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print("\nReceived shutdown signal. Stopping agents gracefully...")
        # Stop agents
        agent1.is_running = False
        agent2.is_running = False

        # Cancel tasks
        for task in tasks:
            task.cancel()

        try:
            # Wait for tasks to be cancelled
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        print("Agents stopped successfully.")

    except Exception as e:
        print(f"Error occurred: {e}")
        # Ensure agents are stopped even if an error occurs
        agent1.is_running = False
        agent2.is_running = False
        for task in tasks:
            task.cancel()

    finally:
        print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
