import typer

app = typer.Typer(help="Create a new FastKit project.")


@app.callback(invoke_without_command=True)
def create(name: str = typer.Argument(..., help="Project name")):
    """Create a new FastKit project."""
    typer.echo(f"Creating new FastKit project: {name}")