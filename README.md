
# Crypto Token Analyzer

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/nescatfe/token-analyzer)
![GitHub issues](https://img.shields.io/github/issues/nescatfe/token-analyzer)
![GitHub stars](https://img.shields.io/github/stars/nescatfe/token-analyzer)

## Description


# Crypto Token Analyzer

The Crypto Token Analyzer is a command-line interface (CLI) application written in Python. It utilizes various APIs and web3 libraries to fetch and display real-time information about cryptocurrencies, tokens, and blockchain wallets. The application is designed with a user-friendly interface using the Rich library for enhanced console output.

## Key Features:

### 1. Token Analysis:
- Fetch and display detailed information about any token using its address
- Show token price, liquidity, volume, and price changes
- Display top token holders and their shares

### 2. Wallet Analysis:
- Analyze wallet transactions across different blockchains (Ethereum, BSC)
- View token transfer events for a given wallet
- Display detailed transaction information

### 3. Favorites Management:
- Add tokens to a favorites list for quick access
- View and manage favorite tokens
- Scan all favorite tokens to see price changes and updates

### 4. Top Cryptocurrencies:
- Display the top 10 cryptocurrencies by market cap
- Show price changes and market cap information

### 5. Ethereum Gas Prices:
- Fetch and display current Ethereum gas prices
- Show estimated transaction costs for different types of operations

### 6. Meme Token Search:
- Search for meme tokens using keywords
- Display search results with key metrics
- Analyze selected meme tokens in detail

### 7. Multi-chain Support:
- Support for multiple blockchains including Ethereum, Binance Smart Chain, and Polygon

### 8. Real-time Data:
- Fetch real-time price data for Bitcoin and Ethereum
- Use various APIs (DexScreener, CoinGecko, CoinCap) for up-to-date information

### 9. Transaction Decoding:
- Decode and interpret common transaction types (swaps, transfers, approvals)

### 10. User-friendly Interface:
- Clear menu structure for easy navigation
- Colorful and formatted output using Rich library
- Progress bars for data fetching operations

### 11. Persistent Storage:
- Save favorite tokens and wallets for future sessions
- Track price changes between scans

This application serves as a powerful tool for cryptocurrency enthusiasts, traders, and analysts to quickly gather and analyze information about various tokens, track their favorites, and stay updated on market trends. The modular structure of the code allows for easy expansion and addition of new features in the future.

## Installation

1. Ensure you have Python 3.7 or later installed on your system.

2. Clone this repository:
```
git clone https://github.com/nescatfe/token-analyzer.git
```

3. Navigate to the project directory:
```
cd crypto-token-analyzer
```

4. Install the required dependencies:
```
pip install -r requirements.txt
```

## Dependencies

This project relies on the following Python packages:

- requests
- web3
- rich
- pyperclip

These dependencies are listed in the `requirements.txt` file and will be installed when you follow the installation instructions above.

## Usage

Run the application by executing:

```
python token_analyzer.py
```

Follow the on-screen prompts to navigate through different features:

1. Analyze a token
2. View favorites
3. Scan all favorite tokens
4. Analyze Wallets
5. View Top 10 Cryptocurrencies

## API Keys

This application uses various APIs to fetch cryptocurrency data. You'll need to obtain API keys from the following services and add them to the script:

- Etherscan: https://etherscan.io/apis
- BscScan: https://bscscan.com/apis
- Infura (for Ethereum provider): https://infura.io/

Replace the placeholder API keys in the script with your own:

```python
ETHERSCAN_KEY = "YOUR_ETHERSCAN_API_KEY"
BSCSCAN_KEY = "YOUR_BSCSCAN_API_KEY"
ETH_PROVIDER = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
```

## Configuration

The application stores favorite tokens and wallets in JSON files:

- `favorite_tokens.json`: Stores your favorite token addresses and names.
- `favorite_wallets.json`: Stores your favorite wallet addresses and their associated chains.

These files will be created automatically when you add favorites through the application.

## License

This project is [MIT](https://github.com/nescatfe/token-analyzer/blob/main/LICENSE) licensed.

## Disclaimer

This tool is for informational purposes only. It is not financial advice. Always do your own research before making any investment decisions. The developers of this tool are not responsible for any financial losses incurred through the use of this software.
