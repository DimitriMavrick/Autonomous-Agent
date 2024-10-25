import threading
import queue
import random
import time
import os
from dotenv import load_dotenv
from web3 import Web3
from config import (
    TOKEN_ADDRESS, ERC20_ABI, WORD_LIST,
    CHECK_BALANCE_INTERVAL, MESSAGE_GENERATION_INTERVAL,
    GAS_LIMIT
)

# Load environment variables
load_dotenv()


class Agent:
    def __init__(self, name):
        self.name = name
        # Message queues
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()
        self.running = True

        # Handlers and behaviors registration
        self.message_handlers = {}
        self.behaviors = {}

        # Word list for messages
        self.words = WORD_LIST

        # Web3 setup
        self.setup_web3()

        # Register default handlers and behaviors
        self.register_default_handlers()
        self.register_default_behaviors()

    def setup_web3(self):
        """Setup Web3 and token contract"""
        # Connect to network
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI')))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")

        # Token contract setup
        self.token_contract = self.w3.eth.contract(
            address=TOKEN_ADDRESS,
            abi=ERC20_ABI
        )

        # Setup wallet
        self.wallet_address = os.getenv('SOURCE_WALLET_ADDRESS')
        self.private_key = os.getenv('SOURCE_WALLET_PRIVATE_KEY')

        if not all([self.wallet_address, self.private_key]):
            raise ValueError("Wallet configuration missing in .env")

        print(f"Connected to network. Wallet: {self.wallet_address}")

    def register_handler(self, message_type: str, handler_function):
        """Register a message handler"""
        self.message_handlers[message_type] = handler_function
        print(f"{self.name} registered handler for: {message_type}")

    def register_behavior(self, behavior_name: str, behavior_function):
        """Register a behavior"""
        self.behaviors[behavior_name] = behavior_function
        print(f"{self.name} registered behavior: {behavior_name}")

    def register_default_handlers(self):
        """Register default message handlers"""

        def hello_handler(message):
            """Handle hello messages"""
            if "hello" in message.get('content', '').lower():
                print(f"HELLO MESSAGE: {message}")

        def crypto_handler(message):
            """Handle crypto messages"""
            if "crypto" in message.get('content', '').lower():
                target = message.get('target_address')
                if target and Web3.is_address(target):
                    self.transfer_token(target)

        # Register handlers
        self.register_handler('hello', hello_handler)
        self.register_handler('crypto', crypto_handler)

    def register_default_behaviors(self):
        """Register default behaviors"""

        def random_message_behavior():
            """Generate random messages"""
            words = random.sample(self.words, 2)
            message = {
                'type': 'default',
                'content': f"{words[0]} {words[1]}",
                'from': self.name
            }
            self.outbox.put(message)
            print(f"{self.name} sent: {message}")
            time.sleep(MESSAGE_GENERATION_INTERVAL)

        def check_balance_behavior():
            """Check token balance"""
            balance = self.token_contract.functions.balanceOf(self.wallet_address).call()
            print(f"Token balance for {self.wallet_address}: {balance}")
            time.sleep(CHECK_BALANCE_INTERVAL)

        # Register behaviors
        self.register_behavior('random_messages', random_message_behavior)
        self.register_behavior('check_balance', check_balance_behavior)

    def transfer_token(self, target_address):
        """Transfer 1 token to target address"""
        try:
            # Check balance
            balance = self.token_contract.functions.balanceOf(self.wallet_address).call()
            if balance < 1:
                print("Insufficient balance")
                return False

            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            txn = self.token_contract.functions.transfer(
                target_address,
                1  # 1 token unit
            ).build_transaction({
                'from': self.wallet_address,
                'nonce': nonce,
                'gas': GAS_LIMIT,
                'gasPrice': self.w3.eth.gas_price
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(
                txn,
                self.private_key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transfer successful: {receipt['transactionHash'].hex()}")
            return True

        except Exception as e:
            print(f"Transfer failed: {e}")
            return False

    # def setup_web3(self):
    #     """Setup Web3 with Tenderly fork"""
    #     try:
    #         # Connect to Tenderly fork
    #         tenderly_rpc = os.getenv('WEB3_PROVIDER_URI')
    #         if not tenderly_rpc:
    #             raise ValueError("Tenderly Fork RPC URL not found in .env")
    #
    #         # Initialize Web3 with Tenderly fork
    #         self.w3 = Web3(Web3.HTTPProvider(
    #             tenderly_rpc,
    #             request_kwargs={
    #                 'headers': {
    #                     'Content-Type': 'application/json',
    #                 }
    #             }
    #         ))
    #
    #         if not self.w3.is_connected():
    #             raise ConnectionError("Failed to connect to Tenderly fork")
    #
    #         print(f"Connected to Tenderly fork")

    def process_messages(self):
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
            try:
                for behavior in self.behaviors.values():
                    behavior()
            except Exception as e:
                print(f"Error in behavior: {e}")

    def start(self):
        """Start all threads"""
        self.threads = [
            threading.Thread(target=self.process_messages, name=f"{self.name}-messages"),
            threading.Thread(target=self.run_behaviors, name=f"{self.name}-behaviors")
        ]

        for thread in self.threads:
            thread.start()
            print(f"Started {thread.name}")

    def stop(self):
        """Stop all threads"""
        print(f"Stopping {self.name}")
        self.running = False
        for thread in self.threads:
            thread.join()
        print(f"Stopped {self.name}")


def main():
    try:
        # Create two agents
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")

        # Connect their queues
        agent1.outbox = agent2.inbox
        agent2.outbox = agent1.inbox

        print("Starting agents... Press Ctrl+C to stop")

        # Start agents
        agent1.start()
        agent2.start()

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping agents...")
        agent1.stop()
        agent2.stop()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()