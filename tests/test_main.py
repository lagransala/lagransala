from unittest.mock import patch

from typer.testing import CliRunner

from lagransala.__main__ import app

runner = CliRunner()


def test_app():
    with (
        patch("lagransala.__main__.event_discovery_app") as mock_event_discovery,
        patch("lagransala.__main__.logging") as mock_logging,
    ):
        # Test event-discovery command
        result = runner.invoke(app, ["event-discovery"])
        assert result.exit_code == 0
        mock_event_discovery.assert_called_once()

        # Test --debug option
        runner.invoke(app, ["--debug", "event-discovery"])
        mock_logging.getLogger.assert_called_with("lagransala")
        mock_logging.getLogger.return_value.setLevel.assert_called_with(
            mock_logging.DEBUG
        )

        # Test no --debug option
        runner.invoke(app, ["event-discovery"])
        mock_logging.getLogger.assert_called_with("lagransala")
        mock_logging.getLogger.return_value.setLevel.assert_called_with(
            mock_logging.INFO
        )
