# src/web3_client.py

from web3 import Web3
from typing import Optional, Dict, Any, List
import logging
from eth_typing import ChecksumAddress
from web3.contract import Contract
from web3.exceptions import ContractLogicError
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Web3Client:
    """
    Centralized client for Web3 interactions with fallback RPC support.
    """

    def __init__(
            self,
            contract_address: str,
            contract_abi: list
    ):
        """
        Initialize with multiple RPC providers for fallback support.

        Args:
            contract_address: ERC20 contract address
            contract_abi: Contract ABI
        """
        self.contract_address = contract_address
        self.contract_abi = contract_abi
        self.web3 = None
        self.contract = None

        # Initialize connection
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Web3 connection with fallback support."""
        # Load environment variables
        load_dotenv()

        # List of potential RPC providers in order of preference
        rpc_providers = [
            "https://sepolia.infura.io/v3/c793d11827584ba3b3d9632bfa881f5b",  # Infura
            os.getenv("TENDERLY_FORK_RPC_URL"),
            "https://rpc.sepolia.dev",  # Public Sepolia RPC
            "https://eth-sepolia.g.alchemy.com/v2/demo"  # Alchemy public endpoint
        ]

        # Try each provider until one works
        for provider_url in rpc_providers:
            if not provider_url:
                continue

            try:
                web3 = Web3(Web3.HTTPProvider(provider_url))
                if web3.is_connected():
                    # Verify network
                    chain_id = web3.eth.chain_id
                    if chain_id != 11155111:  # Sepolia chain ID
                        logger.warning(f"Wrong network on {provider_url}: {chain_id}")
                        continue

                    self.web3 = web3
                    self.contract = self.web3.eth.contract(
                        address=self.web3.to_checksum_address(self.contract_address),
                        abi=self.contract_abi
                    )

                    # Verify contract
                    try:
                        self.contract.functions.decimals().call()
                        logger.info(f"Connected successfully to {provider_url}")
                        return
                    except Exception:
                        logger.warning(f"Contract not valid on {provider_url}")
                        continue

            except Exception as e:
                logger.warning(f"Failed to connect to {provider_url}: {str(e)}")
                continue

        raise ConnectionError("Failed to connect to any RPC provider")

    async def ensure_connection(self) -> None:
        """Ensure we have a valid connection, retry if not."""
        if not self.web3 or not self.web3.is_connected():
            self._initialize_connection()

    # ... rest of your methods with added connection check ...

    async def transfer_tokens(
            self,
            from_address: str,
            to_address: str,
            amount: float,
            private_key: str
    ) -> Optional[Dict[str, Any]]:
        """Transfer tokens between addresses with connection retry."""
        try:
            await self.ensure_connection()

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

            # Build transaction
            transaction = self.contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,  # Fixed gas limit for simplicity
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                private_key=private_key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] == 1:
                logger.info(
                    f"Transfer successful! Amount: {amount} tokens, "
                    f"Hash: {receipt['transactionHash'].hex()}"
                )
                return receipt
            raise ContractLogicError("Transaction failed")

        except Exception as e:
            logger.error(f"Error transferring tokens: {e}")
            return None

    # ... other methods remain the same ...