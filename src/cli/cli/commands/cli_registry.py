import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError, APITimeoutError

console = Console()

@click.group()
def registry():
    """Registry related commands."""
    pass



@click.command(name="list")
@click.pass_context
def addresses_list(ctx):
    """Show the list of registered addresses."""
    api_client: APIClient = ctx.obj["client"]

    try:
        with console.status("[blue]", spinner="dots"):
            response = api_client.get("/registry/get-address-list")
            console.print("\n[white]Addresses list:[/white]")
        for i, item in enumerate(response, 1):
            console.print(f"[cyan]{i}.[/cyan] {item}")

        console.print("\n")

    except click.Abort:
        console.print("\n[red]Request aborted.[/red]")
        raise

registry.add_command(addresses_list)



@click.command (name="add")
@click.argument("address")
@click.pass_context
def add_address(ctx, address: str):
    """
        Add a new address to the registry.

        ADDRESS: The address to add (e.g., http://example.com:8080)

        Examples:

        ypfind registry add http://192.168.1.100:8080

        ypfind registry add https://yprov.example.com
    """

    api_client: APIClient= ctx.obj["client"]

    try:
        with console.status("[blue]Adding new address...", spinner="dots"):
            response = api_client.post("/registry/update-list", json={"address": address})
        status = response.get("status")
        if status == 'updated':
            status_color = "green"
            status_icon = "✓"
        elif status == 'already_present':
            status_color = "yellow"
            status_icon = "⚠"
        else:
            status_color = "red"
            status_icon = "✗"

        console.print(f"\n[{status_color}]{status_icon} Status: {status}[/{status_color}]\n")
    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")
        
        if e.status_code == 400:
            console.print(f"   Invalid request: {e.detail}")
        elif e.status_code == 422:
            console.print(f"Input should be a valid URL, relative URL without a base: {e.detail}")
        else:
            console.print(f"   {e.detail}")
        
        raise click.Abort()
    
    except APIConnectionError as e:
        console.print(f"\n[red]✗ Connection error[/red]")
        console.print(f"   {str(e)}")
        console.print("   [dim]Is yProvFind service active??[/dim]")
        raise click.Abort()
    
    except APITimeoutError as e:
        console.print(f"\n[red]✗ Timeout[/red]")
        console.print(f"   {str(e)}")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()

registry.add_command(add_address)



@click.command (name="delete")
@click.argument("address")
@click.pass_context
def delete_address(ctx, address: str):
    """
        Delete address from the registry.

        ADDRESS: The address to add (e.g., http://example.com:8080)

        Examples:

        ypfind registry delete http://192.168.1.100:8080

        ypfind registry delete https://yprov.example.com
    
    """
    api_client: APIClient= ctx.obj["client"]
    try:
        with console.status("[blue]Deletion in progress...", spinner="dots"):
            response = api_client.delete(
                "/registry/delete-address", 
                params={"address": address}
            )
        
        
        status = response.get("status")
        if status == 'deleted':
            console.print(f"\n[green]✓ Address deleted: {address}[/green]\n")
        else:
            console.print(f"\n[cyan]ℹ {response.get('message', 'Operation completed')}[/cyan]")
    
    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")
        
        if e.status_code == 404:
            console.print(f"   Address not found [yellow]{address}[/yellow]")
        elif e.status_code == 400:
            console.print(f"   Invalid request: {e.detail}")
        else:
            console.print(f"   {e.detail}")
        
        raise click.Abort()
    
    except APIConnectionError as e:
        console.print(f"\n[red]✗ Connection error[/red]")
        console.print(f"   {str(e)}")
        console.print("   [dim]Is yProvFind service active??[/dim]")
        raise click.Abort()
    
    except APITimeoutError as e:
        console.print(f"\n[red]✗ Timeout[/red]")
        console.print(f"   {str(e)}")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()

registry.add_command(delete_address)