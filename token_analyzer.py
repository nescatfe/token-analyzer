import requests
import json
import os
import sys
import time
import pyperclip
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from datetime import datetime, timedelta
from collections import defaultdict
from web3 import Web3
from solana.rpc.async_api import AsyncClient
import asyncio

# Load ABIs
with open('erc20_abi.json') as f:
    ERC20_ABI = json.load(f)
with open('router_abi.json') as f:
    ROUTER_ABI = json.load(f)
    
console = Console()
ETH_PROVIDER = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
BSC_PROVIDER = "https://bsc-dataseed.binance.org/"
UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
PANCAKESWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
ETHERSCAN_API = "https://api.etherscan.io/api"
BSCSCAN_API = "https://api.bscscan.com/api"
SOLSCAN_API = "https://public-api.solscan.io/account/transactions"
ETHERSCAN_KEY = "YOUR_ETHERSCAN_API_KEY"
BSCSCAN_KEY = "YOUR_BSC_API_KEY"
POLYGON_KEY = "YOUR_POLYGON_API_KEY"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"
ETHEREUM_GAS_LIMIT = 21000
FAVORITES_FILE = "favorite_tokens.json"
WALLET_FAVORITES_FILE = "favorite_wallets.json"

# Gas limit estimates for different transaction types
GAS_LIMITS = {
    "Swap": 356190,
    "Bridging": 114000,
    "NFT Sale": 600000,
    "Borrowing": 302000
}

def display_ascii_art():
    ascii_art = """
[bold cyan]
╔╦╗┌─┐┬┌─┌─┐┌┐┌  ╔═╗┌┐┌┌─┐┬ ┬ ┬┌─┐┌─┐┬─┐
 ║ │ │├┴┐├┤ │││  ╠═╣│││├─┤│ └┬┘┌─┘├┤ ├┬┘
 ╩ └─┘┴ ┴└─┘┘└┘  ╩ ╩┘└┘┴ ┴┴─┘┴ └─┘└─┘┴└─ v.1.4
by Malvidous | github/nescatfe
[/bold cyan]
    """
    print(ascii_art)

#----- ABE NEW FUNCTION HERE -----#

def decode_input_data(input_data, chain):
    # Add more common function signatures here
    function_signatures = {
        "0x38ed1739": "swapExactTokensForTokens",
        "0x7ff36ab5": "swapExactETHForTokens",
        "0x18cbafe5": "swapExactTokensForETH",
        "0xfb3bdb41": "swapETHForExactTokens",
        "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens",
        "0xa9059cbb": "transfer",
        "0x23b872dd": "transferFrom",
        "0x095ea7b3": "approve",
    }
    
    if len(input_data) < 10:
        return "Unknown Function"
    
    function_signature = input_data[:10]
    return function_signatures.get(function_signature, "Unknown Function")

def get_token_info(address, chain):
    if chain.lower() in ['ethereum', 'eth']:
        w3 = Web3(Web3.HTTPProvider(ETH_PROVIDER))
    elif chain.lower() in ['binance', 'bsc', 'bnb']:
        w3 = Web3(Web3.HTTPProvider(BSC_PROVIDER))
    else:
        return {"symbol": "UNKNOWN", "decimals": 18, "name": "Unknown Token"}

    try:
        token_contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_ABI)
        
        # Try to get symbol, name, and decimals with fallbacks
        try:
            symbol = token_contract.functions.symbol().call()
        except:
            symbol = "UNKNOWN"

        try:
            name = token_contract.functions.name().call()
        except:
            name = "Unknown Token"

        try:
            decimals = token_contract.functions.decimals().call()
        except:
            decimals = 18

        return {
            "symbol": symbol,
            "decimals": decimals,
            "name": name
        }
    except Exception as e:
        console.print(f"[bold yellow]Warning: Could not fetch complete token info: {str(e)}[/bold yellow]")
        return {"symbol": "UNKNOWN", "decimals": 18, "name": "Unknown Token"}

def display_transaction_details(tx, chain, wallet_address):
    tx_hash = tx['hash']
    if chain == 'eth':
        api_base = ETHERSCAN_API
        api_key = ETHERSCAN_KEY
        explorer_base = "https://etherscan.io/tx/"
    elif chain == 'bsc':
        api_base = BSCSCAN_API
        api_key = BSCSCAN_KEY
        explorer_base = "https://bscscan.com/tx/"
    else:
        console.print(f"[red]Unsupported chain: {chain}[/red]")
        return
    
    # Fetch transaction details
    tx_url = f"{api_base}?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={api_key}"
    tx_response = requests.get(tx_url)
    
    # Fetch transaction receipt
    receipt_url = f"{api_base}?module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}&apikey={api_key}"
    receipt_response = requests.get(receipt_url)
    
    if tx_response.status_code == 200 and receipt_response.status_code == 200:
        tx_data = tx_response.json().get('result', {})
        receipt_data = receipt_response.json().get('result', {})
        
        if tx_data and receipt_data:
            # Create a table to display transaction details
            table = Table(title=f"Transaction Details for {tx_hash}")
            table.add_column("Field", style="cyan", width=30)
            table.add_column("Value", style="yellow")
            
            # Transaction type and status
            tx_type = "IN" if tx['to'].lower() == wallet_address.lower() else "OUT"
            status = "Success" if receipt_data.get('status') == '0x1' else "Failed"
            table.add_row("Type", f"[{'green' if tx_type == 'IN' else 'red'}]{tx_type}[/{'green' if tx_type == 'IN' else 'red'}]")
            table.add_row("Status", f"[{'green' if status == 'Success' else 'red'}]{status}[/{'green' if status == 'Success' else 'red'}]")
            
            # Token information
            table.add_row("Token Name", tx['tokenName'])
            table.add_row("Token Symbol", tx['tokenSymbol'])
            table.add_row("Token Decimals", tx['tokenDecimal'])
            table.add_row("Amount", f"{float(tx['value']) / (10 ** int(tx['tokenDecimal'])):.6f} {tx['tokenSymbol']}")
            
            # Basic transaction details
            table.add_row("From", tx_data.get('from', 'Unknown'))
            table.add_row("To", tx_data.get('to', 'Unknown'))
            table.add_row("Native Value", f"{Web3.from_wei(int(tx_data.get('value', '0'), 16), 'ether'):.18f} {'ETH' if chain == 'eth' else 'BNB'}")
            table.add_row("Gas Price", f"{Web3.from_wei(int(tx_data.get('gasPrice', '0'), 16), 'gwei'):.2f} Gwei")
            table.add_row("Gas Limit", str(int(tx_data.get('gas', '0'), 16)))
            table.add_row("Nonce", str(int(tx_data.get('nonce', '0'), 16)))
            
            # Transaction receipt details
            table.add_row("Gas Used", str(int(receipt_data.get('gasUsed', '0'), 16)))
            table.add_row("Block Number", str(int(receipt_data.get('blockNumber', '0'), 16)))
            table.add_row("Block Hash", receipt_data.get('blockHash', 'Unknown'))
            
            # Calculate transaction fee
            gas_price = Web3.from_wei(int(tx_data.get('gasPrice', '0'), 16), 'ether')
            gas_used = int(receipt_data.get('gasUsed', '0'), 16)
            tx_fee = gas_price * gas_used
            table.add_row("Transaction Fee", f"{tx_fee:.8f} {'ETH' if chain == 'eth' else 'BNB'}")
            
            # Add transaction timestamp if available
            if 'timeStamp' in tx:
                tx_time = datetime.fromtimestamp(int(tx['timeStamp']))
                table.add_row("Timestamp", tx_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Add explorer link
            table.add_row("Explorer Link", f"{explorer_base}{tx_hash}")
            
            # Interpret transaction
            input_data = tx_data.get('input', '')
            function_name = decode_input_data(input_data, chain)
            
            if function_name in ["swapExactTokensForTokens", "swapExactETHForTokens", "swapExactTokensForETH", "swapETHForExactTokens"]:
                # Interpret swap transaction
                from_token = get_token_info(tx_data.get('from'), chain)
                to_token = get_token_info(receipt_data.get('to'), chain)
                
                from_amount = Web3.from_wei(int(tx_data.get('value', '0'), 16), 'ether')
                to_amount = float(tx.get('value', '0')) / (10 ** int(tx.get('tokenDecimal', '18')))
                
                if function_name == "swapExactETHForTokens":
                    interpretation = f"Swapped {from_amount:.6f} {'ETH' if chain == 'eth' else 'BNB'} for {to_amount:.6f} {tx['tokenSymbol']}"
                elif function_name == "swapExactTokensForETH":
                    interpretation = f"Swapped {to_amount:.6f} {tx['tokenSymbol']} for {from_amount:.6f} {'ETH' if chain == 'eth' else 'BNB'}"
                else:
                    interpretation = f"Swapped {from_amount:.6f} {from_token['symbol']} for {to_amount:.6f} {to_token['symbol']}"
            elif function_name == "transfer":
                amount = float(tx.get('value', '0')) / (10 ** int(tx.get('tokenDecimal', '18')))
                interpretation = f"Transferred {amount:.6f} {tx['tokenSymbol']} to {tx_data.get('to', 'Unknown')}"
            elif function_name == "approve":
                amount = Web3.from_wei(int(input_data[74:138], 16), 'ether')
                spender = "0x" + input_data[34:74]
                interpretation = f"Approved {amount:.6f} {tx['tokenSymbol']} to be spent by {spender}"
            else:
                interpretation = f"Executed {function_name} function"
            
            table.add_row("Transaction Type", interpretation)
            
            console.print(table)
            

def format_token_share(share_str):
    try:
        share = float(share_str)
        if share > 100:
            share /= 100
        return f"{share:.4f}%"
    except ValueError:
        return share_str  

def fetch_top_token_holders(token_address, chain):
    try:
        if chain.lower() in ['ethereum', 'eth']:
            api_url = f"https://api.ethplorer.io/getTopTokenHolders/{token_address}?apiKey=freekey&limit=10"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return [{'address': h['address'], 'share': h['share']} for h in data.get('holders', [])]
        elif chain.lower() in ['binance', 'bsc', 'bnb']:
            api_url = f"https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress={token_address}&page=1&offset=10&apikey={BSCSCAN_KEY}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1' and 'result' in data:
                    return [{'address': h['HolderAddress'], 'share': float(h['PercentHeld'])} for h in data['result']]
        elif chain.lower() in ['polygon', 'matic']:
            api_url = f"https://api.polygonscan.com/api?module=token&action=tokenholderlist&contractaddress={token_address}&page=1&offset=10&apikey={POLYGON_KEY}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1' and 'result' in data:
                    return [{'address': h['HolderAddress'], 'share': float(h['PercentHeld'])} for h in data['result']]
    except Exception as e:
        console.print(f"[bold red]Error fetching top token holders for {chain} chain: {str(e)}[/bold red]")
        
    return None

def fetch_eth_gas_prices():
    etherscan_url = f"{ETHERSCAN_API}?module=gastracker&action=gasoracle&apikey={ETHERSCAN_KEY}"
    
    try:
        response = requests.get(etherscan_url)
        response.raise_for_status()
        data = response.json()
        return data["result"]
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching ETH gas prices: {e}[/bold red]")
        return None
    
def fetch_eth_price():
    try:
        response = requests.get(f"{COINGECKO_API}?ids=ethereum&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        return data['ethereum']['usd']
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching ETH price: {e}[/bold red]")
        return None
    
def gwei_to_eth(gwei):
    return float(gwei) * (10 ** -9)

def calculate_gas_cost_in_usd(gas_price_gwei, eth_price_usd, gas_limit):
    eth_cost = gwei_to_eth(gas_price_gwei) * gas_limit
    return eth_cost * eth_price_usd

def display_eth_gas_prices():
    gas_data = fetch_eth_gas_prices()
    eth_price_usd = fetch_eth_price()
    
    if gas_data and eth_price_usd:
        # Calculate USD costs for different gas tiers and transaction types
        usd_costs = {
            "Low": {},
            "Standard": {},
            "Fast": {}
        }
        
        for tier, gas_price_key in [("Low", "SafeGasPrice"), ("Standard", "ProposeGasPrice"), ("Fast", "FastGasPrice")]:
            gas_price_gwei = float(gas_data[gas_price_key])
            for tx_type, gas_limit in GAS_LIMITS.items():
                usd_costs[tier][tx_type] = calculate_gas_cost_in_usd(gas_price_gwei, eth_price_usd, gas_limit)
                
        # Gas Price Table
        gas_table = Table(title="Ethereum Gas Prices")
        gas_table.add_column("Priority", style="cyan")
        gas_table.add_column("Gas Price (Gwei)", style="yellow")
        gas_table.add_column("Cost in USD (ETH Transfer)", style="green")
        gas_table.add_column("Estimated Time", style="magenta")
        
        low_gas_usd = calculate_gas_cost_in_usd(gas_data['SafeGasPrice'], eth_price_usd, 21000)
        standard_gas_usd = calculate_gas_cost_in_usd(gas_data['ProposeGasPrice'], eth_price_usd, 21000)
        fast_gas_usd = calculate_gas_cost_in_usd(gas_data['FastGasPrice'], eth_price_usd, 21000)
        
        gas_table.add_row("Low", gas_data['SafeGasPrice'], f"${low_gas_usd:.2f}", "< 15 minutes")
        gas_table.add_row("Standard", gas_data['ProposeGasPrice'], f"${standard_gas_usd:.2f}", "< 5 minutes")
        gas_table.add_row("Fast", gas_data['FastGasPrice'], f"${fast_gas_usd:.2f}", "< 1 minute")
        
        console.print(gas_table)
        
        # Transaction Type Costs Table
        tx_table = Table(title="Estimated Transaction Costs (USD)")
        tx_table.add_column("Transaction Type", style="cyan")
        tx_table.add_column("Low Priority", style="green")
        tx_table.add_column("Standard Priority", style="yellow")
        tx_table.add_column("Fast Priority", style="red")
        
        for tx_type in GAS_LIMITS.keys():
            tx_table.add_row(
                tx_type,
                f"${usd_costs['Low'][tx_type]:.2f}",
                f"${usd_costs['Standard'][tx_type]:.2f}",
                f"${usd_costs['Fast'][tx_type]:.2f}"
            )
            
        console.print(tx_table)
        
        # Additional Information
        info_table = Table(show_header=False, box=None)
        info_table.add_row("Base Fee:", f"[yellow]{gas_data['suggestBaseFee']} Gwei[/yellow]")
        info_table.add_row("Last Block:", f"[green]{gas_data['LastBlock']}[/green]")
        
        now = datetime.now()
        info_table.add_row("Last Updated:", f"[magenta]{now.strftime('%Y-%m-%d %H:%M:%S')}[/magenta]")
        
        console.print(Panel(info_table, title="Additional Information", expand=False))
        
        # Historical comparison
        if 'LastBlock' in gas_data and 'suggestBaseFee' in gas_data:
            blocks_per_day = 24 * 60 * 60 / 12  # Approximate number of blocks per day
            estimated_daily_base_fee = float(gas_data['suggestBaseFee']) * blocks_per_day
            console.print(f"\n[bold yellow]Estimated daily base fee burn:[/bold yellow] {estimated_daily_base_fee:.2f} ETH")
            
        # Gas price volatility warning
        console.print("\n[bold red]Note:[/bold red] Gas prices can be highly volatile. Always check current prices before sending a transaction.")
        
    else:
        console.print("[bold red]Failed to fetch Ethereum gas prices or ETH price.[/bold red]")
        
        
def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls') 
    else:
        os.system('clear')  
        
def save_favorite_wallets(favorites):
    with open(WALLET_FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)
        
def load_favorite_wallets():
    if os.path.exists(WALLET_FAVORITES_FILE):
        with open(WALLET_FAVORITES_FILE, 'r') as f:
            return json.load(f)
    return {}
        
def add_to_favorite_wallets(favorites, address, chain):
    nickname = Prompt.ask("Enter a nickname for this wallet (optional)", default="")
    favorites[address] = {'chain': chain, 'nickname': nickname}
    save_favorite_wallets(favorites)
    console.print(f"[bold green]Added {address} ({chain}) to favorite wallets with nickname: {nickname or 'N/A'}![/bold green]")
    
def remove_from_favorite_wallets(favorites, address):
    if address in favorites:
        data = favorites.pop(address)
        save_favorite_wallets(favorites)
        console.print(f"[bold yellow]Removed {address} ({data['chain']}) from favorite wallets.[/bold yellow]")
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
    table.add_column("Nickname", style="green")
    
    for i, (address, data) in enumerate(favorites.items(), 1):
        chain = data['chain']
        nickname = data.get('nickname', 'N/A') 
        table.add_row(str(i), address, chain, nickname)
        
    console.print(table)
    
def copy_to_clipboard(text):
    pyperclip.copy(text)
    console.print("[bold green]Copied to clipboard![/bold green]")
    
def fetch_token_transfers(address, chain, start=0, limit=30):
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
        "offset": limit,
        "page": start // limit + 1,
        "apikey": api_key
    }
    
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            return data["result"]
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
    
def truncate_address(address):
    return f"{address[:6]}...{address[-6:]}"

def display_transactions(transactions, chain, wallet_address, start=0):
    table = Table(title=f"Token Transfer Events ({chain.upper()}) - Showing {start+1} to {start+len(transactions)}")
    table.add_column("#", style="cyan")
    table.add_column("Date", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("From", style="yellow")
    table.add_column("To", style="yellow")
    table.add_column("Token", style="green")
    table.add_column("Amount", style="blue", justify="right")
    table.add_column("Tx Hash", style="dim blue")
    
    for index, tx in enumerate(transactions, start=start+1):
        date = datetime.fromtimestamp(int(tx['timeStamp']))
        amount = float(tx['value']) / (10 ** int(tx['tokenDecimal']))
        
        # Determine if it's a buy or sell/send transaction
        if tx['to'].lower() == wallet_address.lower():
            tx_type = "[green]IN[/green]"
        else:
            tx_type = "[red]OUT[/red]"
        
        table.add_row(
            str(index),
            date.strftime("%b %d %H:%M"),
            tx_type,
            truncate_address(tx['from']),
            truncate_address(tx['to']),
            tx['tokenSymbol'],
            f"{amount:,.4f}",
            truncate_address(tx['hash'])
        )
        
    console.print(table)
    return transactions

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
        
        choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]")
        
        
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
                    chain = favorite_wallets[address]['chain']
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
            clear_screen()
            break
        
def analyze_wallet(address, chain):
    start = 0
    limit = 30
    all_transactions = []

    while True:
        with console.status("[bold green]Fetching token transfer events..."):
            transactions = fetch_token_transfers(address, chain, start, limit)
        
        if transactions:
            all_transactions.extend(transactions)
            displayed_transactions = display_transactions(transactions, chain, address, start)
            display_wallet_balance(address, chain)
            
            while True:
                action = Prompt.ask("\nEnter a transaction number to view details, 'm' for more transactions, or 'c' to continue")
                if action.lower() == 'c':
                    return
                elif action.lower() == 'm':
                    start += limit
                    break
                elif action.isdigit():
                    tx_index = int(action) - 1
                    if 0 <= tx_index < len(all_transactions):
                        tx = all_transactions[tx_index]
                        display_transaction_details(tx, chain, address)
                    else:
                        console.print("[bold red]Invalid transaction number.[/bold red]")
                else:
                    console.print("[bold red]Invalid input. Please enter a number, 'm', or 'c'.[/bold red]")
        else:
            if start == 0:
                console.print("[bold red]No token transfer events found or error occurred.[/bold red]")
            else:
                console.print("[bold yellow]No more transactions to display.[/bold yellow]")
            break

def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    return {}

def update_last_scan_price(favorites, token_address, current_price):
    if token_address in favorites:
        favorites[token_address]['last_scan_price'] = current_price
        favorites[token_address]['last_scan_time'] = datetime.now().isoformat()
    save_favorites(favorites)
    
def save_favorites(favorites):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f, indent=2)

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
    info_table.add_row("Price (USD)", f"[yellow]${float(pair_data['priceUsd']):,.9f}[/yellow]")
    info_table.add_row("Price (Native)", f"[yellow]{float(pair_data['priceNative']):,.9f} {quote_token}[/yellow]")
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

    # Token Holders
    token_address = pair_data['baseToken']['address']
    chain = pair_data['chainId']
    top_holders = fetch_top_token_holders(token_address, chain)
    
    if top_holders:
        holders_table = Table(title=f"Top 10 Token Holders ({chain.upper()})", show_header=True, header_style="bold blue")
        holders_table.add_column("Rank", style="cyan", justify="right")
        holders_table.add_column("Address", style="green")
        holders_table.add_column("Share", style="magenta", justify="right")
        
        for i, holder in enumerate(top_holders, 1):
            holders_table.add_row(
                str(i),
                holder['address'],
                format_token_share(holder['share'])
            )
            
        console.print(holders_table)
    else:
        console.print(f"[yellow]Unable to fetch or display top token holders for {chain} chain. This may be due to API limitations or the token contract not supporting this feature.[/yellow]")
        
def add_to_favorites(favorites, token_address, token_name, current_price, current_fdv=None):
    favorites[token_address] = {
        'name': token_name,
        'last_scan_price': current_price,
        'last_scan_time': datetime.now().isoformat(),
    }
    if current_fdv is not None:
        favorites[token_address]['last_scan_fdv'] = current_fdv
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
    table.add_column("Last Scan Price", style="yellow")
    table.add_column("Last Scan Time", style="green")
    
    for i, (address, data) in enumerate(favorites.items(), 1):
        # Parse and format the last scan time
        last_scan_time = datetime.fromisoformat(data['last_scan_time'])
        formatted_time = last_scan_time.strftime("%b %d, %H:%M")
        
        table.add_row(
            str(i),
            address,
            data['name'],
            f"${data['last_scan_price']:.8f}",
            formatted_time
        )
        
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


def display_favorite_token_summary(favorites, address, data, pair_data):
    if pair_data:
        current_price = float(pair_data['priceUsd'])
        last_price = float(data['last_scan_price'])
        price_change = ((current_price - last_price) / last_price) * 100
        
        # Parse the last scan time and format it
        last_scan_time = datetime.fromisoformat(data['last_scan_time'])
        formatted_time = last_scan_time.strftime("%b %d, %H:%M")
        
        summary_table = Table(show_header=False, box=None)
        summary_table.add_row("Name", f"[cyan]{data['name']}[/cyan]")
        summary_table.add_row("Address", f"[green]{address}[/green]")
        summary_table.add_row("Current Price", f"[yellow]${current_price:.9f}[/yellow]")
        summary_table.add_row("Last Scan Price", f"[yellow]${last_price:.9f}[/yellow]")
        summary_table.add_row("Last Scan Time", f"[blue]{formatted_time}[/blue]")
        summary_table.add_row("Price Change", f"[{'green' if price_change >= 0 else 'red'}]{price_change:+.2f}%[/{'green' if price_change >= 0 else 'red'}]")
        summary_table.add_row("24h Change", f"[{'green' if float(pair_data['priceChange']['h24']) >= 0 else 'red'}]{float(pair_data['priceChange']['h24']):+.2f}%[/{'green' if float(pair_data['priceChange']['h24']) >= 0 else 'red'}]")
        summary_table.add_row("Liquidity", f"${float(pair_data['liquidity']['usd']):,.2f}")
        summary_table.add_row("24h Volume", f"${float(pair_data['volume']['h24']):,.2f}")
        summary_table.add_row("24h Transactions", f"Buys: {pair_data['txns']['h24']['buys']}, Sells: {pair_data['txns']['h24']['sells']}")
        
        if 'fdv' in pair_data:
            current_fdv = float(pair_data['fdv'])
            last_fdv = data.get('last_scan_fdv', current_fdv)  # Default to current if last_scan_fdv doesn't exist
            fdv_change = current_fdv - last_fdv
            fdv_color = 'green' if fdv_change >= 0 else 'red'
            summary_table.add_row("Market Cap (FDV)", f"${current_fdv:,.2f} [{fdv_color}]({fdv_change:+,.2f})[/{fdv_color}]")
            
        console.print(Panel(summary_table, title=f"Summary for {data['name']}", expand=False))
        
        # Update the last scan price and FDV
        update_last_scan_data(favorites, address, current_price, current_fdv if 'fdv' in pair_data else None)
    else:
        console.print(f"[bold red]Failed to fetch data for {data['name']}[/bold red]")
        
def update_last_scan_data(favorites, token_address, current_price, current_fdv=None):
    if token_address in favorites:
        favorites[token_address]['last_scan_price'] = current_price
        favorites[token_address]['last_scan_time'] = datetime.now().isoformat()
        if current_fdv is not None:
            favorites[token_address]['last_scan_fdv'] = current_fdv
    save_favorites(favorites)
        
        
def scan_all_favorites(favorites):
    for address, data in favorites.items():
        _, pair_data = scan_favorite_token(address)
        display_favorite_token_summary(favorites, address, data, pair_data)

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

def load_last_scanned_prices():
    if os.path.exists('last_scanned_prices.json'):
        with open('last_scanned_prices.json', 'r') as f:
            return json.load(f)
    return {}

def save_last_scanned_prices(prices):
    with open('last_scanned_prices.json', 'w') as f:
        json.dump(prices, f)

def display_top_cryptocurrencies():
    cryptos = fetch_top_cryptocurrencies()
    last_scanned = load_last_scanned_prices()
    current_time = datetime.now()
    
    if cryptos:
        table = Table(title="Top 10 Cryptocurrencies by Market Cap")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Name", style="magenta")
        table.add_column("Symbol", style="yellow")
        table.add_column("Price (USD)", style="green", justify="right")
        table.add_column("24h Change", style="blue", justify="right")
        table.add_column("Market Cap (USD)", style="red", justify="right")
        table.add_column("Last Scanned Price", style="yellow", justify="right")
        table.add_column("Price Change", style="cyan", justify="right")
        
        new_prices = {}
        for crypto in cryptos:
            symbol = crypto['symbol']
            current_price = float(crypto['priceUsd'])
            new_prices[symbol] = {'price': current_price, 'time': current_time.isoformat()}
            
            last_price = last_scanned.get(symbol, {}).get('price', current_price)
            last_time = last_scanned.get(symbol, {}).get('time', current_time.isoformat())
            
            price_change = ((current_price - last_price) / last_price) * 100 if last_price else 0
            price_change_24h = float(crypto['changePercent24Hr'])
            
            change_color = "green" if price_change_24h >= 0 else "red"
            price_change_color = "green" if price_change >= 0 else "red"
            
            table.add_row(
                crypto['rank'],
                crypto['name'],
                symbol,
                f"${current_price:.2f}",
                f"[{change_color}]{price_change_24h:.2f}%[/{change_color}]",
                f"${float(crypto['marketCapUsd']):,.0f}",
                f"${last_price:.2f}",
                f"[{price_change_color}]{price_change:+.2f}%[/{price_change_color}]"
            )
        
        console.print(table)
        
        # Save the new prices
        save_last_scanned_prices(new_prices)
        
        # Display last scan time
        last_scan_time = datetime.fromisoformat(min(p['time'] for p in last_scanned.values())) if last_scanned else current_time
        console.print(f"\n[bold cyan]Last scan time: {last_scan_time.strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]")
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
    
def fetch_meme_tokens(search_term):
    url = f"https://api.dexscreener.com/latest/dex/search?q={search_term}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('pairs', [])
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching meme tokens: {e}[/bold red]")
        return None

def display_meme_tokens(tokens):
    if not tokens:
        console.print("[yellow]No tokens found matching the search term.[/yellow]")
        return

    table = Table(title="Meme Tokens Search Results")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="magenta")
    table.add_column("Symbol", style="yellow")
    table.add_column("Chain", style="green")
    table.add_column("Address", style="blue")
    table.add_column("Liquidity (USD)", style="cyan", justify="right")
    table.add_column("Market Cap", style="red", justify="right")

    for i, token in enumerate(tokens[:10], 1):  # Limit to top 10 results
        base_token = token['baseToken']
        liquidity = float(token['liquidity']['usd'])
        market_cap = float(token.get('fdv', 0))  # Use FDV as market cap, default to 0 if not available
        chain = token['chainId']  # Get the chain information

        table.add_row(
            str(i),
            base_token['name'],
            base_token['symbol'],
            chain.upper(),  # Display chain in uppercase
            base_token['address'],
            f"${liquidity:,.2f}",
            f"${market_cap:,.2f}" if market_cap > 0 else "N/A"
        )

    console.print(table)
    return tokens[:10]  # Return the displayed tokens for further analysis

def search_and_analyze_meme_tokens(favorites):
    search_term = Prompt.ask("\n[bold cyan]Enter the name of the meme token to search[/bold cyan]")
    
    with Progress() as progress:
        task = progress.add_task("[green]Searching for meme tokens...", total=100)
        
        while not progress.finished:
            progress.update(task, advance=0.5)
            tokens = fetch_meme_tokens(search_term)
            progress.update(task, completed=100)
    
    if tokens:
        displayed_tokens = display_meme_tokens(tokens)
        
        while True:
            choice = Prompt.ask(
                "\n[bold cyan]Enter the number of the token to analyze, or 'q' to return to the main menu[/bold cyan]"
            )
            
            if choice.lower() == 'q':
                break
            
            try:
                token_index = int(choice) - 1
                if 0 <= token_index < len(displayed_tokens):
                    token_address = displayed_tokens[token_index]['baseToken']['address']
                    
                    with Progress() as progress:
                        task = progress.add_task("[green]Fetching token data...", total=100)
                        
                        while not progress.finished:
                            progress.update(task, advance=0.5)
                            data = fetch_dexscreener_data(token_address)
                            progress.update(task, completed=100)
                    
                    if data and 'pairs' in data and data['pairs']:
                        pair_data = data['pairs'][0]
                        token_data = pair_data['baseToken']
                        current_price = float(pair_data['priceUsd'])
                        
                        display_token_info(token_data, pair_data)
                        display_pair_info(pair_data)
                        
                        if token_address not in favorites:
                            if Prompt.ask("[bold cyan]Add this token to favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                                current_fdv = float(pair_data.get('fdv', 0))
                                add_to_favorites(favorites, token_address, token_data['name'], current_price, current_fdv)
                        else:
                            if Prompt.ask("[bold cyan]Remove this token from favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                                remove_from_favorites(favorites, token_address)
                            else:
                                update_last_scan_price(favorites, token_address, current_price)
                    else:
                        console.print("[bold red]Failed to fetch data for the selected token.[/bold red]")
                    
                    if Prompt.ask("\n[bold cyan]Analyze another token from the list?[/bold cyan]", choices=["y", "n"], default="n") == "n":
                        break
                else:
                    console.print("[bold red]Invalid token number. Please try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'q' to quit.[/bold red]")
    else:
        console.print("[bold red]No tokens found or error occurred during search.[/bold red]")

def main():
    clear_screen()
    console.print("[bold green]Welcome to the Crypto Token Analyzer![/bold green]")
    console.print("This tool fetches and displays information about cryptocurrency tokens across various networks.")
    
    favorites = load_favorites()
    
    while True:
        display_ascii_art()
        btc_price, eth_price = fetch_btc_eth_prices()
        if btc_price and eth_price:
            console.print(f"\n[bold yellow]BTC: ${btc_price:,.2f}[/bold yellow] | [bold yellow]ETH: ${eth_price:,.2f}[/bold yellow]")
        else:
            console.print("\n[bold red]Unable to fetch BTC and ETH prices[/bold red]")
            
        console.print("\n[bold cyan]Main Menu:[/bold cyan]")
        console.print("[bold white]1.[/bold white] [yellow]Analyze Token[/yellow]")
        console.print("[bold white]2.[/bold white] [yellow]Analyze Wallets[/yellow]")
        console.print("[bold white]3.[/bold white] [yellow]View Favorites Token[/yellow]")
        console.print("[bold white]4.[/bold white] [yellow]View Top 10 Cryptocurrencies[/yellow]")
        console.print("[bold white]5.[/bold white] [yellow]View Ethereum Gas Prices[/yellow]")
        console.print("[bold white]6.[/bold white] [yellow]Search Meme Tokens[/yellow]")
        console.print("[bold white]7.[/bold white] [yellow]Exit[/yellow]")
        
        choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]")
        
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
                    current_price = float(pair_data['priceUsd'])
                    
                    display_token_info(token_data, pair_data)
                    display_pair_info(pair_data)
                    
                    if token_address not in favorites:
                        if Prompt.ask("[bold cyan]Add this token to favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                            current_fdv = float(pair_data.get('fdv', 0)) 
                            add_to_favorites(favorites, token_address, token_data['name'], current_price, current_fdv)
                    else:
                        if Prompt.ask("[bold cyan]Remove this token from favorites?[/bold cyan]", choices=["y", "n"], default="n") == "y":
                            remove_from_favorites(favorites, token_address)
                        else:
                            update_last_scan_price(favorites, token_address, current_price)
                else:
                    console.print("[bold red]No data found for the given token address.[/bold red]")
                    console.print("[yellow]Please check the address and try again.[/yellow]")
                
        elif choice == "3":
            clear_screen()
            display_favorites(favorites)
            if favorites:
                console.print("\n[bold cyan]Favorite Token Options:[/bold cyan]")
                console.print("[bold white]1.[/bold white] [yellow]Enter the number of a favorite token to analyze[/yellow]")
                console.print("[bold white]2.[/bold white] [yellow]Scan all favorite tokens[/yellow]")
                console.print("[bold white]3.[/bold white] [yellow]Remove a favorite token by number[/yellow]")
                console.print("[bold white]4.[/bold white] [yellow]Remove all favorite tokens[/yellow]")
                console.print("[bold white]5.[/bold white] [yellow]Return to the main menu[/yellow]")
                
                fav_choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]")
                
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
                                console.print("\nPress Enter to continue...")
                                input()
                            else:
                                console.print("[bold red]Failed to fetch data for the selected token.[/bold red]")
                        else:
                            console.print("[bold red]Invalid token number.[/bold red]")
                    else:
                        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
                        
                elif fav_choice == "2":
                    scan_all_favorites(favorites)
                    console.print("\nPress Enter to continue...")
                    input()
                    
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
                    clear_screen()
                    pass 

        elif choice == "2":
            clear_screen()
            wallet_transaction_analysis()
        elif choice == "4":
            clear_screen()
            console.print("\n[bold cyan]Top 10 Cryptocurrencies by Market Cap:[/bold cyan]")
            display_top_cryptocurrencies()
            input("\nPress Enter to return to the main menu...")
        elif choice == "5":
            clear_screen()
            console.print("\n[bold cyan]Ethereum Gas Prices:[/bold cyan]")
            display_eth_gas_prices()
            input("\nPress Enter to return to the main menu...")
        elif choice == "6":
            clear_screen()
            search_and_analyze_meme_tokens(favorites)
        elif choice == "7":
            break
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        
    console.print("[bold green]Thank you for using the Crypto Token Analyzer![/bold green]")
if __name__ == "__main__":
    main()
