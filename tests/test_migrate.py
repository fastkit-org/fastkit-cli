"""Tests for fastkit_cli.commands.migrate"""
from unittest.mock import patch
from typer.testing import CliRunner
from fastkit_cli.commands.migrate import app

runner = CliRunner()


class TestMigrateRun:
    def test_run_exits_successfully(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["run"])

        assert result.exit_code == 0

    def test_run_output(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["run"])

        assert "migrations" in result.output.lower()

    def test_run_calls_alembic_upgrade_head(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run") as mock_run:
            runner.invoke(app, ["run"])

        cmd = mock_run.call_args.args[0]
        assert "alembic" in " ".join(cmd)
        assert "upgrade" in cmd
        assert "head" in cmd

    def test_run_alembic_not_found_exits_with_error(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(app, ["run"])

        assert result.exit_code == 1
        assert "alembic not found" in result.output

    def test_run_alembic_error_exits_with_code(self):
        import subprocess
        with patch("fastkit_cli.commands.migrate.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "alembic")):
            result = runner.invoke(app, ["run"])

        assert result.exit_code == 1

class TestMigrateMake:
    def test_make_with_message(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["make", "--message", "create_invoices"])

        assert result.exit_code == 0
        assert "create_invoices" in result.output

    def test_make_with_short_flag(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["make", "-m", "create_users"])

        assert result.exit_code == 0
        assert "create_users" in result.output

    def test_make_without_message_fails(self):
        result = runner.invoke(app, ["make"])
        assert result.exit_code != 0

    def test_make_calls_alembic_revision_autogenerate(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run") as mock_run:
            runner.invoke(app, ["make", "-m", "create_invoices"])

        cmd = mock_run.call_args.args[0]
        assert "revision" in cmd
        assert "--autogenerate" in cmd
        assert "-m" in cmd
        assert "create_invoices" in cmd

    def test_make_alembic_not_found_exits_with_error(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(app, ["make", "-m", "create_invoices"])

        assert result.exit_code == 1
        assert "alembic not found" in result.output

class TestMigrateRollback:
    def test_rollback_exits_successfully(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["rollback"])

        assert result.exit_code == 0

    def test_rollback_output(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run"):
            result = runner.invoke(app, ["rollback"])

        assert "rollback" in result.output.lower()

    def test_rollback_calls_alembic_downgrade(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run") as mock_run:
            runner.invoke(app, ["rollback"])

        cmd = mock_run.call_args.args[0]
        assert "downgrade" in cmd
        assert "-1" in cmd

    def test_rollback_alembic_not_found_exits_with_error(self):
        with patch("fastkit_cli.commands.migrate.subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(app, ["rollback"])

        assert result.exit_code == 1
        assert "alembic not found" in result.output