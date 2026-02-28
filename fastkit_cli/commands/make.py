import re
from enum import Enum
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader

app = typer.Typer(help="Code generation commands.")

# Path to templates folder (relative to this file)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "module"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case. Example: InvoiceItem → invoice_item"""
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)
    return name.lower()


def _to_pascal_case(name: str) -> str:
    """Convert snake_case or any string to PascalCase. Example: invoice_item → InvoiceItem"""
    return ''.join(word.capitalize() for word in re.split(r'[_\s-]', name))


def _to_plural(name: str) -> str:
    """
    Simple English pluralization for table names.
    Covers most common cases used in model naming.
    """
    if name.endswith('y') and not name.endswith(('ay', 'ey', 'iy', 'oy', 'uy')):
        return name[:-1] + 'ies'   # category → categories
    if name.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return name + 'es'          # status → statuses
    return name + 's'               # invoice → invoices


def _render_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 template with the given context."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    return template.render(**context)


def _register_in_alembic(model_name: str, module_folder: str) -> None:
    """
    Register the new model in Alembic env.py so autogenerate detects it.
    Looks for env.py in alembic/ or migrations/ folder.
    """
    env_py = None
    for candidate in ["alembic/env.py", "migrations/env.py"]:
        path = Path(candidate)
        if path.exists():
            env_py = path
            break

    if env_py is None:
        typer.secho(
            "  ⚠  Could not find alembic/env.py or migrations/env.py. "
            "Please register the model manually.",
            fg=typer.colors.YELLOW,
        )
        return

    content = env_py.read_text()
    import_line = f"from modules.{module_folder}.models import {model_name}  # noqa"

    if import_line in content:
        typer.secho(f"  ✓  Model already registered in {env_py}", fg=typer.colors.YELLOW)
        return

    # Insert after the last existing "from modules." import, or before "target_metadata"
    insert_marker = "target_metadata"
    if insert_marker in content:
        content = content.replace(
            insert_marker,
            f"{import_line}\n{insert_marker}",
            1,
        )
        env_py.write_text(content)
        typer.secho(f"  ✓  Registered model in {env_py}", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"  ⚠  Could not auto-register model in {env_py}. "
            f"Please add manually:\n     {import_line}",
            fg=typer.colors.YELLOW,
        )

# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def module(
    name: str = typer.Argument(..., help="Module name in PascalCase (e.g. Invoice, InvoiceItem)"),
    modules_dir: str = typer.Option("modules", "--dir", "-d", help="Modules root directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    async_mode: bool = typer.Option(False, "--async", "-a", help="Use async repository and service"),
):
    """
    Generate a new module with model, schemas, repository, and service.

    \b
    Example:
        fastkit make module Invoice
        fastkit make module InvoiceItem --dir src/modules
    """
    # Derive naming variants
    model_name = _to_pascal_case(name)
    snake_name = _to_snake_case(model_name)
    table_name = _to_plural(snake_name)
    module_folder = snake_name + "s" if not snake_name.endswith("s") else snake_name

    # Use table_name as folder name (e.g. invoices)
    module_path = Path(modules_dir) / table_name

    typer.echo("")
    typer.secho(f"Generating module: {model_name}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo(f"  Location : {module_path}/")
    typer.echo(f"  Model    : {model_name}")
    typer.echo(f"  Table    : {table_name}")
    typer.echo("")

    # Create module directory
    module_path.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_file = module_path / "__init__.py"
    if not init_file.exists() or force:
        init_file.write_text("")
        typer.secho(f"  ✓  __init__.py", fg=typer.colors.GREEN)

    # Jinja2 context
    context = {
        "model_name": model_name,
        "snake_name": snake_name,
        "table_name": table_name,
        "module_folder": table_name,
    }

    # Generate each template
    skipped = []
    if async_mode:
        module_templates = [
            ("model.py.jinja", "models.py"),
            ("schemas.py.jinja", "schemas.py"),
            ("async_repository.py.jinja", "repository.py"),
            ("async_service.py.jinja", "service.py"),
        ]
    else:
        module_templates = [
            ("model.py.jinja", "models.py"),
            ("schemas.py.jinja", "schemas.py"),
            ("repository.py.jinja", "repository.py"),
            ("service.py.jinja", "service.py"),
        ]
    for template_name, output_filename in module_templates:
        output_path = module_path / output_filename

        if output_path.exists() and not force:
            skipped.append(output_filename)
            continue

        try:
            content = _render_template(template_name, context)
            output_path.write_text(content)
            typer.secho(f"  ✓  {output_filename}", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"  ✗  {output_filename} — {e}", fg=typer.colors.RED)

    if skipped:
        typer.echo("")
        typer.secho(
            f"  Skipped {len(skipped)} existing file(s). Use --force to overwrite.",
            fg=typer.colors.YELLOW,
        )

    # Register model in Alembic
    typer.echo("")
    _register_in_alembic(model_name, table_name)

    typer.echo("")
    typer.secho("Done! Next steps:", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo(f"  1. Define your fields in  {module_path}/models.py")
    typer.echo(f"  2. Add schemas in          {module_path}/schemas.py")
    typer.echo(f"  3. Run: fastkit migrate make -m 'create_{table_name}'")
    typer.echo("")