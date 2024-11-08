# src/utils/web3_utils.py
from web3 import Web3
from typing import Optional, List
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Single source of truth for ERC20 ABI
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


class Web3Helper:
    def __init__(self, contract_address: str):
        """
        Initialize Web3Helper with fallback RPC support.

        Args:
            contract_address: ERC20 contract address
        """
        self.contract_address = contract_address
        self.web3 = None
        self.contract = None
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Web3 connection with fallback support."""
        # RPC providers in order of preference
        rpc_providers = [
            "https://sepolia.infura.io/v3/c793d11827584ba3b3d9632bfa881f5b",  # Infura
            "https://rpc.sepolia.dev",  # Public Sepolia RPC
            "https://eth-sepolia.g.alchemy.com/v2/demo",  # Alchemy public endpoint
            os.getenv("TENDERLY_FORK_RPC_URL")  # Fallback to Tenderly if available
        ]

        for provider_url in rpc_providers:
            if not provider_url:
                continue

            try:
                web3 = Web3(Web3.HTTPProvider(provider_url))
                if web3.is_connected():
                    self.web3 = web3
                    self.contract = self.web3.eth.contract(
                        address=self.web3.to_checksum_address(self.contract_address),
                        abi=ERC20_ABI
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

    async def get_balance(self, address: str) -> Optional[float]:
        """Get token balance in human-readable format"""
        try:
            await self.ensure_connection()
            checksummed_address = self.web3.to_checksum_address(address)
            balance = self.contract.functions.balanceOf(checksummed_address).call()
            decimals = self.contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None

    async def get_raw_balance(self, address: str) -> Optional[int]:
        """Get token balance in wei"""
        try:
            await self.ensure_connection()
            checksummed_address = self.web3.to_checksum_address(address)
            return self.contract.functions.balanceOf(checksummed_address).call()
        except Exception as e:
            logger.error(f"Error getting raw balance: {e}")
            return None

    async def transfer_tokens(
            self,
            from_address: str,
            to_address: str,
            amount: float,
            private_key: str
    ) -> bool:
        """Transfer tokens between addresses"""
        try:
            await self.ensure_connection()

            # Check balance
            balance = await self.get_balance(from_address)
            if balance is None or balance < amount:
                logger.error(f"Insufficient balance. Has: {balance}, Needs: {amount}")
                return False

            # Prepare transaction
            decimals = self.contract.functions.decimals().call()
            amount_wei = int(amount * (10 ** decimals))
            nonce = self.web3.eth.get_transaction_count(
                self.web3.to_checksum_address(from_address)
            )

            transfer_txn = self.contract.functions.transfer(
                self.web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': 100000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })

            signed_txn = self.web3.eth.account.sign_transaction(
                transfer_txn,
                private_key=private_key
            )

            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] == 1:
                logger.info(f"Transfer successful! Hash: {receipt['transactionHash'].hex()}")
                return True
            else:
                logger.error("Transfer failed: Transaction reverted")
                return False

        except Exception as e:
            logger.error(f"Error transferring tokens: {e}")
            return False