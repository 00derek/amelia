from unittest.mock import patch

from click.testing import CliRunner
from amelia.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "flights" in result.output
    assert "awards" in result.output
    assert "hotels" in result.output
    assert "config" in result.output


def test_awards_help():
    runner = CliRunner()
    result = runner.invoke(main, ["awards", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "trip" in result.output
    assert "availability" in result.output
    assert "live" in result.output
    assert "programs" in result.output
    assert "routes" in result.output


def test_awards_programs():
    runner = CliRunner()
    result = runner.invoke(main, ["awards", "programs"])
    assert result.exit_code == 0
    assert "united" in result.output
    assert "aeroplan" in result.output


def test_flights_help():
    runner = CliRunner()
    result = runner.invoke(main, ["flights", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output


def test_hotels_help():
    runner = CliRunner()
    result = runner.invoke(main, ["hotels", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output


def test_config_show_default():
    runner = CliRunner()
    result = runner.invoke(main, ["config", "show"])
    assert result.exit_code == 0
    assert "home_airport" in result.output


def test_flights_insights_help():
    runner = CliRunner()
    result = runner.invoke(main, ["flights", "insights", "--help"])
    assert result.exit_code == 0
    assert "--from" in result.output
    assert "--to" in result.output
    assert "--date" in result.output
    assert "--cabin" in result.output


def test_flights_insights_no_api_key():
    """Should exit with code 2 when SERPAPI_KEY is not set."""
    runner = CliRunner()
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(
            main,
            [
                "flights",
                "insights",
                "--from",
                "SFO",
                "--to",
                "GRU",
                "--date",
                "2026-07-18",
            ],
        )
    assert result.exit_code == 2
