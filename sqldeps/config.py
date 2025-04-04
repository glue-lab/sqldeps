"""Configuration utilities for SQLDeps.

This module provides functions for loading configuration from YAML files.
"""

import yaml


def load_config(config_path: str) -> dict:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        dict: Parsed configuration dictionary
    """
    with open(config_path) as config_file:
        config = yaml.safe_load(config_file)
    return config
