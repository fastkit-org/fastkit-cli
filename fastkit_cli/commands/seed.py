import typer

app = typer.Typer(help="Database seeding commands.")


@app.callback(invoke_without_command=True)
def seed(seeder: str = typer.Argument(None, help="Specific seeder class to run")):
    """Run database seeders."""
    if seeder:
        typer.echo(f"Running seeder: {seeder}")
    else:
        typer.echo("Running all seeders...")