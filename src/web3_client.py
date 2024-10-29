# src/web3_client.py

from web3 import Web3
from typing import Optional, Dict, Any
import logging
from eth_typing import ChecksumAddress
from web3.contract import Contract
from web3.exceptions import ContractLogicError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Web3Client:
    """
    Centralized client for Web3 interactions.
    Handles ERC20 token operations and connection management.
    """

    def __init__(
            self,
            provider_url: str,
            contract_address: str,
            contract_abi: list
    ):
        try:
            # Initialize Web3 connection
            self.web3 = Web3(Web3.HTTPProvider(provider_url))

            # Validate connection
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to Web3 provider")

            # Get network info
            self.chain_id = self.web3.eth.chain_id

            # Verify we're on Sepolia (chain ID 11155111)
            if self.chain_id != 11155111:
                raise ValueError(f"Expected Sepolia network (11155111), got chain ID: {self.chain_id}")

            # Set up contract
            self.contract_address = self.web3.to_checksum_address(contract_address)
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=contract_abi
            )

            # Verify contract existence
            try:
                self.contract.functions.decimals().call()
            except Exception as e:
                raise ValueError(f"Contract not found at {contract_address} or is not an ERC20 token")

            logger.info(
                f"Web3 client initialized. Connected to Sepolia (Chain ID: {self.chain_id})"
                f"\nContract address: {self.contract_address}"
            )

        except Exception as e:
            logger.error(f"Error initializing Web3 client: {e}")
            raise

    def to_checksum_address(self, address: str) -> ChecksumAddress:
        """
        Convert address to checksum format.

        Args:
            address: Ethereum address

        Returns:
            ChecksumAddress: Checksummed address
        """
        return self.web3.to_checksum_address(address)

    async def get_token_balance(self, address: str) -> Optional[float]:
        """
        Get token balance for address in human-readable format.

        Args:
            address: Address to check balance for

        Returns:
            Optional[float]: Token balance with decimals applied
        """
        try:
            checksummed_address = self.to_checksum_address(address)
            balance_wei = self.contract.functions.balanceOf(checksummed_address).call()
            decimals = self.contract.functions.decimals().call()

            balance = balance_wei / (10 ** decimals)
            logger.debug(f"Balance for {address}: {balance}")
            return balance

        except Exception as e:
            logger.error(f"Error getting token balance for {address}: {e}")
            return None

    async def get_token_decimals(self) -> Optional[int]:
        """
        Get token decimals.

        Returns:
            Optional[int]: Token decimals
        """
        try:
            return self.contract.functions.decimals().call()
        except Exception as e:
            logger.error(f"Error getting token decimals: {e}")
            return None

    async def transfer_tokens(
            self,
            from_address: str,
            to_address: str,
            amount: float,
            private_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transfer tokens between addresses.

        Args:
            from_address: Source address
            to_address: Target address
            amount: Amount of tokens to transfer (in human-readable format)
            private_key: Private key for source address

        Returns:
            Optional[Dict[str, Any]]: Transaction receipt if successful
        """
        try:
            # Convert addresses to checksum format
            from_address = self.to_checksum_address(from_address)
            to_address = self.to_checksum_address(to_address)

            # Get decimals and convert amount
            decimals = await self.get_token_decimals()
            if decimals is None:
                raise ValueError("Could not get token decimals")

            amount_wei = int(amount * (10 ** decimals))

            # Check balance
            balance = await self.get_token_balance(from_address)
            if balance is None:
                raise ValueError("Could not check source address balance")

            if balance < amount:
                raise ValueError(
                    f"Insufficient balance. Has: {balance}, Needs: {amount}"
                )

            # Prepare transaction
            nonce = self.web3.eth.get_transaction_count(from_address)

            # Estimate gas
            gas_estimate = self.contract.functions.transfer(
                to_address,
                amount_wei
            ).estimate_gas({'from': from_address})

            # Build transaction
            transaction = self.contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })

            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                private_key=private_key
            )

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            # Check if transaction was successful
            if receipt['status'] == 1:
                logger.info(
                    f"Transfer successful! Amount: {amount} tokens, "
                    f"Transaction hash: {receipt['transactionHash'].hex()}"
                )
                return receipt
            else:
                raise ContractLogicError("Transaction failed")

        except Exception as e:
            logger.error(f"Error transferring tokens: {e}")
            return None

    async def validate_connection(self) -> bool:
        """
        Validate Web3 connection is active.

        Returns:
            bool: True if connected
        """
        try:
            return self.web3.is_connected()
        except Exception as e:
            logger.error(f"Error validating connection: {e}")
            return False


# Common ERC20 ABI - used across the application
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
        load_dotenv()

        # Initialize client
        client = Web3Client(
            provider_url=os.getenv("TENDERLY_FORK_RPC_URL"),
            contract_address=os.getenv("ERC20_CONTRACT_ADDRESS"),
            contract_abi=ERC20_ABI
        )

        # Check connection
        if await client.validate_connection():
            # Check balance
            balance = await client.get_token_balance(
                os.getenv("SOURCE_WALLET_ADDRESS")
            )
            print(f"Balance: {balance}")

            # Perform transfer
            receipt = await client.transfer_tokens(
                from_address=os.getenv("SOURCE_WALLET_ADDRESS"),
                to_address=os.getenv("TARGET_WALLET_ADDRESS"),
                amount=1.0,
                private_key=os.getenv("SOURCE_WALLET_PRIVATE_KEY")
            )

            if receipt:
                print(f"Transfer successful! Hash: {receipt['transactionHash'].hex()}")


    asyncio.run(example())