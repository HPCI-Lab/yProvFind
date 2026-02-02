import click 
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError, APITimeoutError
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def demo():
    """Load or delete the example documents"""
    pass

@click.command()
@click.pass_context
def start(ctx):
    """
    index some sample documents

    """
    apiclient : APIClient = ctx.obj["client"]
    try:
        with console.status("[blue]", spinner="dots"):
            response = apiclient.post("/demo/start")
            
            if response.get("status")=="Demo started successfully":
                indexed=response.get("indexed")
                console.print(f"[green]✓ Demo started successfully with: {indexed} documents[/green]")
            else:
                console.print("[red]✗ Demo start failed[/red]")


    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")
        if e.status_code == 400:
            console.print(f"Invalid request: {e.detail}")
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

demo.add_command(start)





@click.command()
@click.pass_context
def end(ctx): 
    """
    delete sample documents
    
    """
    apiclient:APIClient=ctx.obj["client"]
    try:
        with console.status("[blue]", spinner="dots"):
            response = apiclient.delete("/demo/end")
            if response.get("status")=="Demo ended succesfully":
                console.print("[green]✓ Demo ended succesfully[/green]")
            else: 
                console.print(f"[red]✗ Demo end failed : {response}[/red]")

    
    except APIHTTPError as e:

        console.print(f"\n[red]✗ Error {e.status_code}[/red]")
        if e.status_code == 400:
            console.print(f"Invalid request: {e.detail}")
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

demo.add_command(end)

