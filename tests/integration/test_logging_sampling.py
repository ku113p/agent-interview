from unittest.mock import patch

import pytest
import structlog

from src.logging import configure_logging, sampling_processor
from src.settings import settings


def test_sampling_processor_rate_100():
    """
    With sample rate 1.0, all logs should be returned.
    """
    with patch.object(settings, "LOG_SAMPLE_RATE", 1.0):
        # Should pass through
        event = {"level": "info", "event": "test"}
        result = sampling_processor(None, "info", event)
        assert result == event


def test_sampling_processor_rate_0():
    """
    With sample rate 0.0:
    - INFO/DEBUG should raise DropEvent
    - ERROR/WARNING should pass through
    """
    with patch.object(settings, "LOG_SAMPLE_RATE", 0.0):
        # INFO -> Drop
        with pytest.raises(structlog.DropEvent):
            sampling_processor(None, "info", {"level": "info", "event": "test"})

        # DEBUG -> Drop
        with pytest.raises(structlog.DropEvent):
            sampling_processor(None, "debug", {"level": "debug", "event": "test"})

        # ERROR -> Keep
        event_error = {"level": "error", "event": "error"}
        assert sampling_processor(None, "error", event_error) == event_error

        # WARNING -> Keep
        event_warn = {"level": "warning", "event": "warn"}
        assert sampling_processor(None, "warning", event_warn) == event_warn


def test_sampling_processor_rate_50():
    """
    With sample rate 0.5, verify random behavior.
    """
    with patch.object(settings, "LOG_SAMPLE_RATE", 0.5):
        with patch("src.logging.random.random") as mock_random:
            # Case 1: Keep (0.2 <= 0.5)
            # Logic: if random() > rate: drop. 0.2 is not > 0.5. So keep.
            mock_random.return_value = 0.2
            event = {"level": "info", "event": "test"}
            assert sampling_processor(None, "info", event) == event

            # Case 2: Drop (0.8 > 0.5)
            mock_random.return_value = 0.8
            with pytest.raises(structlog.DropEvent):
                sampling_processor(None, "info", {"level": "info", "event": "test"})


def test_processor_is_configured():
    """
    Verify that sampling_processor is actually added to the structlog configuration.
    """
    # Ensure configure_logging is called
    configure_logging()

    config = structlog.get_config()
    processors = config["processors"]

    # Check if sampling_processor is in the list
    assert sampling_processor in processors
