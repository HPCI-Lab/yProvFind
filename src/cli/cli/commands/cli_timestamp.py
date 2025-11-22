import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError, APITimeoutError

console = Console()

@click.group
def tmstamp():
    "Manage the timestamps of each yprovstore address"
    pass



@click.command(name="list")
@click.pass_context
def get_list(ctx):
    """Returns the list of yProvStore addresses with the last update date"""
    api_client:APIClient=ctx.obj["client"]

    try:
        with console.status("", spinner="dots"):
            response = api_client.get("/timestamp/all-timestamp")

        console.print("\nAddress timestamp list:")
        if response:
            for i, (k, v) in enumerate(response.items(), start= 1):
                console.print(f"{i}. {k}  :  {v}")
            console.print("\n")

        else: 
            console.print("[yellow]⚠ empty \n")
    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")

        if e.status_code == 400:
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
    
tmstamp.add_command(get_list)





@click.command(name="delete-all")
@click.pass_context
def delete_all(ctx):
    """Delete all timestamps for all yProvStore instance addresses"""
    api_client: APIClient= ctx.obj["client"]
    try: 
        with console.status("[blue] Deleting", spinner="dots"):
            response= api_client.delete("/timestamp/delete-all-timestamp")
        if response.get("status")=="completed":
            console.print("[green]✓ Completed")
        else:
            console.print(f"[red]✗ Error:{response}")


    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")

        if e.status_code == 400:
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


tmstamp.add_command(delete_all)






@click.command(name="delete-address")
@click.pass_context
def delete_address(ctx, address: str):
    """Delete all timestamps for all yProvStore instance addresses"""
    api_client: APIClient= ctx.obj["client"]
    try: 
        params= {"address": address}
        with console.status("[blue] Deleting", spinner="dots"):
            response= api_client.delete("/timestamp/delete-address-timestamp", params=params)
        if response.get("status")=="completed":
            console.print("[green]✓ Completed")
        else:
            console.print(f"[red]✗ Error:{response}")


    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")

        if e.status_code == 400:
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


tmstamp.add_command(delete_all)
