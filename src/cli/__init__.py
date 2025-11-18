import click
from cli.cli.utils.api_client import APIClient
from cli.cli.commands.cli_indexing import start_index
from cli.cli.commands.cli_registry import registry
from cli.cli.commands.cli_search import search
from cli.cli.commands.cli_timestamp import tmstamp
from cli.cli.commands.cli_demo import demo
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
    default=300,
    type=int,
    show_default=True,
    help="Set the timeout for API calls (in seconds)"
)
@click.pass_context
def cli(ctx, url: str, timeout: int):
    ctx.ensure_object(dict)
    ctx.obj["client"] = APIClient(url, timeout)

cli.add_command(start_index)
cli.add_command(registry)
cli.add_command(search)
cli.add_command(tmstamp)
cli.add_command(demo)


if __name__ == "__main__":
    cli()
