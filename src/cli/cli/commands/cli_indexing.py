import click
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError, APITimeoutError
from rich.console import Console
from rich.table import Table

console = Console()

@click.command
@click.pass_context
def start_index(ctx):
    """
    Starts the full indexing process.

    This command triggers the indexing of all documents
    from active yProv instances to ElasticSearch.
    """

    api_client: APIClient = ctx.obj["client"]

    try:
        with console.status("[blue]indexing in progress...", spinner="dots"):
            response = api_client.get("/fetch/date-fetch")


        _display_results(response)


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



def _display_results(result: dict):
    """show results in a formatted table"""
    
    # Determina il colore in base allo status
    status = result.get('status', 'unknown')
    if status == 'completed':
        status_color = "green"
        status_icon = "✓"
    elif status == 'interrupted':
        status_color = "yellow"
        status_icon = "⚠"
    else:
        status_color = "red"
        status_icon = "✗"
    
    console.print(f"\n[{status_color}]{status_icon} Status: {status}[/{status_color}]")
    
    # Tabella con i risultati
    table = Table(title="Indexing resume", show_header=True)
    table.add_column("Results", style="cyan", no_wrap=True)
    table.add_column("Values", justify="right", style="magenta")
    
    table.add_row(
        "Indexed documents on ES",
        f"[green]{result.get('ES_successfully_indexed', 0)}[/green]"
    )
    table.add_row(
        "Indexing errors on ES",
        f"[red]{result.get('ES_error_count', 0)}[/red]"
    )
    table.add_row(
        "Embeddings created",
        f"[green]{result.get('embed_success', 0)}[/green]"
    )
    table.add_row(
        "Embeddings errors",
        f"[red]{result.get('embed_error', 0)}[/red]"
    )
    
    console.print(table)
    
    # Mostra dettagli se presenti
    if result.get('details'):
        console.print(f"\n[yellow]ℹ Details: {result['details']}[/yellow]")