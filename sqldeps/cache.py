"""Caching utilities for SQL dependency extraction."""

import hashlib
import json
import os
from pathlib import Path

from loguru import logger

from sqldeps.models import SQLProfile

CACHE_DIR = ".sqldeps_cache"


def get_cache_path(file_path: str | Path, cache_dir: str | Path = CACHE_DIR) -> Path:
    """Generates a consistent cache file path for a given SQL file.

    Converts file paths to unique cache filenames by using either a relative path
    or a hash-based name (for external files).

    Args:
        file_path: Path to the SQL file to be processed
        cache_dir: Directory where cache files will be stored.
                   Defaults to ".sqldeps_cache"

    Returns:
        Path object pointing to the cache file location
    """
    file_path = Path(file_path).resolve()

    try:
        # Use relative path for readability
        cache_name = str(file_path.relative_to(Path.cwd())).replace(os.sep, "_")
    except ValueError:
        # Use a hash for external paths
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:10]
        cache_name = f"{file_path.stem}_{path_hash}"

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
