# tests/test_cache.py
import json
from pathlib import Path
from unittest.mock import mock_open, patch

from sqldeps.cache import cleanup_cache, get_cache_path, load_from_cache, save_to_cache
from sqldeps.models import SQLProfile


def test_get_cache_path():
    """Test generation of cache file paths."""
    # Test relative to current directory
    with (
        patch("pathlib.Path.resolve") as mock_resolve,
        patch("pathlib.Path.relative_to") as mock_relative_to,
    ):
        mock_resolve.return_value = Path("/absolute/path/to/file.sql")
        mock_relative_to.return_value = Path("relative/path/to/file.sql")

        cache_path = get_cache_path("file.sql")
        assert str(cache_path) == ".sqldeps_cache/relative_path_to_file.sql.json"

    # Test with external path (hash-based)
    with (
        patch("pathlib.Path.resolve") as mock_resolve,
        patch("pathlib.Path.relative_to") as mock_relative_to,
        patch("hashlib.md5") as mock_md5,
    ):
        mock_resolve.return_value = Path("/external/path/script.sql")
        mock_relative_to.side_effect = ValueError("Not relative")
        mock_md5().hexdigest.return_value = "abcdef1234567890"

        cache_path = get_cache_path("/external/path/script.sql")
        assert "script_abcdef1234" in str(cache_path)


def test_save_load_cache():
    """Test saving and loading from cache."""
    # Create a test SQLProfile
    profile = SQLProfile(
        dependencies={"table1": ["col1"]}, outputs={"table2": ["col2"]}
    )

    # Mock file operations
    mock_file_content = json.dumps(profile.to_dict())

    with (
        patch("sqldeps.cache.get_cache_path") as mock_get_path,
        patch("builtins.open", mock_open(read_data=mock_file_content)),
    ):
        # Setup mock path
        mock_cache_path = Path(".sqldeps_cache/test.json")
        mock_get_path.return_value = mock_cache_path

        # Test saving to cache
        result = save_to_cache(profile, "test.sql")
        assert result is True

        # Test loading from cache
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            loaded = load_from_cache("test.sql")
            assert loaded.dependencies == profile.dependencies
            assert loaded.outputs == profile.outputs


def test_cleanup_cache_success():
    """Test successful cleanup of cache directory."""
    # Setup - create a mock cache directory with some files
    mock_cache_dir = Path("mock_cache_dir")
    mock_json_files = [
        Path("mock_cache_dir/file1.json"),
        Path("mock_cache_dir/file2.json"),
    ]

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
        patch("pathlib.Path.unlink") as mock_unlink,
        patch("pathlib.Path.iterdir", return_value=[]),
        patch("pathlib.Path.rmdir") as mock_rmdir,
        patch("sqldeps.cache.logger") as mock_logger,
    ):
        # Setup mock glob to return our json files
        mock_glob.return_value = mock_json_files

        # Call the function
        result = cleanup_cache(mock_cache_dir)

        # Verify the result
        assert result is True
        assert mock_unlink.call_count == 2  # Should unlink both JSON files
        mock_rmdir.assert_called_once()  # Should remove the directory
        mock_logger.info.assert_called()  # Should log success


def test_cleanup_cache_non_empty_dir():
    """Test cleanup when directory still has other files."""
    mock_cache_dir = Path("mock_cache_dir")

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
        patch("pathlib.Path.unlink") as mock_unlink,
        patch("pathlib.Path.iterdir", return_value=["other_file"]),
        patch("pathlib.Path.rmdir") as mock_rmdir,
        patch("sqldeps.cache.logger") as mock_logger,
    ):
        # Setup mock glob to return JSON files
        mock_glob.return_value = [Path("mock_cache_dir/file1.json")]

        # Call the function
        result = cleanup_cache(mock_cache_dir)

        # Verify the result
        assert result is True
        assert mock_unlink.call_count == 1  # Should unlink the JSON file
        mock_rmdir.assert_not_called()  # Should not remove non-empty directory
        mock_logger.info.assert_called_with(
            "Cache directory cleaned but not removed (contains other files)"
        )


def test_cleanup_cache_error():
    """Test cleanup when an error occurs."""
    mock_cache_dir = Path("mock_cache_dir")

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
        patch("sqldeps.cache.logger") as mock_logger,
    ):
        # Make glob raise an exception
        mock_glob.side_effect = Exception("Test error")

        # Call the function
        result = cleanup_cache(mock_cache_dir)

        # Verify the result
        assert result is False
        mock_logger.warning.assert_called_once()  # Should log warning


def test_cleanup_cache_nonexistent():
    """Test cleanup when cache directory doesn't exist."""
    mock_cache_dir = Path("nonexistent_dir")

    with patch("pathlib.Path.exists", return_value=False):
        # Call the function
        result = cleanup_cache(mock_cache_dir)

        # Verify the result
        assert result is True  # Should return True when directory doesn't exist
