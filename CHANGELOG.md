# Changelog

All notable changes to FastKit CLI are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
FastKit CLI follows [Semantic Versioning](https://semver.org/).

---
## [0.2.2] — 2026-04-22

### Fixed

- Corrected `fastkit-core` minimum version constraint from `>=0.3.5` to `>=0.4.1`.
  Version 0.2.1 shipped with an incorrect lower bound that would allow installation
  alongside an incompatible core version, causing import errors at runtime.

## [0.2.1] — 2026-04-21

This release fixes two bugs that were hit immediately on first use of
`fastkit make module`. No breaking changes.

### Fixed

#### `make module` — Incorrect pluralization of already-plural input

When the user passed an already-plural name (e.g. `clients`, `invoices`),
the CLI applied its naive pluralization rules a second time, producing broken output:

| Input | Before | After |
|---|---|---|
| `clients` | folder `clientses/`, table `clientses`, class `Clients` | folder `clients/`, table `clients`, class `Client` |
| `invoices` | folder `invoicess/`, table `invoicess`, class `Invoices` | folder `invoices/`, table `invoices`, class `Invoice` |

**Root cause** — `_build_context` called `_to_plural()` on the raw input without
first checking whether the name was already plural, and derived the class name from
the plural form instead of the singular.

**Fix** — replaced the hand-rolled pluralization helpers with
[`inflect`](https://pypi.org/project/inflect/) and reworked `_build_context` to
always normalize to singular first:

- Input is converted to `snake_case`, then **singularized** via `inflect`.
- `model_name` (PascalCase class name) is always derived from the **singular** form.
- `table_name` and `module_folder` are always the **plural** snake_case form.
- `inflect.singular_noun()` returns `False` for already-singular words, so the
  singularization step is a no-op for inputs like `invoice` or `invoice_item`.

All four input forms now produce consistent output:

| Input | `model_name` | `snake_name` | `table_name` |
|---|---|---|---|
| `client` | `Client` | `client` | `clients` |
| `clients` | `Client` | `client` | `clients` |
| `invoice_item` | `InvoiceItem` | `invoice_item` | `invoice_items` |
| `invoice_items` | `InvoiceItem` | `invoice_item` | `invoice_items` |

#### `db seed` — subcommand not reachable via documented syntax

`fastkit db seed` and `fastkit db seed <SeederClass>` raised
`Error: No such command 'seed'` despite being the documented usage.

**Root cause** — the `seed` function was registered as `@app.callback` on the `db`
Typer group, making it the group callback rather than an explicit subcommand.
`fastkit db` invoked it directly, but `fastkit db seed` looked for a non-existent
nested command.

**Fix** — replaced `@app.callback(invoke_without_command=True)` with
`@app.command("seed")`. The `db` group is now correctly structured for future
extension with additional subcommands (`db reset`, `db fresh`, etc.).

```bash
# Now works as documented
fastkit db seed                  # Run all seeders
fastkit db seed UserSeeder       # Run specific seeder
```

### Added

- **`inflect>=7.0`** added to package dependencies to support robust
  pluralization and singularization.

## [0.2.0] — 2026-04-11

This release aligns the CLI with fastkit-core 0.4.0. Two areas are addressed:
the schema template now generates secure-by-default base classes, and the signal
system introduced in fastkit-core 0.4.0 gets full code generation support — both
as part of `make module` and as a standalone `make signals` command.

### Added

#### `signals.py.jinja` template

New template that generates a `signals.py` file declaring the three standard
lifecycle signals for a module.

- Imports `Signal` from `fastkit_core.events`.
- Generates `{snake_name}_created`, `{snake_name}_updated`, and `{snake_name}_deleted`
  signal instances following the `module_name.event_name` naming convention.
- Includes `__all__` so the public interface of the signals module is explicit.
- File-level comment explains the import convention and warns against creating new
  `Signal` instances outside this file.

```bash
# Generated output for: fastkit make signals Invoice
invoice_created = Signal('invoice.created')
invoice_updated = Signal('invoice.updated')
invoice_deleted = Signal('invoice.deleted')
```

#### `listeners.py.jinja` template

New template that generates a `listeners.py` file with commented-out receiver stubs
for each of the three lifecycle signals.

- Imports all three signals from the sibling `signals.py`.
- Three commented-out async receiver stubs — `on_{snake_name}_created`,
  `on_{snake_name}_updated`, `on_{snake_name}_deleted` — each with a docstring
  describing common use cases.
- Prominent file-level comment explaining the **startup import requirement**: without
  `import modules.{table_name}.listeners` in `main.py`, the `@signal.connect`
  decorators never run and receivers are never registered — signals fire silently
  with no effect.
- Comment includes the exact import line the developer needs to add to `main.py`.

#### `--signals` / `-s` flag on `make module`

The existing `make module` command gains an optional flag that additionally generates
`signals.py` and `listeners.py` alongside the standard module files.

- Default behaviour is unchanged — no extra files generated without the flag.
- Mode line in the generation header updates to reflect the combination:
  `sync + signals` or `async + signals`.
- "Next steps" output gains a fourth step with the startup import line when the flag
  is active.
- `--force` correctly overwrites `signals.py` and `listeners.py` along with all other
  module files.

```bash
fastkit make module Invoice --signals          # sync + signals
fastkit make module Invoice --async --signals  # async + signals
fastkit make module Invoice -a -s              # short flags
```

#### `make signals` standalone command

New command for adding signal infrastructure to an existing module without regenerating
the entire module. Follows the same pattern as the existing `make model`, `make schema`,
`make service`, `make repository`, and `make router` commands.

- Generates `signals.py` and `listeners.py` only — no other files touched.
- `--path` / `-p` option targets any directory; defaults to the current directory.
- `--force` / `-f` overwrites existing files.
- Skipped files are reported with a count and a reminder to use `--force`.
- "Next steps" output includes the startup import line.

```bash
fastkit make signals Invoice
fastkit make signals Invoice --path modules/invoices
fastkit make signals Invoice --force
```

---

### Changed

#### `schemas.py.jinja` — `BaseCreateSchema` and `BaseUpdateSchema`

The generated schema file now uses the appropriate base class for each schema type,
aligned with the three-class pattern introduced in fastkit-core 0.4.0.

| Schema class | Previous base | New base | Why |
|---|---|---|---|
| `{ModelName}Create` | `BaseSchema` | `BaseCreateSchema` | `extra='forbid'` + auto whitespace strip |
| `{ModelName}Update` | `BaseSchema` | `BaseUpdateSchema` | `extra='forbid'` + partial update convention |
| `{ModelName}Response` | `BaseSchema` | `BaseSchema` | unchanged — correct for response schemas |

**`BaseCreateSchema`** enforces `extra='forbid'` (returns `422` on unexpected fields,
preventing mass assignment) and automatically strips leading and trailing whitespace
from all string fields before validation runs.

**`BaseUpdateSchema`** enforces `extra='forbid'` and establishes the PATCH convention:
all fields should be declared as `Optional` with `None` as default so that only
explicitly provided fields are sent to the database.

Both `BaseCreateSchema` and `BaseUpdateSchema` are added to the import block alongside
the existing `BaseSchema`. Docstrings on each generated class explain the conventions
the base class enforces, so developers understand the behaviour without reading the docs.

This is a **breaking change for generated code** — any module generated with 0.1.x
will continue to work unchanged, but new modules generated with 0.2.0 will have
stricter validation by default.


---

### Requires

- **fastkit-core >= 0.4.0** — `BaseCreateSchema`, `BaseUpdateSchema`, and
  `fastkit_core.events.Signal` are all introduced in 0.4.0. Generating and running
  modules with the new templates requires the updated core package.

---

## [0.1.5] — Previous release

See git history for changes prior to 0.2.0.
