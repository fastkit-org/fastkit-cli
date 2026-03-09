"""Tests for fastkit_cli.commands.server"""
from unittest.mock import patch
from typer.testing import CliRunner
from fastkit_cli.commands.server import app

runner = CliRunner()


class TestServerStart:
    def test_start_exits_successfully(self):
        with patch("fastkit_cli.commands.server.subprocess.run"):
            result = runner.invoke(app, [])

        assert result.exit_code == 0

    def test_start_default_host_and_port(self):
        with patch("fastkit_cli.commands.server.subprocess.run"):
            result = runner.invoke(app, [])

        assert "8000" in result.output
        assert "0.0.0.0" in result.output

    def test_start_custom_host(self):
        with patch("fastkit_cli.commands.server.subprocess.run"):
            result = runner.invoke(app, ["--host", "127.0.0.1"])

        assert "127.0.0.1" in result.output

    def test_start_custom_port(self):
        with patch("fastkit_cli.commands.server.subprocess.run"):
            result = runner.invoke(app, ["--port", "9000"])

        assert "9000" in result.output

    def test_start_custom_host_and_port(self):
        with patch("fastkit_cli.commands.server.subprocess.run"):
            result = runner.invoke(app, ["--host", "127.0.0.1", "--port", "9000"])

        assert "127.0.0.1" in result.output
        assert "9000" in result.output

    def test_reload_flag_passed_to_uvicorn(self):
        with patch("fastkit_cli.commands.server.subprocess.run") as mock_run:
            runner.invoke(app, [])

        cmd = mock_run.call_args.args[0]
        assert "--reload" in cmd

    def test_no_reload_flag_not_passed(self):
        with patch("fastkit_cli.commands.server.subprocess.run") as mock_run:
            runner.invoke(app, ["--no-reload"])

        cmd = mock_run.call_args.args[0]
        assert "--reload" not in cmd

    def test_default_app_path(self):
        with patch("fastkit_cli.commands.server.subprocess.run") as mock_run:
            runner.invoke(app, [])

        cmd = mock_run.call_args.args[0]
        assert "main:app" in cmd

    def test_custom_app_path(self):
        with patch("fastkit_cli.commands.server.subprocess.run") as mock_run:
            runner.invoke(app, ["--app", "src.main:app"])

        cmd = mock_run.call_args.args[0]
        assert "src.main:app" in cmd

    def test_uvicorn_not_found_exits_with_error(self):
        with patch("fastkit_cli.commands.server.subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(app, [])

        assert result.exit_code == 1
        assert "uvicorn not found" in result.output