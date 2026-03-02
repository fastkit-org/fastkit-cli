import typer

app = typer.Typer(help="Server commands.")


@app.callback(invoke_without_command=True)
def start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
):
    """Start the FastAPI development server."""
    typer.echo(f"Starting server on {host}:{port}...")