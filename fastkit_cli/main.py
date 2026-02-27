import typer
from fastkit_cli.commands import make, migrate, seed, server, new

app = typer.Typer(
    name="fastkit",
    help="FastKit CLI - FastAPI with structure and developer experience.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

# Register command groups
app.add_typer(make.app, name="make")
app.add_typer(migrate.app, name="migrate")
app.add_typer(seed.app, name="db")
app.add_typer(server.app, name="server")
app.add_typer(new.app, name="new")


if __name__ == "__main__":
    app()