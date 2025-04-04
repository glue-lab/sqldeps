"""Caching utilities for SQL dependency extraction.

This module provides functions for caching extraction results to avoid
repeatedly processing the same SQL files, which can save API calls, cost, and time.
"""

import hashlib
import json
from pathlib import Path

from loguru import logger

from sqldeps.models import SQLProfile

CACHE_DIR = ".sqldeps_cache"


def get_cache_path(file_path: str | Path, cache_dir: str | Path = CACHE_DIR) -> Path:
    """Generate a consistent cache file path based on SQL file content.

    Creates a unique cache filename by hashing the SQL file's content.
    Includes the original filename in the cache name for easier debugging.

    Args:
        file_path: Path to the SQL file to be processed
        cache_dir: Directory where cache files will be stored.
                   Defaults to ".sqldeps_cache"

    Returns:
        Path object pointing to the cache file location

    Raises:
        FileNotFoundError: If the SQL file doesn't exist
        PermissionError: If the SQL file can't be read
    """
    file_path = Path(file_path).resolve()

    # Read file content and create hash
    with open(file_path, "rb") as f:
        content = f.read()

    # Hash the content
    content_hash = hashlib.md5(content).hexdigest()[:16]

    # Use a combination of filename and content hash for better readability/debugging
    cache_name = f"{file_path.stem}_{content_hash}"

    # Ensure a valid filename
    cache_name = "".join(c if c.isalnum() or c in "_-." else "_" for c in cache_name)

    return Path(cache_dir) / f"{cache_name}.json"


def save_to_cache(
    result: SQLProfile, file_path: Path, cache_dir: Path = Path(CACHE_DIR)
) -> bool:
    """Save extraction result to cache.

    Args:
        result: The SQLProfile to save
        file_path: The original SQL file path
        cache_dir: The cache directory

    Returns:
        True if saved successfully, False otherwise
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = get_cache_path(file_path, cache_dir)

    try:
        with open(cache_file, "w") as f:
            json.dump(result.to_dict(), f)
        return True
    except Exception as e:
        logger.warning(f"Failed to save cache for {file_path}: {e}")
        return False


def load_from_cache(
    file_path: Path, cache_dir: Path = Path(CACHE_DIR)
) -> SQLProfile | None:
    """Load extraction result from cache.

    Args:
        file_path: The original SQL file path
        cache_dir: The cache directory

    Returns:
        SQLProfile if loaded successfully, None otherwise
    """
    cache_file = get_cache_path(file_path, cache_dir)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file) as f:
            cached_data = json.load(f)
            logger.info(f"Loading from cache: {file_path}")
            return SQLProfile(**cached_data)
    except Exception as e:
        logger.warning(f"Failed to load cache for {file_path}: {e}")
        return None


def cleanup_cache(cache_dir: Path = Path(CACHE_DIR)) -> bool:
    """Clean up cache directory.

    Args:
        cache_dir: The cache directory to clean up

    Returns:
        True if cleaned up successfully, False otherwise
    """
    if not cache_dir.exists():
        return True

    try:
        # Remove all JSON files
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()

        # Try to remove directory if empty
        if not any(cache_dir.iterdir()):
            cache_dir.rmdir()
            logger.info(f"Removed cache directory: {cache_dir}")
        else:
            logger.info(
                "Cache directory cleaned but not removed (contains other files)"
            )
        return True
    except Exception as e:
        logger.warning(f"Failed to clean up cache: {e}")
        return False
