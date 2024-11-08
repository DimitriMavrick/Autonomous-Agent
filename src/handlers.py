# src/handlers.py

import logging
from typing import Optional
import asyncio
from agent import Handler, Message
from utils.web3_utils import Web3Helper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HelloHandler(Handler):
    """
    Handler that processes messages containing the keyword 'hello'.
    Prints matching messages to stdout.
    """

    async def can_handle(self, message: Message) -> bool:
        """
        Check if message contains 'hello' keyword.

        Args:
            message: Message to check

        Returns:
            bool: True if message contains 'hello'
        """
        return message.contains_keyword("hello")

    async def handle(self, message: Message) -> None:
        """
        Print message containing 'hello' to stdout.
        Simple and non-blocking operation.

        Args:
            message: Message to handle
        """
        print(f"Hello Handler received: {message}")
        logger.info(f"Processed hello message: {message}")


class CryptoTransferHandler(Handler):
    """
    Handler that processes messages containing the keyword 'crypto'.
    Transfers 1 token unit if conditions are met. Non-blocking implementation.
    """

    def __init__(
            self,
            contract_address: str,
            source_address: str,
            target_address: str,
            private_key: str
    ):
        """
        Initialize handler with Web3 details.

        Args:
            contract_address: ERC20 contract address
            source_address: Address to transfer from
            target_address: Address to transfer to
            private_key: Private key for source address
        """
        self.web3_helper = Web3Helper(contract_address)
        self.source_address = source_address
        self.target_address = target_address
        self.private_key = private_key
        self._transfer_in_progress = False
        logger.info(
            f"CryptoTransferHandler initialized for contract "
            f"{contract_address[:6]}...{contract_address[-4:]}"
        )

    async def can_handle(self, message: Message) -> bool:
        """
        Check if message contains 'crypto' keyword and no transfer is in progress.

        Args:
            message: Message to check

        Returns:
            bool: True if message contains 'crypto' and handler is available
        """
        if self._transfer_in_progress:
            logger.debug("Transfer in progress, skipping new crypto message")
            return False
        return message.contains_keyword("crypto")

    async def handle(self, message: Message) -> None:
        """
        Transfer 1 token unit if balance is sufficient.
        Non-blocking implementation with timeout and transfer tracking.

        Args:
            message: Message to handle
        """
        if self._transfer_in_progress:
            logger.debug("Transfer already in progress, skipping")
            return

        try:
            self._transfer_in_progress = True
            
            # Create transfer task
            transfer_task = asyncio.create_task(
                self._execute_transfer()
            )

            # Wait for transfer with timeout
            try:
                await asyncio.wait_for(transfer_task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("Transfer operation timed out")
            
        except Exception as e:
            logger.error(f"Error in crypto transfer handler: {e}")
        finally:
            self._transfer_in_progress = False

    async def _execute_transfer(self) -> None:
        """
        Execute the actual token transfer operation.
        Separated from handle method for better error handling and timeout control.
        """
        try:
            # Check balance first
            balance = await self.web3_helper.get_balance(self.source_address)

            if balance is None or balance < 1.0:
                logger.warning(
                    f"Insufficient balance for transfer. Current balance: {balance}"
                )
                return

            # Attempt transfer
            success = await self.web3_helper.transfer_tokens(
                from_address=self.source_address,
                to_address=self.target_address,
                amount=1.0,  # Transfer 1 token unit
                private_key=self.private_key
            )

            if success:
                logger.info(
                    f"Successfully transferred 1 token from "
                    f"{self.source_address[:6]}...{self.source_address[-4:]} to "
                    f"{self.target_address[:6]}...{self.target_address[-4:]}"
                )
            else:
                logger.error("Token transfer failed")

        except Exception as e:
            logger.error(f"Error executing transfer: {e}")