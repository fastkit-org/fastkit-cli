<div align="center">
  <h1>FastKit CLI</h1>
  
  [![PyPI version](https://badge.fury.io/py/fastkit-cli.svg)](https://pypi.org/project/fastkit-cli/)
  [![Python 3.11+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
  [![CI](https://github.com/codevelo-pub/fastkit-core/actions/workflows/tests.yml/badge.svg)](https://github.com/codevelo-pub/fastkit-cli/actions/workflows/tests.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>


**FastAPI with structure and developer experience.**

FastKit CLI is a code generation tool for the [FastKit](https://github.com/codevelo-pub/fastkit-core) ecosystem. It generates complete, production-ready modules for FastAPI projects — models, schemas, repositories, services, and routers — in seconds.

> Inspired by Laravel's `php artisan`, built for FastAPI developers who want structure without the overhead.

---

## Requirements

- Python 3.12
- [fastkit-core](https://pypi.org/project/fastkit-core/)

---

## Installation

```bash
pip install fastkit-cli
```

Or with [uv](https://github.com/astral-sh/uv) (recommended):

```bash
uv add fastkit-cli
```

Verify the installation:

```bash
fastkit --help
```

---

## Quickstart

### Generate a complete module

```bash
fastkit make module Invoice
```

This generates the following structure:

```
modules/
└── invoices/
    ├── __init__.py
    ├── models.py
    ├── schemas.py
    ├── repository.py
    ├── service.py
    └── router.py
```

With a confirmation and next steps:

```
Generating module: Invoice
  Location : modules/invoices/
  Model    : Invoice
  Table    : invoices
  Mode     : sync

  ✓  __init__.py
  ✓  models.py
  ✓  schemas.py
  ✓  repository.py
  ✓  service.py
  ✓  router.py

  ✓  Registered model in alembic/env.py

Done! Next steps:
  1. Define your fields in  modules/invoices/models.py
  2. Add schemas in          modules/invoices/schemas.py
  3. Run: fastkit migrate make -m 'create_invoices'
```

### Generate an async module

```bash
fastkit make module Invoice --async
```

Generates the same structure but with async repository, service, and router using `AsyncSession` and `get_async_db`.

---

## make

### `fastkit make module`

Generates a complete module with all layers.

```bash
fastkit make module <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dir` | `-d` | `modules` | Root directory for modules |
| `--async` | `-a` | `False` | Use async repository, service, and router |
| `--force` | `-f` | `False` | Overwrite existing files |

**Examples:**

```bash
# Basic usage
fastkit make module Invoice

# Async mode
fastkit make module Invoice --async

# Custom directory
fastkit make module Invoice --dir src/modules

# Compound name (automatically converted)
fastkit make module InvoiceItem

# Overwrite existing files
fastkit make module Invoice --force
```

---

### `fastkit make model`

Generates only the SQLAlchemy model file.

```bash
fastkit make model <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--path` | `-p` | `.` | Target directory |
| `--force` | `-f` | `False` | Overwrite existing file |

**Examples:**

```bash
fastkit make model Invoice
fastkit make model Invoice --path modules/invoices
```

**Generated `models.py`:**

```python
from fastkit_core.database import BaseWithTimestamps, IntIdMixin
# from fastkit_core.database import UUIDMixin, SoftDeleteMixin, SlugMixin

class Invoice(BaseWithTimestamps, IntIdMixin):
    __tablename__ = "invoices"
    # Define your fields here
```

---

### `fastkit make schema`

Generates only the Pydantic schemas file.

```bash
fastkit make schema <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--path` | `-p` | `.` | Target directory |
| `--force` | `-f` | `False` | Overwrite existing file |

**Examples:**

```bash
fastkit make schema Invoice
fastkit make schema Invoice --path modules/invoices
```

**Generated `schemas.py`:**

```python
from fastkit_core.validation import BaseSchema

class InvoiceCreate(BaseSchema):
    pass  # Define your fields here

class InvoiceUpdate(BaseSchema):
    pass  # All fields optional for partial updates

class InvoiceResponse(BaseSchema):
    id: int
    model_config = {"from_attributes": True}
```

---

### `fastkit make repository`

Generates only the repository file.

```bash
fastkit make repository <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--path` | `-p` | `.` | Target directory |
| `--async` | `-a` | `False` | Use async repository |
| `--force` | `-f` | `False` | Overwrite existing file |

**Examples:**

```bash
fastkit make repository Invoice
fastkit make repository Invoice --async
fastkit make repository Invoice --path modules/invoices
```

---

### `fastkit make service`

Generates only the service file.

```bash
fastkit make service <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--path` | `-p` | `.` | Target directory |
| `--async` | `-a` | `False` | Use async service |
| `--force` | `-f` | `False` | Overwrite existing file |

**Examples:**

```bash
fastkit make service Invoice
fastkit make service Invoice --async
```

---

### `fastkit make router`

Generates only the router file with full CRUD endpoints.

```bash
fastkit make router <Name> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--path` | `-p` | `.` | Target directory |
| `--async` | `-a` | `False` | Use async router |
| `--force` | `-f` | `False` | Overwrite existing file |

**Examples:**

```bash
fastkit make router Invoice
fastkit make router Invoice --async
```

**Generated endpoints:**

```
GET    /invoices        → index   (paginated list)
GET    /invoices/{id}   → show
POST   /invoices        → store
PUT    /invoices/{id}   → update
DELETE /invoices/{id}   → destroy
```

---

## migrate

Wrapper around [Alembic](https://alembic.sqlalchemy.org/) migrations.

### `fastkit migrate run`

Run all pending migrations.

```bash
fastkit migrate run
# Equivalent to: alembic upgrade head
```

### `fastkit migrate make`

Generate a new migration based on model changes.

```bash
fastkit migrate make -m "create_invoices"
# Equivalent to: alembic revision --autogenerate -m "create_invoices"
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--message` | `-m` | Yes | Migration description |

### `fastkit migrate rollback`

Rollback the last migration.

```bash
fastkit migrate rollback
# Equivalent to: alembic downgrade -1
```

### `fastkit migrate status`

Show the current migration status.

```bash
fastkit migrate status
# Equivalent to: alembic current
```

---

## db seed

Run database seeders.

```bash
# Run all seeders
fastkit db seed

# Run a specific seeder
fastkit db seed UserSeeder
```

---

## server

Start the FastAPI development server.

```bash
fastkit server
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--host` | `-h` | `0.0.0.0` | Host to bind |
| `--port` | `-p` | `8000` | Port to bind |
| `--reload / --no-reload` | | `True` | Enable auto-reload |

**Examples:**

```bash
# Default
fastkit server

# Custom host and port
fastkit server --host 127.0.0.1 --port 9000

# Without auto-reload
fastkit server --no-reload
```

---

## new

Create a new FastKit project from a template.

```bash
fastkit new my-project
```

---

## Naming Conventions

FastKit CLI automatically handles naming conversions regardless of how you pass the module name:

| Input | Model | Snake | Table | Folder |
|-------|-------|-------|-------|--------|
| `Invoice` | `Invoice` | `invoice` | `invoices` | `invoices` |
| `invoice` | `Invoice` | `invoice` | `invoices` | `invoices` |
| `InvoiceItem` | `InvoiceItem` | `invoice_item` | `invoice_items` | `invoice_items` |
| `invoice_item` | `InvoiceItem` | `invoice_item` | `invoice_items` | `invoice_items` |
| `Category` | `Category` | `category` | `categories` | `categories` |

---

## Typical Workflow

```bash
# 1. Generate a new module
fastkit make module Invoice --async

# 2. Define your model fields
# Edit modules/invoices/models.py

# 3. Define your schemas
# Edit modules/invoices/schemas.py

# 4. Generate and run migration
fastkit migrate make -m "create_invoices"
fastkit migrate run

# 5. Register the router in your main app
# In app.py:
# from modules.invoices.router import router as invoices_router
# app.include_router(invoices_router, prefix="/api/v1")

# 6. Start the server
fastkit server
```

---

## Related Packages

- [fastkit-core](https://pypi.org/project/fastkit-core/) — Base classes, repository pattern, validation, i18n
- [mailbridge](https://pypi.org/project/mailbridge/) — Email delivery abstraction

---

## License

FastKit Core is open-source software licensed under the [MIT License](https://opensource.org/license/MIT).

---

## Built by CodeVelo

FastKit is developed and maintained by [Codevelo](https://codevelo.io) for the FastAPI community.