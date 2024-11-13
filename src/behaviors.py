# src/behaviors.py

import random
from datetime import datetime
from typing import List, Optional
import logging
import asyncio
from agent import Behavior, Message
from utils.web3_utils import Web3Helper

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
        self._message_generation_in_progress = False
        logger.info("RandomMessageBehavior initialized with "
                   f"{len(word_list)} words")

    async def execute(self) -> Optional[Message]:
        """
        Generate random two-word message asynchronously.

        Returns:
            Message: Contains randomly generated two-word string
        """
        if self._message_generation_in_progress:
            logger.debug("Message generation already in progress, skipping")
            return None

        try:
            self._message_generation_in_progress = True

            # Create a task for word selection
            async def select_words():
                return random.choice(self.word_list), random.choice(self.word_list)

            try:
                word_task = asyncio.create_task(select_words())
                word1, word2 = await asyncio.wait_for(word_task, timeout=0.1)
            except asyncio.TimeoutError:
                logger.warning("Word selection timed out")
                return None

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

        finally:
            self._message_generation_in_progress = False


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
        self._balance_check_in_progress = False

        logger.info(
            f"TokenBalanceBehavior initialized for wallet "
            f"{wallet_address[:6]}...{wallet_address[-4:]}"
        )

    async def execute(self) -> Optional[Message]:
        """
        Check token balance and generate balance message.
        Non-blocking implementation with timeout.

        Returns:
            Message: Contains current token balance
        """
        if self._balance_check_in_progress:
            logger.debug("Balance check already in progress, skipping")
            return None

        try:
            self._balance_check_in_progress = True

            # Create balance check task with timeout
            async def check_balance():
                return await self.web3_helper.get_balance(self.wallet_address)

            try:
                balance_task = asyncio.create_task(check_balance())
                balance = await asyncio.wait_for(balance_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Balance check timed out")
                return None

            if balance is None:
                logger.warning("No balance returned from web3_helper")
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
            self._balance_check_in_progress = False