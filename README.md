
# Crypto Token Analyzer

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/nescatfe/token-analyzer)
![GitHub issues](https://img.shields.io/github/issues/nescatfe/token-analyzer)
![GitHub stars](https://img.shields.io/github/stars/nescatfe/token-analyzer)

## Description

The Crypto Token Analyzer is a powerful command-line tool designed to fetch and display information about cryptocurrency tokens across various networks. It provides real-time data analysis, wallet tracking, and market insights for crypto enthusiasts, traders, and researchers.

## Features

- **Token Analysis**: Analyze any token by its contract address, providing detailed information about price, liquidity, volume, and more.
- **Favorite Tokens**: Save and manage a list of favorite tokens for quick access and monitoring.
- **Wallet Analysis**: Track and analyze cryptocurrency wallets across different blockchains (Ethereum, Binance Smart Chain).
- **Top Cryptocurrencies**: View the top 10 cryptocurrencies by market cap with real-time data.
- **Real-time BTC and ETH Prices**: Display current Bitcoin and Ethereum prices in the main menu.
- **Ethereum Gas Prices**: Fetch and display real-time Ethereum gas prices, including low, standard, and fast gas prices, with estimated transaction times.
- **Multi-chain Support**: Supports Ethereum, Binance Smart Chain, and Solana networks.


This update reflects the new Ethereum gas price tracking feature you added. Let me know if there's anything else you'd like to modify!

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
