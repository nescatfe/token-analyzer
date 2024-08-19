
# Crypto Token Analyzer

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/nescatfe/token-analyzer)
![GitHub issues](https://img.shields.io/github/issues/nescatfe/token-analyzer)
![GitHub stars](https://img.shields.io/github/stars/nescatfe/token-analyzer)

## Description

The Crypto Token Analyzer is a powerful command-line tool designed for cryptocurrency enthusiasts and traders. It provides real-time analysis of token data across various blockchain networks, leveraging the DexScreener API to fetch comprehensive information about cryptocurrency tokens and trading pairs.

Key features include:
- Real-time token analysis
- Favorite token management
- Batch scanning of favorite tokens
- Detailed metrics display including price, liquidity, volume, and transaction data
- User-friendly interface with rich text formatting

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/nescatfe/token-analyzer.git
   cd token-analyzer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line:

```
python token_analyzer.py
```

Follow the on-screen prompts to:
1. Analyze individual tokens
2. Manage your favorite tokens
3. Scan all your favorite tokens for quick updates

## Features

- **Token Analysis**: Enter any token address to get detailed information including price, liquidity, volume, and recent transactions.
- **Favorite Management**: Save tokens to your favorites list for quick access and batch scanning.
- **Batch Scanning**: Quickly scan all your favorite tokens to get an overview of their current status.
- **Rich Display**: Utilizes the `rich` library for a visually appealing and easy-to-read command-line interface.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for informational purposes only. Always conduct your own research before making any investment decisions.

## Acknowledgments

- [DexScreener API](https://docs.dexscreener.com/api/reference) for providing the token data
- [Rich library](https://github.com/Textualize/rich) for the beautiful command-line interface
