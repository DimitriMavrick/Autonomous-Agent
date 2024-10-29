# src/behaviors.py

import random
from datetime import datetime
from typing import List, Optional
import logging
from web3 import Web3
from agent import Behavior, Message

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Word list for random message generation
WORD_LIST = [
    "hello", "sun", "world", "space", "moon",
    "crypto", "sky", "ocean", "universe", "human"
]


class RandomMessageBehavior(Behavior):
    """
    Generates random two-word messages every 2 seconds from predefined word list.
    """

    def __init__(self, word_list: List[str] = WORD_LIST):
        """
        Initialize behavior with word list and 2-second interval.

        Args:
            word_list: List of words to choose from
        """
        super().__init__(interval=2.0)  # 2 seconds interval
        self.word_list = word_list
        logger.info("RandomMessageBehavior initialized with "
                    f"{len(word_list)} words")

    async def execute(self) -> Optional[Message]:
        """
        Generate random two-word message.

        Returns:
            Message: Contains randomly generated two-word string
        """
        try:
            # Select two random words
            word1 = random.choice(self.word_list)
            word2 = random.choice(self.word_list)

            # Create message content
            content = f"{word1} {word2}"

            # Create and return message
            message = Message(
                type="random_words",
                content=content,
                metadata={
                    "word1": word1,
                    "word2": word2,
                    "generated_at": datetime.now().isoformat()
                }
            )

            logger.debug(f"Generated random message: {content}")
            return message

        except Exception as e:
            logger.error(f"Error generating random message: {e}")
            return None


class TokenBalanceBehavior(Behavior):
    """
    Checks ERC20 token balance every 10 seconds and generates balance message.
    """

    def __init__(
            self,
            web3_provider: str,
            contract_address: str,
            wallet_address: str,
            contract_abi: List[dict]
    ):
        """
        Initialize behavior with Web3 and contract details.

        Args:
            web3_provider: Web3 provider URL (e.g., Tenderly fork URL)
            contract_address: ERC20 contract address
            wallet_address: Address to check balance for
            contract_abi: ERC20 contract ABI
        """
        super().__init__(interval=10.0)  # 10 seconds interval

        # Initialize Web3 connection
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))

        # Store addresses
        self.contract_address = contract_address
        self.wallet_address = wallet_address

        # Initialize contract
        self.contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(contract_address),
            abi=contract_abi
        )

        logger.info(
            f"TokenBalanceBehavior initialized for wallet "
            f"{wallet_address[:6]}...{wallet_address[-4:]}"
        )

    async def execute(self) -> Optional[Message]:
        """
        Check token balance and generate balance message.

        Returns:
            Message: Contains current token balance
        """
        try:
            # Get token balance
            balance = self.contract.functions.balanceOf(
                self.web3.to_checksum_address(self.wallet_address)
            ).call()

            # Get token decimals
            decimals = self.contract.functions.decimals().call()

            # Convert balance to human-readable format
            human_balance = balance / (10 ** decimals)

            # Create message
            message = Message(
                type="token_balance",
                content=f"Current balance: {human_balance}",
                metadata={
                    "raw_balance": str(balance),
                    "decimals": decimals,
                    "human_balance": human_balance,
                    "wallet_address": self.wallet_address,
                    "contract_address": self.contract_address,
                    "checked_at": datetime.now().isoformat()
                }
            )

            logger.info(
                f"Token balance checked for "
                f"{self.wallet_address[:6]}...{self.wallet_address[-4:]}: "
                f"{human_balance}"
            )
            return message

        except Exception as e:
            logger.error(f"Error checking token balance: {e}")
            return None

    async def get_balance(self) -> Optional[float]:
        """
        Helper method to get current balance.

        Returns:
            float: Current token balance in human-readable format
        """
        try:
            balance = self.contract.functions.balanceOf(
                self.web3.to_checksum_address(self.wallet_address)
            ).call()
            decimals = self.contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return None


# Example minimal ERC20 ABI (only needed functions)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    from dotenv import load_dotenv


    async def example():
        # Random message behavior example
        random_behavior = RandomMessageBehavior()
        message = await random_behavior.execute()
        print(f"Random message: {message}")

        # Token balance behavior example
        load_dotenv()
        balance_behavior = TokenBalanceBehavior(
            web3_provider=os.getenv("TENDERLY_FORK_RPC_URL"),
            contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
            wallet_address=os.getenv("SOURCE_WALLET_ADDRESS"),
            contract_abi=ERC20_ABI
        )
        balance_message = await balance_behavior.execute()
        print(f"Balance message: {balance_message}")


    asyncio.run(example())