import os
from dotenv import load_dotenv

# Token Configuration (Humanity Token on Sepolia)
TOKEN_ADDRESS = "0xa42C8BDA1A7aFCe24894995bbB8F592B2129CdCe"

# ERC20 Token ABI
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Message Configuration
WORD_LIST = [
    "hello", "sun", "world", "space", "moon",
    "crypto", "sky", "ocean", "universe", "human"
]

# Time intervals
CHECK_BALANCE_INTERVAL = 10
MESSAGE_GENERATION_INTERVAL = 2

# Tenderly Configuration
TENDERLY_FORK_ID = os.getenv('TENDERLY_FORK_ID')
TENDERLY_ACCESS_KEY = os.getenv('TENDERLY_ACCESS_KEY')

# Gas settings
GAS_LIMIT = 100000