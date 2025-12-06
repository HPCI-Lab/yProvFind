import click
from .utils.api_client import APIClient
from .commands.cli_indexing import scraper
from .commands.cli_registry import registry
from .commands.cli_search import search
from .commands.cli_timestamp import tmstamp
from .commands.cli_demo import demo
@click.group()
@click.option(
    "--url",
    default="http://localhost:8002",
    envvar="BASE_API_URL",
    show_default=True,
    help="Set the base URL for the API calls"
)
@click.option(
    "--timeout",
    default=60,
    type=int,
    show_default=True,
    help="Set the timeout for API calls (in seconds)"
)
@click.pass_context
def cli(ctx, url: str, timeout: int):
    ctx.ensure_object(dict)
    ctx.obj["client"] = APIClient(url, timeout)

cli.add_command(scraper)
cli.add_command(registry)
cli.add_command(search)
cli.add_command(tmstamp)
cli.add_command(demo)


if __name__ == "__main__":
    cli()
