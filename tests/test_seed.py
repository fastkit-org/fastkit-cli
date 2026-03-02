"""Tests for fastkit_cli.commands.seed"""
from typer.testing import CliRunner
from fastkit_cli.commands.seed import app

runner = CliRunner()


class TestSeedCommand:
    def test_seed_all_exits_successfully(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0

    def test_seed_all_output(self):
        result = runner.invoke(app, [])
        assert "seeder" in result.output.lower()

    def test_seed_specific_seeder(self):
        result = runner.invoke(app, ["UserSeeder"])
        assert result.exit_code == 0
        assert "UserSeeder" in result.output

    def test_seed_invoice_seeder(self):
        result = runner.invoke(app, ["InvoiceSeeder"])
        assert result.exit_code == 0
        assert "InvoiceSeeder" in result.output