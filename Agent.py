
import threading
import queue
import random
import time


class Agent:
    def __init__(self, name):
        self.name = name
        # Communication queues
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()
        self.running = True

        # Registration dictionaries
        self.message_handlers = {}
        self.behaviors = {}

        # Word list
        self.words = [
            "hello", "sun", "world", "space", "moon",
            "crypto", "sky", "ocean", "universe", "human"
        ]

    def register_handler(self, message_type, handler_function):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler_function
        print(f"{self.name} registered handler for type: {message_type}")

    def register_behavior(self, behavior_name, behavior_function):
        """Register a behavior"""
        self.behaviors[behavior_name] = behavior_function
        print(f"{self.name} registered behavior: {behavior_name}")

    def hello_handler(self, message):
        """Handler for messages containing 'hello'"""
        if "hello" in message.get('content', '').lower():
            print(message)
            return True  # For testing
        return False

    def generate_message(self):
        """Generate random two-word messages"""
        words = random.sample(self.words, 2)
        message = {
            'type': 'default',
            'content': f"{words[0]} {words[1]}",
            'from': self.name
        }
        self.outbox.put(message)
        print(f"{self.name} sent: {message}")
        return message  # For testing

    def check_inbox(self):
        """Process messages from inbox"""
        while self.running:
            try:
                message = self.inbox.get(timeout=1)
                message_type = message.get('type', 'default')
                if handler := self.message_handlers.get(message_type):
                    handler(message)
            except queue.Empty:
                continue

    def run_behaviors(self):
        """Execute registered behaviors"""
        while self.running:
            for behavior in self.behaviors.values():
                behavior()
            time.sleep(2)

    def start(self):
        """Start the agent"""
        # Register default handlers and behaviors
        self.register_handler('default', self.hello_handler)
        self.register_behavior('generate', self.generate_message)

        # Start threads
        self.handler_thread = threading.Thread(target=self.check_inbox)
        self.behavior_thread = threading.Thread(target=self.run_behaviors)

        self.handler_thread.start()
        self.behavior_thread.start()

    def stop(self):
        """Stop the agent"""
        self.running = False
        self.handler_thread.join()
        self.behavior_thread.join()


def main():
    # Create two agents
    agent1 = Agent("Agent1")
    agent2 = Agent("Agent2")

    # Connect their queues
    agent1.outbox = agent2.inbox
    agent2.outbox = agent1.inbox

    print("Starting agents... Press Ctrl+C to stop")

    # Start both agents
    agent1.start()
    agent2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agents...")
        agent1.stop()
        agent2.stop()


if __name__ == "__main__":
    main()
