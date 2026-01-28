from unittest.mock import patch

from typer.testing import CliRunner

from lagransala.__main__ import app

runner = CliRunner()


def test_app():
    with patch("lagransala.__main__.event_discovery_app") as mock_event_discovery:
        # Test event-discovery command
        result = runner.invoke(app, ["event-discovery"])
        assert result.exit_code == 0
        mock_event_discovery.assert_called_once()
