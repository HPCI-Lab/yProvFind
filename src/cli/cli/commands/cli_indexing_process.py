import click
import time
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError, APITimeoutError
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from typing import Dict
console = Console()

@click.group()
def indexing_process():
    "start the indexing and monitoring process"
    pass



@click.command()
@click.option(
    '--poll-interval',
    default=2,
    help='Seconds between status checks (default: 2)',
    type=int
)
@click.option(
    '--no-wait',
    is_flag=True,
    help='Start process and exit without waiting for completion'
)
@click.pass_context
def start(ctx, poll_interval: int, no_wait: bool):
    """
    Starts the full indexing process.
    
    This command triggers the indexing of all documents
    from active yProv instances to ElasticSearch.
    
    By default, it waits for the process to complete and shows progress.
    Use --no-wait to start the process and exit immediately.
    """
    api_client: APIClient = ctx.obj["client"]
    
    try:
        # Start the process
        console.print("[blue]Starting indexing process...[/blue]")
        start_response = api_client.post("/indexing-process/start")
        
        console.print(f"[green]✓ {start_response.get('message', 'Process started')}[/green]")
        
        if no_wait:
            console.print("\n[yellow]Process started in background.[/yellow]")
            console.print("[dim]Use 'yprovfind index status' to check progress[/dim]")
            return
        
        # Poll for status until completion
        console.print("\n[blue]Monitoring process...[/blue]")
        _monitor_process(api_client, poll_interval)
        
    except APIHTTPError as e:
        if e.status_code == 409:
            console.print(f"\n[yellow]⚠ {e.detail}[/yellow]")
            console.print("[dim]Use 'yprovfind index status' to check current progress[/dim]")
        elif e.status_code == 400:
            console.print(f"\n[red]✗ Invalid request: {e.detail}[/red]")
        else:
            console.print(f"\n[red]✗ Error {e.status_code}: {e.detail}[/red]")
        raise click.Abort()
    
    except APIConnectionError as e:
        console.print(f"\n[red]✗ Connection error[/red]")
        console.print(f"   {str(e)}")
        console.print("   [dim]Is yProvFind service active?[/dim]")
        raise click.Abort()
    
    except APITimeoutError as e:
        console.print(f"\n[red]✗ Timeout[/red]")
        console.print(f"   {str(e)}")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
indexing_process.add_command(start)

@click.command()
@click.pass_context
def status(ctx):
    """
    Check the status of the current indexing process.
    
    Shows real-time information about the running process,
    including progress and statistics.
    """
    api_client: APIClient = ctx.obj["client"]
    
    try:
        response = api_client.get("/indexing-process/status")
        _display_status(response)
        
    except APIHTTPError as e:
        console.print(f"\n[red]✗ Error {e.status_code}: {e.detail}[/red]")
        raise click.Abort()
    
    except APIConnectionError as e:
        console.print(f"\n[red]✗ Connection error: {str(e)}[/red]")
        console.print("   [dim]Is yProvFind service active?[/dim]")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
indexing_process.add_command(status)

@click.command()
@click.pass_context
def status_reset(ctx):
    """
    Reset the indexing process status.
    
    This command resets the status to idle.
    Can only be used when no process is running.
    """
    api_client: APIClient = ctx.obj["client"]
    
    if not click.confirm("Are you sure you want to reset the status?"):
        console.print("[yellow]Reset cancelled[/yellow]")
        return
    
    try:
        response = api_client.post("/indexing-process/reset")
        console.print(f"[green]✓ {response.get('message', 'Status reset')}[/green]")
        
    except APIHTTPError as e:
        if e.status_code == 409:
            console.print(f"\n[yellow]⚠ {e.detail}[/yellow]")
        else:
            console.print(f"\n[red]✗ Error {e.status_code}: {e.detail}[/red]")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
indexing_process.add_command(status_reset)


@click.command()
@click.pass_context
def abort(ctx):
    """
    Terminate the idexing process 
    """
    api_client:APIClient = ctx.obj["client"]

    try: 
        response = api_client.get("/indexing-process/abort")
        console.print(f"[yellow] {response.get('message')}[/yellow]")

    except APIHTTPError as e:
        if e.status_code == 409:
            console.print(f"\n[yellow]⚠ {e.detail}[/yellow]")
        else:
            console.print(f"\n[red]✗ Error {e.status_code}: {e.detail}[/red]")
        raise click.Abort()
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
    
indexing_process.add_command(abort)


@click.command()
@click.pass_context
def errors(ctx):
    """List all the errors occurred during the process."""
    api_client:APIClient = ctx.obj["client"]
    try:
        response:Dict = api_client.get("/indexing-process/errors")
        for k, v in response.items():
            console.print(f"[blue]\n\n{k}:[/blue]")
            for s in v:
                console.print(f"  - {s}")
    except APIHTTPError as e:
        console.print(f"\n[red]✗ Error {e.status_code}: {e.detail}[/red]")
        raise click.Abort()
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
indexing_process.add_command(errors)



def _monitor_process(api_client: APIClient, poll_interval: int):
    """Monitor the process until completion with live updates"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False
    ) as progress:
        
        task = progress.add_task("[cyan]Indexing...", total=None)
        last_details = ""
        
        while True:
            try:
                status_response = api_client.get("/indexing-process/status")
                status = status_response.get("status", "unknown")
                details = status_response.get("details", "")
                
                # Update progress description if details changed
                if details != last_details:
                    progress.update(task, description=f"[cyan]{details}")
                    last_details = details
                
                # Check if process completed
                if status in ["completed", "error", "interrupted"]:
                    progress.stop()
                    _display_results(status_response)
                    break
                
                # Wait before next check
                time.sleep(poll_interval)
                
            except APIError as e:
                progress.stop()
                console.print(f"\n[red]✗ Error checking status: {str(e)}[/red]")
                raise click.Abort()
















def _display_status(result: dict):
    """Display current status in a formatted way"""
    
    status = result.get('status', 'unknown')
    
    # Status with icon
    status_icons = {
        'idle': ('⚪', 'white'),
        'running': ('🔄', 'blue'),
        'completed': ('✓', 'green'),
        'interrupted': ('⚠', 'yellow'),
        'error': ('✗', 'red')
    }
    
    icon, color = status_icons.get(status, ('?', 'white'))
    console.print(f"\n[{color}]{icon} Status: {status.upper()}[/{color}]")
    
    # Details
    if result.get('details'):
        console.print(f"[dim]Details: {result['details']}[/dim]")
    
    # Timestamps
    if result.get('started_at'):
        console.print(f"[dim]Started: {result['started_at']}[/dim]")
    if result.get('completed_at'):
        console.print(f"[dim]Completed: {result['completed_at']}[/dim]")
    
    # Statistics table
    if status != 'idle':
        table = Table(title="Statistics", show_header=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="magenta")
        
        table.add_row(
            "Documents indexed",
            f"[green]{result.get('ES_successfully_indexed', 0)}[/green]"
        )
        table.add_row(
            "Indexing errors",
            f"[red]{result.get('ES_error_count', 0)}[/red]"
        )
        table.add_row(
            "Embeddings created",
            f"[green]{result.get('embed_success', 0)}[/green]"
        )
        table.add_row(
            "Embedding errors",
            f"[red]{result.get('embed_error', 0)}[/red]"
        )
        
        console.print(table)


def _display_results(result: dict):
    """Display final results with formatted table"""
    
    status = result.get('status', 'unknown')
    
    # Status header
    if status == 'completed':
        console.print(f"\n[green]✓ Indexing completed successfully![/green]")
    elif status == 'interrupted':
        console.print(f"\n[yellow]⚠ Indexing interrupted[/yellow]")
    else:
        console.print(f"\n[red]✗ Indexing failed[/red]")
    
    # Details
    if result.get('details'):
        console.print(f"[dim]{result['details']}[/dim]\n")
    
    # Results table
    table = Table(title="Indexing Summary", show_header=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="magenta")
    
    table.add_row(
        "Documents indexed",
        f"[green]{result.get('ES_successfully_indexed', 0)}[/green]"
    )
    table.add_row(
        "Indexing errors",
        f"[red]{result.get('ES_error_count', 0)}[/red]"
    )
    table.add_row(
        "Embeddings created",
        f"[green]{result.get('embed_success', 0)}[/green]"
    )
    table.add_row(
        "Embedding errors",
        f"[red]{result.get('embed_error', 0)}[/red]"
    )
    
    console.print(table)
    
    # Timestamps
    if result.get('started_at') and result.get('completed_at'):
        console.print(f"\n[dim]Started: {result['started_at']}[/dim]")
        console.print(f"[dim]Completed: {result['completed_at']}[/dim]")