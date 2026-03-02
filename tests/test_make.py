"""
Tests for fastkit_cli.commands.make

Coverage:
- Naming helpers: _to_snake_case, _to_pascal_case, _to_plural, _build_context
- File generation: _render_and_write
- Alembic registration: _register_in_alembic
- CLI commands: module, model, schema, repository, service, router
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from fastkit_cli.commands.make import (
    app,
    _to_snake_case,
    _to_pascal_case,
    _to_plural,
    _build_context,
    _render_and_write,
    _register_in_alembic,
)

runner = CliRunner()


# ─────────────────────────────────────────────────────────────────────────────
# _to_snake_case
# ─────────────────────────────────────────────────────────────────────────────

class TestToSnakeCase:
    def test_simple_pascal_case(self):
        assert _to_snake_case("Invoice") == "invoice"

    def test_compound_pascal_case(self):
        assert _to_snake_case("InvoiceItem") == "invoice_item"

    def test_already_snake_case(self):
        assert _to_snake_case("invoice_item") == "invoice_item"

    def test_all_uppercase_acronym(self):
        assert _to_snake_case("HTTPResponse") == "http_response"

    def test_single_lowercase_word(self):
        assert _to_snake_case("user") == "user"

    def test_three_word_pascal(self):
        assert _to_snake_case("UserProfileSettings") == "user_profile_settings"

    def test_camel_case(self):
        assert _to_snake_case("invoiceItem") == "invoice_item"

# ─────────────────────────────────────────────────────────────────────────────
# _to_plural
# ─────────────────────────────────────────────────────────────────────────────

class TestToPlural:
    def test_regular_word(self):
        assert _to_plural("invoice") == "invoices"

    def test_ends_with_y_consonant(self):
        assert _to_plural("category") == "categories"

    def test_ends_with_y_company(self):
        assert _to_plural("company") == "companies"

    def test_ends_with_ay(self):
        assert _to_plural("day") == "days"

    def test_ends_with_ey(self):
        assert _to_plural("key") == "keys"

    def test_ends_with_oy(self):
        assert _to_plural("boy") == "boys"

    def test_ends_with_s(self):
        assert _to_plural("status") == "statuses"

    def test_ends_with_sh(self):
        assert _to_plural("wish") == "wishes"

    def test_ends_with_ch(self):
        assert _to_plural("branch") == "branches"

    def test_ends_with_x(self):
        assert _to_plural("box") == "boxes"

    def test_compound_snake_case(self):
        assert _to_plural("invoice_item") == "invoice_items"


# ─────────────────────────────────────────────────────────────────────────────
# _to_pascal_case
# ─────────────────────────────────────────────────────────────────────────────

class TestToPascalCase:
    def test_snake_case_to_pascal(self):
        assert _to_pascal_case("invoice_item") == "InvoiceItem"

    def test_already_pascal_case(self):
        assert _to_pascal_case("Invoice") == "Invoice"

    def test_lowercase_single_word(self):
        assert _to_pascal_case("invoice") == "Invoice"

    def test_words_with_spaces(self):
        assert _to_pascal_case("invoice item") == "InvoiceItem"

    def test_words_with_hyphens(self):
        assert _to_pascal_case("invoice-item") == "InvoiceItem"

    def test_three_word_snake(self):
        assert _to_pascal_case("user_profile_settings") == "UserProfileSettings"


# ─────────────────────────────────────────────────────────────────────────────
# _build_context
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildContext:
    def test_invoice_pascal_input(self):
        ctx = _build_context("Invoice")
        assert ctx["model_name"] == "Invoice"
        assert ctx["snake_name"] == "invoice"
        assert ctx["table_name"] == "invoices"
        assert ctx["module_folder"] == "invoices"

    def test_snake_case_input(self):
        ctx = _build_context("invoice_item")
        assert ctx["model_name"] == "InvoiceItem"
        assert ctx["snake_name"] == "invoice_item"
        assert ctx["table_name"] == "invoice_items"

    def test_lowercase_input(self):
        ctx = _build_context("user")
        assert ctx["model_name"] == "User"
        assert ctx["snake_name"] == "user"
        assert ctx["table_name"] == "users"

    def test_category_pluralization(self):
        ctx = _build_context("Category")
        assert ctx["table_name"] == "categories"

    def test_context_has_all_required_keys(self):
        ctx = _build_context("Invoice")
        assert set(ctx.keys()) == {"model_name", "snake_name", "table_name", "module_folder"}

    def test_module_folder_always_equals_table_name(self):
        for name in ["Invoice", "Category", "InvoiceItem", "User"]:
            ctx = _build_context(name)
            assert ctx["module_folder"] == ctx["table_name"]

# ─────────────────────────────────────────────────────────────────────────────
# _render_and_write
# ─────────────────────────────────────────────────────────────────────────────

class TestRenderAndWrite:
    def test_creates_new_file(self, tmp_path):
        output_path = tmp_path / "models.py"
        context = _build_context("Invoice")

        with patch("fastkit_cli.commands.make._render_template", return_value="# generated"):
            _render_and_write("model.py.jinja", output_path, context)

        assert output_path.exists()
        assert output_path.read_text() == "# generated"

    def test_skips_existing_file_by_default(self, tmp_path):
        output_path = tmp_path / "models.py"
        output_path.write_text("# original")
        skipped = []

        with patch("fastkit_cli.commands.make._render_template", return_value="# generated"):
            _render_and_write("model.py.jinja", output_path, _build_context("Invoice"), skipped=skipped)

        assert output_path.read_text() == "# original"
        assert "models.py" in skipped

    def test_overwrites_with_force(self, tmp_path):
        output_path = tmp_path / "models.py"
        output_path.write_text("# original")

        with patch("fastkit_cli.commands.make._render_template", return_value="# generated"):
            _render_and_write("model.py.jinja", output_path, _build_context("Invoice"), force=True)

        assert output_path.read_text() == "# generated"

    def test_handles_render_exception_gracefully(self, tmp_path):
        output_path = tmp_path / "models.py"

        with patch("fastkit_cli.commands.make._render_template", side_effect=Exception("Template error")):
            _render_and_write("model.py.jinja", output_path, _build_context("Invoice"))

        assert not output_path.exists()

    def test_skipped_list_unchanged_when_file_written(self, tmp_path):
        output_path = tmp_path / "models.py"
        skipped = []

        with patch("fastkit_cli.commands.make._render_template", return_value="# generated"):
            _render_and_write("model.py.jinja", output_path, _build_context("Invoice"), skipped=skipped)

        assert skipped == []

    def test_skipped_none_does_not_raise_on_existing_file(self, tmp_path):
        output_path = tmp_path / "models.py"
        output_path.write_text("# original")

        with patch("fastkit_cli.commands.make._render_template", return_value="# generated"):
            _render_and_write("model.py.jinja", output_path, _build_context("Invoice"), force=False, skipped=None)

        assert output_path.read_text() == "# original"

    def test_passes_correct_context_to_render(self, tmp_path):
        output_path = tmp_path / "models.py"
        context = _build_context("Invoice")

        with patch("fastkit_cli.commands.make._render_template", return_value="# ok") as mock_render:
            _render_and_write("model.py.jinja", output_path, context)

        mock_render.assert_called_once_with("model.py.jinja", context)


