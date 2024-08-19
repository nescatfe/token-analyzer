import requests
import json
import os
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress

console = Console()

# File to store favorite tokens
FAVORITES_FILE = "favorite_tokens.json"

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
    token_table.add_row("Symbol", f"[magenta]${token_data['symbol']}[/magenta]")
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

def main():
    console.print("[bold green]Welcome to the  Crypto Token Analyzer![/bold green]")
    console.print("This tool fetches and displays information about cryptocurrency tokens across various networks.")
    
    favorites = load_favorites()
    
    while True:
        console.print("\n[bold cyan]Menu:[/bold cyan]")
        console.print("1. Analyze a token")
        console.print("2. View favorites")
        console.print("3. Scan all favorite tokens")
        console.print("4. Exit")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            token_address = Prompt.ask("\nEnter the token address")
            
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
                    if Prompt.ask("Add this token to favorites?", choices=["y", "n"], default="n") == "y":
                        add_to_favorites(favorites, token_address, token_data['name'])
                else:
                    if Prompt.ask("Remove this token from favorites?", choices=["y", "n"], default="n") == "y":
                        remove_from_favorites(favorites, token_address)
            else:
                console.print("[bold red]No data found for the given token address.[/bold red]")
                console.print("[yellow]Please check the address and try again.[/yellow]")
        
        elif choice == "2":
            display_favorites(favorites)
            if favorites:
                console.print("\n[bold cyan]Favorite Token Options:[/bold cyan]")
                console.print("1. Enter the number of a favorite token to analyze")
                console.print("2. Scan all favorite tokens")
                console.print("3. Remove a favorite token by number")
                console.print("4. Remove all favorite tokens")
                console.print("5. Return to the main menu")
                
                fav_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])
                
                if fav_choice == "1":
                    token_number = Prompt.ask("Enter the number of the favorite token to analyze")
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
                    token_number = Prompt.ask("Enter the number of the favorite token to remove")
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
                    if Prompt.ask("Are you sure you want to remove all favorites?", choices=["y", "n"], default="n") == "y":
                        favorites.clear()
                        save_favorites(favorites)
                        console.print("[bold yellow]All favorites have been removed.[/bold yellow]")
                
                elif fav_choice == "5":
                    pass  # Return to main menu
        
        elif choice == "3":
            scan_all_favorites(favorites)
        
        elif choice == "4":
            break
    
    console.print("[bold green]Thank you for using the Crypto Token Analyzer![/bold green]")

if __name__ == "__main__":
    main()
