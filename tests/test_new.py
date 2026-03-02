"""Tests for fastkit_cli.commands.new"""
from typer.testing import CliRunner
from fastkit_cli.commands.new import app

runner = CliRunner()


class TestNewCommand:
    def test_create_project_exits_successfully(self):
        result = runner.invoke(app, ["my-project"])
        assert result.exit_code == 0

    def test_create_project_output_contains_name(self):
        result = runner.invoke(app, ["my-project"])
        assert "my-project" in result.output

    def test_create_project_requires_name(self):
        result = runner.invoke(app, [])
        assert result.exit_code != 0