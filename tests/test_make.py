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