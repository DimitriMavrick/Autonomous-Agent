# src/handlers.py

import logging
from typing import Optional
from web3 import Web3
from agent import Handler, Message

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HelloHandler(Handler):
    """
    Handles messages containing the keyword "hello" by printing them to stdout.
    """

    def __init__(self):
        """Initialize the hello message handler."""
        logger.info("HelloHandler initialized")

    async def can_handle(self, message: Message) -> bool:
        """
        Check if message contains "hello" keyword.

        Args:
            message: Message to check

        Returns:
            bool: True if message contains "hello"
        """
        return message.contains_keyword("hello")

    async def handle(self, message: Message) -> None:
        """
        Print message containing "hello" to stdout.

        Args:
            message: Message to handle
        """
        try:
            print(f"Hello Handler received: {message.content}")
            logger.info(f"Processed hello message: {message.content}")
        except Exception as e:
            logger.error(f"Error handling hello message: {e}")


class CryptoTransferHandler(Handler):
    """
    Handles messages containing "crypto" by initiating ERC20 token transfers.
    """

    def __init__(
            self,
            web3_provider: str,
            contract_address: str,
            source_address: str,
            target_address: str,
            private_key: str,
            contract_abi: list,
            transfer_amount: int = 1
    ):
        """
        Initialize the crypto transfer handler.

        Args:
            web3_provider: Web3 provider URL (Tenderly fork)
            contract_address: ERC20 contract address
            source_address: Address to transfer from
            target_address: Address to transfer to
            private_key: Private key for source address
            contract_abi: ERC20 contract ABI
            transfer_amount: Amount of tokens to transfer (default: 1)
        """
        # Initialize Web3 connection
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))

        # Store addresses
        self.contract_address = self.web3.to_checksum_address(contract_address)
        self.source_address = self.web3.to_checksum_address(source_address)
        self.target_address = self.web3.to_checksum_address(target_address)

        # Store private key and transfer amount
        self.private_key = private_key
        self.transfer_amount = transfer_amount

        # Initialize contract
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=contract_abi
        )

        logger.info(
            f"CryptoTransferHandler initialized for transfers from "
            f"{source_address[:6]}...{source_address[-4:]} to "
            f"{target_address[:6]}...{target_address[-4:]}"
        )

    async def can_handle(self, message: Message) -> bool:
        """
        Check if message contains "crypto" keyword.

        Args:
            message: Message to check

        Returns:
            bool: True if message contains "crypto"
        """
        return message.contains_keyword("crypto")

    async def handle(self, message: Message) -> None:
        """
        Handle crypto transfer message by transferring tokens.

        Args:
            message: Message to handle
        """
        try:
            # Check source balance
            balance = await self._get_balance(self.source_address)
            if balance is None:
                logger.error("Could not check source address balance")
                return

            # Convert transfer amount considering decimals
            decimals = self.contract.functions.decimals().call()
            transfer_amount_wei = self.transfer_amount * (10 ** decimals)

            # Check if enough balance
            if balance < transfer_amount_wei:
                logger.warning(
                    f"Insufficient balance for transfer: {balance / (10 ** decimals)} "
                    f"< {self.transfer_amount}"
                )
                return

            # Build transfer transaction
            nonce = self.web3.eth.get_transaction_count(self.source_address)

            transfer_txn = self.contract.functions.transfer(
                self.target_address,
                transfer_amount_wei
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,  # Adjust as needed
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transfer_txn,
                private_key=self.private_key
            )

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(
                f"Transfer successful! Transferred {self.transfer_amount} tokens. "
                f"Transaction hash: {receipt.transactionHash.hex()}"
            )

        except Exception as e:
            logger.error(f"Error handling crypto transfer: {e}")

    async def _get_balance(self, address: str) -> Optional[int]:
        """
        Helper method to get token balance.

        Args:
            address: Address to check balance for

        Returns:
            Optional[int]: Token balance in wei, None if error
        """
        try:
            return self.contract.functions.balanceOf(
                self.web3.to_checksum_address(address)
            ).call()
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None


# Minimal ERC20 ABI including transfer function
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
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    from dotenv import load_dotenv


    async def example():
        # Hello handler example
        hello_handler = HelloHandler()
        message = Message(type="text", content="hello world")
        if await hello_handler.can_handle(message):
            await hello_handler.handle(message)

        # Crypto transfer handler example
        load_dotenv()
        crypto_handler = CryptoTransferHandler(
            web3_provider=os.getenv("TENDERLY_FORK_RPC_URL"),
            contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
            source_address=os.getenv("SOURCE_WALLET_ADDRESS"),
            target_address=os.getenv("TARGET_WALLET_ADDRESS"),
            private_key=os.getenv("SOURCE_WALLET_PRIVATE_KEY"),
            contract_abi=ERC20_ABI
        )

        crypto_message = Message(type="text", content="send some crypto please")
        if await crypto_handler.can_handle(crypto_message):
            await crypto_handler.handle(crypto_message)


    asyncio.run(example())