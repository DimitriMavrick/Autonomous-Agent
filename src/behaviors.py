# src/behaviors.py

import random
from datetime import datetime
from typing import List, Optional
import logging
from agent import Behavior, Message
from utils.web3_utils import Web3Helper
import asyncio

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
    Non-blocking implementation.
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
        Generate random two-word message asynchronously.

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
    Non-blocking implementation.
    """

    def __init__(
            self,
            contract_address: str,
            wallet_address: str
    ):
        """
        Initialize behavior with contract and wallet details.

        Args:
            contract_address: ERC20 contract address
            wallet_address: Address to check balance for
        """
        super().__init__(interval=10.0)  # 10 seconds interval
        self.wallet_address = wallet_address
        self.web3_helper = Web3Helper(contract_address)
        # Track ongoing operations
        self._checking_balance = False

        logger.info(
            f"TokenBalanceBehavior initialized for wallet "
            f"{wallet_address[:6]}...{wallet_address[-4:]}"
        )

    async def execute(self) -> Optional[Message]:
        """
        Check token balance and generate balance message asynchronously.
        Uses non-blocking approach to prevent holding up other behaviors.

        Returns:
            Message: Contains current token balance
        """
        # Skip if already checking balance
        if self._checking_balance:
            logger.debug("Balance check already in progress, skipping")
            return None

        try:
            self._checking_balance = True
            
            # Create task for balance check
            balance_task = asyncio.create_task(
                self.web3_helper.get_balance(self.wallet_address)
            )
            
            # Wait for balance with timeout
            try:
                balance = await asyncio.wait_for(balance_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Balance check timed out")
                return None

            if balance is None:
                return None

            # Create message
            message = Message(
                type="token_balance",
                content=f"Current balance: {balance}",
                metadata={
                    "human_balance": balance,
                    "wallet_address": self.wallet_address,
                    "contract_address": self.web3_helper.contract_address,
                    "checked_at": datetime.now().isoformat()
                }
            )

            logger.info(
                f"Token balance checked for "
                f"{self.wallet_address[:6]}...{self.wallet_address[-4:]}: "
                f"{balance}"
            )
            return message

        except Exception as e:
            logger.error(f"Error checking token balance: {e}")
            return None

        finally:
            self._checking_balance = False