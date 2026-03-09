import re
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader

app = typer.Typer(help="Code generation commands.")

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "module"


# ─────────────────────────────────────────────────────────────────────────────
# Naming Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_snake_case(name: str) -> str:
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)
    return name.lower()


def _to_pascal_case(name: str) -> str:
    return ''.join(word.capitalize() for word in re.split(r'[_\s-]', name))


def _to_plural(name: str) -> str:
    if name.endswith('y') and not name.endswith(('ay', 'ey', 'iy', 'oy', 'uy')):
        return name[:-1] + 'ies'
    if name.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return name + 'es'
    return name + 's'


# ─────────────────────────────────────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_context(name: str) -> dict:
    model_name = _to_pascal_case(name)
    snake_name = _to_snake_case(model_name)
    table_name = _to_plural(snake_name)
    return {
        "model_name": model_name,
        "snake_name": snake_name,
        "table_name": table_name,
        "module_folder": table_name,
    }


def _render_template(template_name: str, context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    return env.get_template(template_name).render(**context)


def _render_and_write(
    template_name: str,
    output_path: Path,
    context: dict,
    force: bool = False,
    skipped: list | None = None,
) -> None:
    if output_path.exists() and not force:
        if skipped is not None:
            skipped.append(output_path.name)
        return
    try:
        content = _render_template(template_name, context)
        output_path.write_text(content)
        typer.secho(f"  ✓  {output_path.name}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"  ✗  {output_path.name} — {e}", fg=typer.colors.RED)


def _register_in_alembic(model_name: str, module_folder: str) -> None:
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

    insert_marker = "target_metadata"
    if insert_marker in content:
        content = content.replace(insert_marker, f"{import_line}\n{insert_marker}", 1)
        env_py.write_text(content)
        typer.secho(f"  ✓  Registered model in {env_py}", fg=typer.colors.GREEN)
    else:
        typer.secho(
            f"  ⚠  Could not auto-register model in {env_py}. "
            f"Please add manually:\n     {import_line}",
            fg=typer.colors.YELLOW,
        )


def _print_skipped(skipped: list) -> None:
    if skipped:
        typer.echo("")
        typer.secho(
            f"  Skipped {len(skipped)} existing file(s). Use --force to overwrite.",
            fg=typer.colors.YELLOW,
        )

def _make_init_file(file, force: bool) -> None:
    if not file.exists() or force:
        file.write_text("")
        typer.secho("  ✓  __init__.py", fg=typer.colors.GREEN)

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
        fastkit make module Invoice --async
        fastkit make module InvoiceItem --dir src/modules
    """
    context = _build_context(name)
    module_path = Path(modules_dir) / context["table_name"]

    typer.echo("")
    typer.secho(f"Generating module: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo(f"  Location : {module_path}/")
    typer.echo(f"  Model    : {context['model_name']}")
    typer.echo(f"  Table    : {context['table_name']}")
    typer.echo(f"  Mode     : {'async' if async_mode else 'sync'}")
    typer.echo("")

    module_path.mkdir(parents=True, exist_ok=True)

    module_dir_init = Path(modules_dir) / "__init__.py"
    _make_init_file(module_dir_init, force)

    init_file = module_path / "__init__.py"
    _make_init_file(init_file, force)

    templates = [
        ("model.py.jinja", "models.py"),
        ("schemas.py.jinja", "schemas.py"),
        ("async_repository.py.jinja" if async_mode else "repository.py.jinja", "repository.py"),
        ("async_service.py.jinja" if async_mode else "service.py.jinja", "service.py"),
        ("async_router.py.jinja" if async_mode else "router.py.jinja", "router.py"),
    ]

    skipped: list = []
    for template_name, output_filename in templates:
        _render_and_write(
            template_name=template_name,
            output_path=module_path / output_filename,
            context=context,
            force=force,
            skipped=skipped,
        )

    _print_skipped(skipped)

    typer.echo("")
    _register_in_alembic(context["model_name"], context["table_name"])

    typer.echo("")
    typer.secho("Done! Next steps:", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo(f"  1. Define your fields in  {module_path}/models.py")
    typer.echo(f"  2. Add schemas in          {module_path}/schemas.py")
    typer.echo(f"  3. Run: fastkit migrate make -m 'create_{context['table_name']}'")
    typer.echo("")


@app.command()
def model(
    name: str = typer.Argument(..., help="Model name in PascalCase (e.g. Invoice, InvoiceItem)"),
    path: str = typer.Option(".", "--path", "-p", help="Path to target directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
):
    """
    Generate only a model file.

    \b
    Example:
        fastkit make model Invoice
        fastkit make model Invoice --path modules/invoices
    """
    context = _build_context(name)
    module_path = Path(path)

    typer.echo("")
    typer.secho(f"Generating model: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo("")

    _render_and_write(
        template_name="model.py.jinja",
        output_path=module_path / "models.py",
        context=context,
        force=force,
    )

    typer.echo("")
    _register_in_alembic(context["model_name"], context["table_name"])

    typer.echo("")
    typer.secho("Done!", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo(f"  Define your fields in  {module_path}/models.py")
    typer.echo("")

@app.command()
def schema(
    name: str = typer.Argument(..., help="Schema name in PascalCase (e.g. Invoice)"),
    path: str = typer.Option(".", "--path", "-p", help="Path to target directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
):
    """
    Generate only a schemas file.

    \b
    Example:
        fastkit make schema Invoice
        fastkit make schema Invoice --path modules/invoices
    """
    context = _build_context(name)
    module_path = Path(path)

    typer.echo("")
    typer.secho(f"Generating schemas: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo("")

    _render_and_write(
        template_name="schemas.py.jinja",
        output_path=module_path / "schemas.py",
        context=context,
        force=force,
    )

    typer.echo("")
    typer.secho("Done!", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo(f"  Define your schemas in  {module_path}/schemas.py")
    typer.echo("")


@app.command()
def repository(
    name: str = typer.Argument(..., help="Repository name in PascalCase (e.g. Invoice)"),
    path: str = typer.Option(".", "--path", "-p", help="Path to target directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
    async_mode: bool = typer.Option(False, "--async", "-a", help="Use async repository"),
):
    """
    Generate only a repository file.

    \b
    Example:
        fastkit make repository Invoice
        fastkit make repository Invoice --async
        fastkit make repository Invoice --path modules/invoices
    """
    context = _build_context(name)
    module_path = Path(path)
    template = "async_repository.py.jinja" if async_mode else "repository.py.jinja"

    typer.echo("")
    typer.secho(f"Generating repository: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo(f"  Mode: {'async' if async_mode else 'sync'}")
    typer.echo("")

    _render_and_write(
        template_name=template,
        output_path=module_path / "repository.py",
        context=context,
        force=force,
    )

    typer.echo("")
    typer.secho("Done!", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo("")

@app.command()
def service(
    name: str = typer.Argument(..., help="Service name in PascalCase (e.g. Invoice)"),
    path: str = typer.Option(".", "--path", "-p", help="Path to target directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
    async_mode: bool = typer.Option(False, "--async", "-a", help="Use async service"),
):
    """
    Generate only a service file.

    \b
    Example:
        fastkit make service Invoice
        fastkit make service Invoice --async
        fastkit make service Invoice --path modules/invoices
    """
    context = _build_context(name)
    module_path = Path(path)
    template = "async_service.py.jinja" if async_mode else "service.py.jinja"

    typer.echo("")
    typer.secho(f"Generating service: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo(f"  Mode: {'async' if async_mode else 'sync'}")
    typer.echo("")

    _render_and_write(
        template_name=template,
        output_path=module_path / "service.py",
        context=context,
        force=force,
    )

    typer.echo("")
    typer.secho("Done!", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo("")

@app.command()
def router(
    name: str = typer.Argument(..., help="Router name in PascalCase (e.g. Invoice)"),
    path: str = typer.Option(".", "--path", "-p", help="Path to target directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
    async_mode: bool = typer.Option(False, "--async", "-a", help="Use async router"),
):
    """
    Generate only a router file.

    \b
    Example:
        fastkit make router Invoice
        fastkit make router Invoice --async
        fastkit make router Invoice --path modules/invoices
    """
    context = _build_context(name)
    module_path = Path(path)
    template = "async_router.py.jinja" if async_mode else "router.py.jinja"

    typer.echo("")
    typer.secho(f"Generating router: {context['model_name']}", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo(f"  Mode: {'async' if async_mode else 'sync'}")
    typer.echo("")

    _render_and_write(
        template_name=template,
        output_path=module_path / "router.py",
        context=context,
        force=force,
    )

    typer.echo("")
    typer.secho("Done!", fg=typer.colors.BRIGHT_WHITE, bold=True)
    typer.echo("")