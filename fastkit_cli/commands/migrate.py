import subprocess
import sys

import typer

app = typer.Typer(help="Migration commands.")


def _run_alembic(args: list[str]) -> None:
    """Run an alembic command via subprocess."""
    cmd = [sys.executable, "-m", "alembic"] + args

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        typer.secho(
            "  ✗  alembic not found. Install it with: pip install alembic",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"  ✗  Alembic exited with error: {e.returncode}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(e.returncode)


@app.command()
def run():
    """Run pending migrations. (alembic upgrade head)"""
    typer.secho("Running migrations...", fg=typer.colors.BRIGHT_CYAN, bold=True)
    _run_alembic(["upgrade", "head"])
    typer.secho("  ✓  Migrations complete.", fg=typer.colors.GREEN)


@app.command()
def make(message: str = typer.Option(..., "--message", "-m", help="Migration message")):
    """Generate a new migration. (alembic revision --autogenerate)"""
    typer.secho(f"Generating migration: {message}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    _run_alembic(["revision", "--autogenerate", "-m", message])
    typer.secho("  ✓  Migration file created.", fg=typer.colors.GREEN)


@app.command()
def rollback():
    """Rollback last migration. (alembic downgrade -1)"""
    typer.secho("Rolling back last migration...", fg=typer.colors.BRIGHT_CYAN, bold=True)
    _run_alembic(["downgrade", "-1"])
    typer.secho("  ✓  Rollback complete.", fg=typer.colors.GREEN)


@app.command()
def status():
    """Show current migration status. (alembic current)"""
    typer.secho("Migration status:", fg=typer.colors.BRIGHT_CYAN, bold=True)
    _run_alembic(["current"])
