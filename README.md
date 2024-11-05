# Autonomous Agent System

A Python-based autonomous agent system that demonstrates asynchronous communication and blockchain interaction capabilities.

## Prerequisites

- Python 3.8+
- Git
- Access to Ethereum testnet (Sepolia)
- Ethereum wallet with test tokens

## Quick Start

1. **Clone the Repository**
```bash
git clone https://github.com/DimitriMavrick/Autonomous-Agent
cd Autonomous_Agent
```

2. **Set Up Virtual Environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values:
# - Add your Tenderly fork URL
# - Add your contract address
# - Add wallet addresses
# - Add private key (never commit this!)
```

5. **Run the System**
```bash
python src/main.py
```

## Project Structure
```
├── src/
│   ├── __init__.py
│   ├── agent.py        # Core agent implementation
│   ├── behaviors.py    # Agent behaviors
│   ├── handlers.py     # Message handlers
│   ├── main.py        # Main execution
│   └── utils/
│       ├── __init__.py
│       └── web3_utils.py
├── tests/
│   └── test_agent.py   # Test suite
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Configuration

The system requires several environment variables to be set in your `.env` file:

```env
# Required variables:
TENDERLY_FORK_RPC_URL=       # Your Tenderly fork URL
ERC20_CONTRACT_ADDRESS=      # Token contract address
SOURCE_WALLET_ADDRESS=       # Your wallet address
TARGET_WALLET_ADDRESS=       # Target wallet for transfers
SOURCE_WALLET_PRIVATE_KEY=   # Your wallet private key (keep secure!)

# Optional RPC URLs for fallback:
INFURA_RPC_URL=             # Your Infura endpoint
ALCHEMY_RPC_URL=            # Your Alchemy endpoint
```

## Testing

Run the test suite:
```bash
# Run all tests
pytest tests/test_agent.py

# Run with verbose output
pytest -v tests/test_agent.py

# Run with coverage report
pytest --cov=src tests/test_agent.py
```

## Features

- Asynchronous message processing
- ERC-20 token balance monitoring
- Automatic token transfers
- Random message generation
- Message filtering system

## Development

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Include docstrings

2. **Testing**
   - Write tests for new features
   - Ensure all tests pass before committing
   - Maintain test coverage

3. **Security**
   - Never commit private keys or sensitive data
   - Use environment variables for configuration
   - Follow Web3 security best practices

## Troubleshooting

1. **Connection Issues**
   - Verify RPC URLs in .env
   - Check network connectivity
   - Ensure Tenderly fork is active

2. **Transaction Failures**
   - Check wallet balances
   - Verify contract addresses
   - Ensure proper network setup

3. **Test Failures**
   - Check environment setup
   - Verify mock configurations
   - Ensure async operations are handled properly

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

Please DO NOT commit any private keys or sensitive information. Use environment variables for all sensitive data.