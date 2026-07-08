# src/cli/cli/commands/cli_search.py
import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
from typing import Optional
from ..utils.api_client import APIClient, APIError, APIHTTPError, APIConnectionError

console = Console()


@click.command(name="search")
@click.argument("query")
@click.option(
    "--type",
    type=str,
    help="type of search: ftx (full-text), smt (semantic), hyb (hybrid), knn (semantic Knn), agt (agentic)",
)
@click.option(
    "--date-from",
    type=click.DateTime(formats=["%d-%m-%Y"]),
    help="Filter documents from this date (format: DD-MM-YYYY)",
    metavar="DD-MM-YYYY"
)
@click.option(
    "--date-to",
    type=click.DateTime(formats=["%d-%m-%Y"]),
    help="Filter documents until this date (format: DD-MM-YYYY)",
    metavar="DD-MM-YYYY"
)
@click.option(
    "--version",
    type=int,
    help="Filter by document version",
    metavar="INT"
)
@click.option(
    "--instance",
    type=str,
    help="Filter by yProv instance URL",
    metavar="URL"
)
@click.option(
    "--other-versions/--no-other-versions",
    default=False,
    help="Include other versions of documents in results"
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of results to display",
    show_default=True
)
@click.pass_context
def search(
    ctx,
    query: str,
    type: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    version: Optional[int],
    instance: Optional[str],
    other_versions: bool,
    limit: Optional[int]
):
    """
    Perform search on documents.
    
    QUERY: The search term(s) to look for
    
    Examples:
    
        Full-text search:
        ypfind search climate --type ftx

        Semantic search:
        ypfind search climate --type smt

        Agentic search:
        ypfind search "fetch all files with the keyword 'doc'" --type agt
    """
    api_client: APIClient = ctx.obj["client"]
    
    if not limit: limit=10

    url=""
    search_type=""
    match type:
        case "ftx":
            url="/search/fulltext"
            search_type="Search type: full-text"
        case "smt":
            url="/search/semantic"
            search_type="Search type: semantic"
        case "hyb":
            url="/search/semantic-fulltext"
            search_type="Search type: hybrid"
        case "knn":
            url="/search/knn-fulltext"
            search_type="Search type: knn"
        case "agt":
            url="/search/agentic"
            search_type="Search type: agentic AI"
        case _:
            url="/search/fulltext"
            search_type="Search method typo, full-text default search started"

    if type == "agt":
        params = {"query": query}
    else:
        params = {
            "query": query,
            "page_size": limit,
            "other_versions": other_versions
        }
        
        if date_from:
            params["date_from"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["date_to"] = date_to.strftime("%Y-%m-%d")
        if version is not None:
            params["version"] = version
        if instance:
            params["yProvIstance"] = instance
    
    try:
        with console.status(f"[blue]{search_type}. Searching for '{query}'...", spinner="dots"):
            if type == "agt":
                base_url = getattr(api_client, "base_url", "http://localhost:8000")
                base_url = base_url.rstrip("/")
                response = httpx.get(f"{base_url}{url}", params=params, timeout=None).json()
            else:
                response = api_client.get(url, params=params)
        
        _display_results(response, query, type)
        
    except Exception as e:
        # Catch the httpx error or fallback to the existing handler structure
        if type == "agt":
            console.print(f"\n[red]✗ Agentic Search failed - Error: {str(e)}[/red]")
            raise click.Abort()
        raise  # Reraise standard errors for ftx, smt, etc. to hit the blocks below
    
    except APIHTTPError as e:
        console.print(f"\n[red]✗ Search failed - Error {e.status_code}[/red]")
        
        if e.status_code == 400:
            console.print(f"   [yellow]Invalid request: {e.detail}[/yellow]")
        elif e.status_code == 422:
            console.print(f"   [yellow]Invalid parameters[/yellow]")
            if isinstance(e.detail, list):
                for err in e.detail:
                    field = err.get('loc', [''])[-1]
                    msg = err.get('msg', '')
                    console.print(f"   • {field}: {msg}")
            else:
                console.print(f"   {e.detail}")
        else:
            console.print(f"   {e.detail}")
        
        raise click.Abort()
    
    except APIConnectionError:
        console.print(f"\n[red]✗ Connection error[/red]")
        console.print("   [dim]Is the service running?[/dim]")
        raise click.Abort()
    
    except APIError as e:
        console.print(f"\n[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()

def _display_results(results: list, query: str, type : str):
    """Display search results in a formatted table"""
    
    if not results:
        console.print(f"\n[yellow]No results found for '{query}'[/yellow]\n")
        return
    
    # Header
    console.print(f"\n[green]✓ Found {len(results)} result(s) for '{query}'[/green]")
    
    if type == "agt": 
        response = results["agent_response"]
        console.print(f"""[bold cyan]Agent response:[/bold cyan] {response} """)
        results = results["raw_results"]

    for i, doc in enumerate(results, 1):
        source = doc.get('source', {})
        score = doc.get('score', 0)
        doc_id = doc.get('id', 'N/A')
        
        # Estrai campi principali
        title = source.get('title', 'No title')
        description = source.get('description', 'No description')
        author = source.get('author', 'Unknown')
        date_created = source.get('dateCreated', 'N/A')
        version = source.get('version', 'N/A')
        llm_description = source.get('llm_description', 'N/A')
        
        # Tronca descrizione se troppo lunga
        if description:
            if len(description) > 200:
                description = description[:197] + "..."
        
        # Crea un pannello per ogni risultato
        content = f"""[bold cyan]Title:[/bold cyan] {title}
        [bold cyan]PID:[/bold cyan] {doc_id}
        [bold cyan]description:[/bold cyan] {description}
        [bold cyan]Author:[/bold cyan] {author}
        [bold cyan]Date:[/bold cyan] {date_created}
        [bold cyan]Version:[/bold cyan] {version}
        [bold cyan]Score:[/bold cyan] {score:.4f}
        [bold cyan]llm_description:[/bold cyan] {llm_description}
        """
        
        panel = Panel(
            content,
            title=f"[bold white]Result {i}[/bold white]",
            border_style="blue"
        )
        console.print(panel)
        
        # Mostra altre versioni se presenti
        other_versions = doc.get('other_versions', [])
        if other_versions:
            console.print(f"  [dim]Other versions: {len(other_versions)}[/dim]")
            for ov in other_versions[:3]:  # Mostra max 3 altre versioni
                ov_pid = ov.get("id", 'N/A')
                ov_version= ov["source"].get("version", "N/A")
                ov_title = ov["source"].get("title", 'N/A')
                console.print(f"    • Version {ov_version}")
                console.print(f"    • Document pid:  {ov_pid}")
                console.print(f"    • Title:  {ov_title}\n")
            if len(other_versions) > 3:
                console.print(f"    [dim]... and {len(other_versions) - 3} more[/dim]")
        
        console.print()