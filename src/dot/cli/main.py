"""Main CLI application.

T067: Create typer app skeleton with --version, --help
T068: Entry point is configured in pyproject.toml
"""

from typing import Annotated

import typer

from dot import __version__

app = typer.Typer(
    name="dot",
    help="HOOK Manifest Builder - Create and validate data modeling manifests",
    no_args_is_help=True,
    pretty_exceptions_enable=False,  # Cleaner error output
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"dot version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """HOOK Manifest Builder - Create and validate data modeling manifests."""
    pass


# Import and register subcommands
from dot.cli.examples import examples_app  # noqa: E402
from dot.cli.init import init_command  # noqa: E402
from dot.cli.validate import validate  # noqa: E402

app.command("validate")(validate)
app.command("init")(init_command)
app.add_typer(examples_app, name="examples")


if __name__ == "__main__":
    app()
