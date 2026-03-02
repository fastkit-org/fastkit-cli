"""Tests for fastkit_cli.commands.server"""
from typer.testing import CliRunner
from fastkit_cli.commands.server import app

runner = CliRunner()


class TestServerStart:
    def test_start_exits_successfully(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0

    def test_start_default_host_and_port(self):
        result = runner.invoke(app, [])
        assert "8000" in result.output
        assert "0.0.0.0" in result.output

    def test_start_custom_host(self):
        result = runner.invoke(app, ["--host", "127.0.0.1"])
        assert "127.0.0.1" in result.output

    def test_start_custom_port(self):
        result = runner.invoke(app, ["--port", "9000"])
        assert "9000" in result.output

    def test_start_custom_host_and_port(self):
        result = runner.invoke(app, ["--host", "127.0.0.1", "--port", "9000"])
        assert "127.0.0.1" in result.output
        assert "9000" in result.output