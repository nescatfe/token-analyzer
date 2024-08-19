import requests
import json
import os
import time
import pyperclip

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from datetime import datetime
from collections import defaultdict
from web3 import Web3

console = Console()


# ABI for ERC20 Token and Uniswap/PancakeSwap Router
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
ROUTER_ABI = json.loads('[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]')

# Router addresses
UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
PANCAKESWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
BSC_PROVIDER = "https://bsc-dataseed.binance.org/"

# API endpoints and keys (you should replace these with actual API keys)
ETHERSCAN_API = "https://api.etherscan.io/api"
BSCSCAN_API = "https://api.bscscan.com/api"
SOLSCAN_API = "https://public-api.solscan.io/account/transactions"

# Replace the placeholder API keys in the script with your own
ETHERSCAN_KEY = "YOUR_ETHERSCAN_API_KEY"
BSCSCAN_KEY = "YOUR_BSCSCAN_API_KEY"
ETH_PROVIDER = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"


# File to store favorite tokens
FAVORITES_FILE = "favorite_tokens.json"
WALLET_FAVORITES_FILE = "favorite_wallets.json"

def display_ascii_art():
    ascii_art = """
[bold cyan]
╔╦╗┌─┐┬┌─┌─┐┌┐┌  ╔═╗┌┐┌┌─┐┬ ┬ ┬┌─┐┌─┐┬─┐
 ║ │ │├┴┐├┤ │││  ╠═╣│││├─┤│ └┬┘┌─┘├┤ ├┬┘
 ╩ └─┘┴ ┴└─┘┘└┘  ╩ ╩┘└┘┴ ┴┴─┘┴ └─┘└─┘┴└─ v.1.2
by Malvidous | github/nescatfe
[/bold cyan]
    """
    print(ascii_art)
    
def load_favorite_wallets():
    if os.path.exists(WALLET_FAVORITES_FILE):
        with open(WALLET_FAVORITES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_favorite_wallets(favorites):
    with open(WALLET_FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)
        
def add_to_favorite_wallets(favorites, address, chain):
    favorites[address] = chain
    save_favorite_wallets(favorites)
    console.print(f"[bold green]Added {address} ({chain}) to favorite wallets![/bold green]")
    
def remove_from_favorite_wallets(favorites, address):
    if address in favorites:
        chain = favorites.pop(address)
        save_favorite_wallets(favorites)
        console.print(f"[bold yellow]Removed {address} ({chain}) from favorite wallets.[/bold yellow]")
    else:
        console.print("[bold red]Wallet address not found in favorites.[/bold red]")
        
def display_favorite_wallets(favorites):
    if not favorites:
        console.print("[yellow]No favorite wallets saved yet.[/yellow]")
        return
    
    table = Table(title="Favorite Wallets")
    table.add_column("#", style="cyan")
    table.add_column("Address", style="cyan")
    table.add_column("Chain", style="magenta")
    
    for i, (address, chain) in enumerate(favorites.items(), 1):
        table.add_row(str(i), address, chain)
        
    console.print(table)
    
def copy_to_clipboard(text):
    pyperclip.copy(text)
    console.print("[bold green]Copied to clipboard![/bold green]")
    
def fetch_token_transfers(address, chain):
    if chain == "eth":
        api_url = ETHERSCAN_API
        api_key = ETHERSCAN_KEY
    elif chain == "bsc":
        api_url = BSCSCAN_API
        api_key = BSCSCAN_KEY
    else:
        return None
    
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": api_key
    }
    
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            return data["result"][:25]  # Return only the latest 25 transactions
    return None

def get_wallet_balance(address, chain):
    if chain == "eth":
        api_url = f"{ETHERSCAN_API}?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_KEY}"
    elif chain == "bsc":
        api_url = f"{BSCSCAN_API}?module=account&action=balance&address={address}&tag=latest&apikey={BSCSCAN_KEY}"
    else:
        return None
    
    response = requests.get(api_url)
    data = response.json()
    if data["status"] == "1":
        return float(data["result"]) / 1e18
    return None

def get_solana_balance(address):
    api_url = f"https://public-api.solscan.io/account/{address}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return float(data["lamports"]) / 1e9
    return None

def categorize_transaction(tx, chain):
    w3 = Web3(Web3.HTTPProvider(ETH_PROVIDER if chain == "eth" else BSC_PROVIDER))
    
    if tx['to'].lower() == (UNISWAP_ROUTER if chain == "eth" else PANCAKESWAP_ROUTER).lower():
        router_contract = w3.eth.contract(address=w3.to_checksum_address(tx['to']), abi=ROUTER_ABI)
        try:
            decoded_input = router_contract.decode_function_input(tx['input'])
            func_name = decoded_input[0].fn_name
            func_params = decoded_input[1]
            
            if func_name in ['swapExactTokensForTokens', 'swapTokensForExactTokens', 'swapExactETHForTokens', 'swapETHForExactTokens', 'swapExactTokensForETH', 'swapTokensForExactETH']:
                token_path = func_params['path']
                token_in = get_token_info(w3, token_path[0]) if 'ETH' not in func_name.split('For')[0] else {'symbol': 'ETH' if chain == 'eth' else 'BNB'}
                token_out = get_token_info(w3, token_path[-1]) if 'ETH' not in func_name.split('For')[1] else {'symbol': 'ETH' if chain == 'eth' else 'BNB'}
                
                return f"Swapping {token_in['symbol']} for {token_out['symbol']}"
            
        except Exception as e:
            pass
            
    # Check for ERC20 token transfers
    try:
        token_contract = w3.eth.contract(address=w3.to_checksum_address(tx['to']), abi=ERC20_ABI)
        decoded_input = token_contract.decode_function_input(tx['input'])
        func_name = decoded_input[0].fn_name
        func_params = decoded_input[1]
        
        if func_name == 'transfer':
            token_info = get_token_info(w3, tx['to'])
            amount = func_params['_value'] / (10 ** token_info['decimals'])
            return f"Transferring {amount:.4f} {token_info['symbol']}"
    except Exception as e:
        pass
        
    if tx['input'] != "0x":
        return "Contract Interaction"
    elif float(tx['value']) > 0:
        return f"Sending {float(tx['value']) / 1e18:.4f} {'ETH' if chain == 'eth' else 'BNB'}"
    else:
        return "Other"
    
def get_token_info(w3, token_address):
    token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
    return {
        'symbol': token_contract.functions.symbol().call(),
        'decimals': token_contract.functions.decimals().call()
    }
    
def truncate_address(address):
    return f"{address[:6]}...{address[-6:]}"

def fetch_transactions(address, chain):
    transactions = []
    
    if chain == "eth":
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 10,
            "sort": "desc",
            "apikey": ETHERSCAN_KEY
        }
        response = requests.get(ETHERSCAN_API, params=params)
        data = response.json()
        if data["status"] == "1":
            transactions = data["result"]
            
    elif chain == "bsc":
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 10,
            "sort": "desc",
            "apikey": BSCSCAN_KEY
        }
        response = requests.get(BSCSCAN_API, params=params)
        data = response.json()
        if data["status"] == "1":
            transactions = data["result"]
            
    elif chain == "sol":
        params = {
            "account": address,
            "limit": 10
        }
        response = requests.get(SOLSCAN_API, params=params)
        if response.status_code == 200:
            transactions = response.json()
            
    return transactions

def display_transactions(transactions, chain, wallet_address):
    table = Table(title=f"Latest 25 Token Transfer Events ({chain.upper()})")
    table.add_column("#", style="cyan")
    table.add_column("Date", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("From", style="yellow")
    table.add_column("To", style="yellow")
    table.add_column("Token", style="green")
    table.add_column("Amount", style="blue", justify="right")
    table.add_column("Tx Hash", style="dim blue")
    
    for index, tx in enumerate(transactions, start=1):
        date = datetime.fromtimestamp(int(tx['timeStamp']))
        amount = int(float(tx['value']) / (10 ** int(tx['tokenDecimal'])))
        
        # Determine if it's a buy or sell/send transaction
        if tx['to'].lower() == wallet_address.lower():
            tx_type = "[green]BUY[/green]"
        else:
            tx_type = "[red]SELL[/red]"
            
        table.add_row(
            str(index),
            date.strftime("%b %d %H:%M"),
            tx_type,
            truncate_address(tx['from']),
            truncate_address(tx['to']),
            tx['tokenSymbol'],
            f"{amount:,}",
            truncate_address(tx['hash'])
        )
        
    console.print(table)
    return transactions  # Return transactions for later use


def display_wallet_balance(address, chain):
    balance = get_wallet_balance(address, chain)
    if balance is not None:
        console.print(f"\n[bold green]Current Wallet Balance:[/bold green] {balance:.4f} {'ETH' if chain == 'eth' else 'BNB'}")
    else:
        console.print("\n[bold red]Failed to fetch wallet balance.[/bold red]")
            
def wallet_transaction_analysis():
    favorite_wallets = load_favorite_wallets()
    
    while True:
        console.print("\n[bold cyan]Wallet Analysis Options:[/bold cyan]")
        console.print("[bold white]1.[/bold white] [yellow]Analyze a new wallet[/yellow]")
        console.print("[bold white]2.[/bold white] [yellow]View favorite wallets[/yellow]")
        console.print("[bold white]3.[/bold white] [yellow]Analyze a favorite wallet[/yellow]")
        console.print("[bold white]4.[/bold white] [yellow]Remove a favorite wallet[/yellow]")
        console.print("[bold white]5.[/bold white] [yellow]Return to main menu[/yellow]")
        
        choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4", "5"])
        
        
        if choice == "1":
            address = Prompt.ask("\nEnter the wallet address")
            chain = Prompt.ask("Enter the blockchain (eth/bsc)", choices=["eth", "bsc"])
            analyze_wallet(address, chain)
            
            if address not in favorite_wallets:
                if Prompt.ask("Add this wallet to favorites?", choices=["y", "n"], default="n") == "y":
                    add_to_favorite_wallets(favorite_wallets, address, chain)
                    
        elif choice == "2":
            display_favorite_wallets(favorite_wallets)
            
        elif choice == "3":
            display_favorite_wallets(favorite_wallets)
            if favorite_wallets:
                index = Prompt.ask("Enter the number of the wallet to analyze", default="1")
                if index.isdigit() and 1 <= int(index) <= len(favorite_wallets):
                    address = list(favorite_wallets.keys())[int(index) - 1]
                    chain = favorite_wallets[address]
                    analyze_wallet(address, chain)
                else:
                    console.print("[bold red]Invalid wallet number.[/bold red]")
                    
        elif choice == "4":
            display_favorite_wallets(favorite_wallets)
            if favorite_wallets:
                index = Prompt.ask("Enter the number of the wallet to remove", default="1")
                if index.isdigit() and 1 <= int(index) <= len(favorite_wallets):
                    address = list(favorite_wallets.keys())[int(index) - 1]
                    remove_from_favorite_wallets(favorite_wallets, address)
                else:
                    console.print("[bold red]Invalid wallet number.[/bold red]")
                    
        elif choice == "5":
            break
        
def analyze_wallet(address, chain):
    with console.status("[bold green]Fetching token transfer events..."):
        transactions = fetch_token_transfers(address, chain)
        
    if transactions:
        displayed_transactions = display_transactions(transactions, chain, address)
        display_wallet_balance(address, chain)
        
        while True:
            action = Prompt.ask("\nEnter a transaction number to copy its hash, or 'c' to continue", default="c")
            if action.lower() == 'c':
                break
            elif action.isdigit():
                tx_index = int(action) - 1
                if 0 <= tx_index < len(displayed_transactions):
                    tx_hash = displayed_transactions[tx_index]['hash']
                    copy_to_clipboard(tx_hash)
                else:
                    console.print("[bold red]Invalid transaction number.[/bold red]")
            else:
                console.print("[bold red]Invalid input. Please enter a number or 'c'.[/bold red]")
    else:
        console.print("[bold red]No token transfer events found or error occurred.[/bold red]")

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_favorites(favorites):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)

def fetch_dexscreener_data(token_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching data: {e}[/bold red]")
        return None

def display_token_info(token_data, pair_data):
    token_table = Table(show_header=False, box=None)
    token_table.add_row("Name", f"[cyan]{token_data['name']}[/cyan]")
    token_table.add_row("Symbol", f"[magenta]{token_data['symbol']}[/magenta]")
    token_table.add_row("Address", f"[green]{token_data['address']}[/green]")
    
    if 'fdv' in pair_data:
        token_table.add_row("Fully Diluted Valuation", f"${float(pair_data['fdv']):,.2f}")
    
    console.print(Panel(token_table, title="Token Information", expand=False))

def display_pair_info(pair_data):
    base_token = pair_data['baseToken']['symbol']
    quote_token = pair_data['quoteToken']['symbol']
    
    info_table = Table(show_header=False, box=None)
    info_table.add_row("Pair", f"[cyan]{base_token}/{quote_token}[/cyan]")
    info_table.add_row("DEX", f"[magenta]{pair_data['dexId'].capitalize()}[/magenta]")
    info_table.add_row("Chain", f"[green]{pair_data['chainId'].capitalize()}[/green]")
    info_table.add_row("Price (USD)", f"[yellow]${float(pair_data['priceUsd']):,.2f}[/yellow]")
    info_table.add_row("Price (Native)", f"[yellow]{float(pair_data['priceNative']):,.2f} {quote_token}[/yellow]")
    info_table.add_row("Pair Address", f"[blue]{pair_data['pairAddress']}[/blue]")
    info_table.add_row("DEX URL", f"[blue]{pair_data['url']}[/blue]")
    
    console.print(Panel(info_table, title="Pair Information", expand=False))

    # Price Changes
    changes_table = Table(title="Price Changes", show_header=True, header_style="bold blue")
    changes_table.add_column("Time Frame", style="cyan")
    changes_table.add_column("Change %", justify="right")
    for timeframe, change in pair_data['priceChange'].items():
        color = "green" if float(change) >= 0 else "red"
        changes_table.add_row(timeframe, f"[{color}]{float(change):+.2f}%[/{color}]")
    console.print(changes_table)

    # Liquidity
    liquidity = pair_data['liquidity']
    liquidity_table = Table(title="Liquidity", show_header=True, header_style="bold blue")
    liquidity_table.add_column("Metric", style="cyan")
    liquidity_table.add_column("Value", justify="right")
    liquidity_table.add_row("USD", f"${float(liquidity['usd']):,.2f}")
    liquidity_table.add_row(f"{base_token}", f"{float(liquidity['base']):,.2f}")
    liquidity_table.add_row(f"{quote_token}", f"{float(liquidity['quote']):,.2f}")
    console.print(liquidity_table)

    # Volume
    volume = pair_data['volume']
    volume_table = Table(title="Volume", show_header=True, header_style="bold blue")
    volume_table.add_column("Time Frame", style="cyan")
    volume_table.add_column("Volume (USD)", justify="right")
    for timeframe, value in volume.items():
        volume_table.add_row(timeframe, f"${float(value):,.2f}")
    console.print(volume_table)

    # Transactions
    txns = pair_data['txns']
    txns_table = Table(title="Transactions", show_header=True, header_style="bold blue")
    txns_table.add_column("Time Frame", style="cyan")
    txns_table.add_column("Buys", justify="right")
    txns_table.add_column("Sells", justify="right")
    for timeframe, data in txns.items():
        txns_table.add_row(timeframe, str(data['buys']), str(data['sells']))
    console.print(txns_table)

def add_to_favorites(favorites, token_address, token_name):
    favorites[token_address] = token_name
    save_favorites(favorites)
    console.print(f"[bold green]Added {token_name} to favorites![/bold green]")

def remove_from_favorites(favorites, token_address):
    if token_address in favorites:
        token_name = favorites.pop(token_address)
        save_favorites(favorites)
        console.print(f"[bold yellow]Removed {token_name} from favorites.[/bold yellow]")
    else:
        console.print("[bold red]Token not found in favorites.[/bold red]")

def display_favorites(favorites):
    if not favorites:
        console.print("[yellow]No favorites saved yet.[/yellow]")
        return

    table = Table(title="Favorite Tokens")
    table.add_column("#", style="cyan")
    table.add_column("Address", style="cyan")
    table.add_column("Name", style="magenta")
    
    for i, (address, name) in enumerate(favorites.items(), 1):
        table.add_row(str(i), address, name)
    
    console.print(table)

def scan_favorite_token(token_address):
    with Progress() as progress:
        task = progress.add_task("[green]Fetching data...", total=100)
        while not progress.finished:
            progress.update(task, advance=0.5)
            data = fetch_dexscreener_data(token_address)
            progress.update(task, completed=100)
    
    if data and 'pairs' in data and data['pairs']:
        pair_data = data['pairs'][0]
        token_data = pair_data['baseToken']
        return token_data, pair_data
    else:
        return None, None

def display_favorite_token_summary(address, name, pair_data):
    if pair_data:
        summary_table = Table(show_header=False, box=None)
        summary_table.add_row("Name", f"[cyan]{name}[/cyan]")
        summary_table.add_row("Address", f"[green]{address}[/green]")
        summary_table.add_row("Price", f"[yellow]${float(pair_data['priceUsd']):,.6f}[/yellow]")
        summary_table.add_row("24h Change", f"[{'green' if float(pair_data['priceChange']['h24']) >= 0 else 'red'}]{float(pair_data['priceChange']['h24']):+.2f}%[/{'green' if float(pair_data['priceChange']['h24']) >= 0 else 'red'}]")
        summary_table.add_row("Liquidity", f"${float(pair_data['liquidity']['usd']):,.2f}")
        summary_table.add_row("24h Volume", f"${float(pair_data['volume']['h24']):,.2f}")
        summary_table.add_row("24h Transactions", f"Buys: {pair_data['txns']['h24']['buys']}, Sells: {pair_data['txns']['h24']['sells']}")
        if 'fdv' in pair_data:
            summary_table.add_row("Market Cap (FDV)", f"${float(pair_data['fdv']):,.2f}")
        
        console.print(Panel(summary_table, title=f"Summary for {name}", expand=False))
    else:
        console.print(f"[bold red]Failed to fetch data for {name}[/bold red]")

def scan_all_favorites(favorites):
    for address, name in favorites.items():
        _, pair_data = scan_favorite_token(address)
        display_favorite_token_summary(address, name, pair_data)

def fetch_top_cryptocurrencies():
    url = "https://api.coincap.io/v2/assets?limit=10"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['data']
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching top cryptocurrencies: {e}[/bold red]")
        return None

def display_top_cryptocurrencies():
    cryptos = fetch_top_cryptocurrencies()
    if cryptos:
        table = Table(title="Top 10 Cryptocurrencies by Market Cap")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Name", style="magenta")
        table.add_column("Symbol", style="yellow")
        table.add_column("Price (USD)", style="green", justify="right")
        table.add_column("24h Change", style="blue", justify="right")
        table.add_column("Market Cap (USD)", style="red", justify="right")
        
        for crypto in cryptos:
            price_change = float(crypto['changePercent24Hr'])
            change_color = "green" if price_change >= 0 else "red"
            table.add_row(
                crypto['rank'],
                crypto['name'],
                crypto['symbol'],
                f"${float(crypto['priceUsd']):.2f}",
                f"[{change_color}]{price_change:.2f}%[/{change_color}]",
                f"${float(crypto['marketCapUsd']):,.0f}"
            )
            
        console.print(table)
    else:
        console.print("[bold red]Failed to fetch top cryptocurrencies data.[/bold red]")
        
def fetch_btc_eth_prices():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['bitcoin']['usd'], data['ethereum']['usd']
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching BTC and ETH prices: {e}[/bold red]")
        return None, None
    
def main():
    display_ascii_art()
    console.print("[bold green]Welcome to the Crypto Token Analyzer![/bold green]")
    console.print("This tool fetches and displays information about cryptocurrency tokens across various networks.")
    
    favorites = load_favorites()
    
    while True:
        btc_price, eth_price = fetch_btc_eth_prices()
        if btc_price and eth_price:
            console.print(f"\n[bold yellow]BTC: ${btc_price:,.2f}[/bold yellow] | [bold yellow]ETH: ${eth_price:,.2f}[/bold yellow]")
        else:
            console.print("\n[bold red]Unable to fetch BTC and ETH prices[/bold red]")
            
        console.print("\n[bold cyan]Main Menu:[/bold cyan]")
        console.print("[bold white]1.[/bold white] [yellow]Analyze Token[/yellow]")
        console.print("[bold white]2.[/bold white] [yellow]View favorites[/yellow]")
        console.print("[bold white]3.[/bold white] [yellow]Scan all favorite tokens[/yellow]")
        console.print("[bold white]4.[/bold white] [yellow]Analyze Wallets[/yellow]")
        console.print("[bold white]5.[/bold white] [yellow]View Top 10 Cryptocurrencies[/yellow]")
        console.print("[bold white]6.[/bold white] [yellow]Exit[/yellow]")
        
        choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            token_address = Prompt.ask("\n[bold cyan]Enter the token address[/bold cyan]")
            
            with Progress() as progress:
                task = progress.add_task("[green]Fetching data...", total=100)
                
                while not progress.finished:
                    progress.update(task, advance=0.5)
                    data = fetch_dexscreener_data(token_address)
                    progress.update(task, completed=100)
                    
            if data and 'pairs' in data and data['pairs']:
                pair_data = data['pairs'][0]
                token_data = pair_data['baseToken']
                
                display_token_info(token_data, pair_data)
                display_pair_info(pair_data)
                
                if token_address not in favorites:
                    if Prompt.ask("[bold cyan]Add this token to favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                        add_to_favorites(favorites, token_address, token_data['name'])
                else:
                    if Prompt.ask("[bold cyan]Remove this token from favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                        remove_from_favorites(favorites, token_address)
            else:
                console.print("[bold red]No data found for the given token address.[/bold red]")
                console.print("[yellow]Please check the address and try again.[/yellow]")
                
        elif choice == "2":
            display_favorites(favorites)
            if favorites:
                console.print("\n[bold cyan]Favorite Token Options:[/bold cyan]")
                console.print("[bold white]1.[/bold white] [yellow]Enter the number of a favorite token to analyze[/yellow]")
                console.print("[bold white]2.[/bold white] [yellow]Scan all favorite tokens[/yellow]")
                console.print("[bold white]3.[/bold white] [yellow]Remove a favorite token by number[/yellow]")
                console.print("[bold white]4.[/bold white] [yellow]Remove all favorite tokens[/yellow]")
                console.print("[bold white]5.[/bold white] [yellow]Return to the main menu[/yellow]")
                
                fav_choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4", "5"])
                
                if fav_choice == "1":
                    token_number = Prompt.ask("[bold cyan]Enter the number of the favorite token to analyze[/bold cyan]")
                    if token_number.isdigit():
                        index = int(token_number) - 1
                        if 0 <= index < len(favorites):
                            address = list(favorites.keys())[index]
                            token_data, pair_data = scan_favorite_token(address)
                            if token_data and pair_data:
                                display_token_info(token_data, pair_data)
                                display_pair_info(pair_data)
                            else:
                                console.print("[bold red]Failed to fetch data for the selected token.[/bold red]")
                        else:
                            console.print("[bold red]Invalid token number.[/bold red]")
                    else:
                        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
                        
                elif fav_choice == "2":
                    scan_all_favorites(favorites)
                    
                elif fav_choice == "3":
                    token_number = Prompt.ask("[bold cyan]Enter the number of the favorite token to remove[/bold cyan]")
                    if token_number.isdigit():
                        index = int(token_number) - 1
                        if 0 <= index < len(favorites):
                            address = list(favorites.keys())[index]
                            remove_from_favorites(favorites, address)
                        else:
                            console.print("[bold red]Invalid token number.[/bold red]")
                    else:
                        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
                        
                elif fav_choice == "4":
                    if Prompt.ask("[bold cyan]Are you sure you want to remove all favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                        favorites.clear()
                        save_favorites(favorites)
                        console.print("[bold yellow]All favorites have been removed.[/bold yellow]")
                        
                elif fav_choice == "5":
                    pass  # Return to main menu
                    
        elif choice == "3":
            scan_all_favorites(favorites)
        elif choice == "4":
            wallet_transaction_analysis()
        elif choice == "5":
            console.print("\n[bold cyan]Top 10 Cryptocurrencies by Market Cap:[/bold cyan]")
            display_top_cryptocurrencies()
            input("\nPress Enter to return to the main menu...")
        elif choice == "6":
            break
        
    console.print("[bold green]Thank you for using the Crypto Token Analyzer![/bold green]")
if __name__ == "__main__":
    main()
