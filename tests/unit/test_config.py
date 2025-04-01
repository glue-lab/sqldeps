"""Unit tests for config.py.

This module tests configuration loading functionality.
"""

from unittest.mock import mock_open, patch

from sqldeps.config import load_config


def test_load_config() -> None:
    """Test loading configuration from a YAML file."""
    # Simple test YAML with nested keys
    config_yaml = """
    database:
      host: localhost
      port: 5432
    """

    # Mock file open
    with patch("builtins.open", mock_open(read_data=config_yaml)):
        config = load_config("fake_config.yml")

    # Verify basic parsing including nested values
    assert config["database"]["host"] == "localhost"
    assert config["database"]["port"] == 5432
