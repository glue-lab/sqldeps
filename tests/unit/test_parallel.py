"""Unit tests for parallel processing functionality.

This module tests the parallel execution of SQL dependency extraction
across multiple processes.
"""

from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sqldeps.parallel import (
    _extract_from_file,
    _process_batch_files,
    process_files_in_parallel,
    resolve_workers,
)


class TestParallelProcessing:
    """Test suite for parallel processing functionality."""

    def test_resolve_workers(self) -> None:
        """Test resolution of worker count."""
        with patch("sqldeps.parallel.cpu_count", return_value=8):
            # Default (-1) should use all CPUs
            assert resolve_workers(-1) == 8

            # Specific number within range
            assert resolve_workers(4) == 4

            # Minimum 1
            assert resolve_workers(1) == 1

            # Too large should raise ValueError
            with pytest.raises(ValueError):
                resolve_workers(9)

            # Too small should raise ValueError
            with pytest.raises(ValueError):
                resolve_workers(0)

    def test_extract_from_file_with_cache(self) -> None:
        """Test single file extraction with caching."""
        # Mock dependencies
        mock_limiter = MagicMock()
        mock_result = MagicMock()
        mock_path = Path("test.sql")

        # Mock cache hit
        with patch("sqldeps.parallel.load_from_cache", return_value=mock_result):
            # Should return cached result without extracting
            path, result = _extract_from_file(
                mock_path, mock_limiter, "groq", "model", None, True
            )

            assert path == mock_path
            assert result == mock_result
            mock_limiter.wait_if_needed.assert_not_called()

    def test_extract_from_file_without_cache(self) -> None:
        """Test single file extraction without cache hit."""
        # Mock dependencies
        mock_limiter = MagicMock()
        mock_extractor = MagicMock()
        mock_extractor.extract_from_file.return_value = "result"
        mock_path = Path("test.sql")

        # Setup no cache hit, extract successful
        with (
            patch("sqldeps.parallel.load_from_cache", return_value=None),
            patch("sqldeps.llm_parsers.create_extractor", return_value=mock_extractor),
            patch("sqldeps.parallel.save_to_cache") as mock_save,
        ):
            # Should perform extraction
            path, result = _extract_from_file(
                mock_path, mock_limiter, "groq", "model", None, True
            )

            assert path == mock_path
            assert result == "result"
            mock_limiter.wait_if_needed.assert_called_once()
            mock_extractor.extract_from_file.assert_called_once_with(mock_path)
            mock_save.assert_called_once()

    def test_process_batch_files(self) -> None:
        """Test batch processing of files."""
        # Mock dependencies
        mock_limiter = MagicMock()
        mock_files = [Path("test1.sql"), Path("test2.sql")]

        # Setup extraction results
        path1_result = MagicMock()
        path2_result = MagicMock()

        # Mock the extract_from_file function to return predetermined results
        with patch(
            "sqldeps.parallel._extract_from_file",
            side_effect=[(mock_files[0], path1_result), (mock_files[1], path2_result)],
        ):
            # Process batch
            results = _process_batch_files(
                mock_files, mock_limiter, "groq", "model", None, True
            )

            # Verify results
            assert len(results) == 2
            assert results[str(mock_files[0])] == path1_result
            assert results[str(mock_files[1])] == path2_result

    def test_process_files_in_parallel(self) -> None:
        """Test parallel file processing."""
        with (
            patch("sqldeps.parallel.ProcessPoolExecutor") as mock_executor_class,
            patch("sqldeps.parallel.Manager") as mock_manager,
            patch("sqldeps.parallel.MultiprocessingRateLimiter") as mock_limiter_class,
            patch("sqldeps.parallel.resolve_workers") as mock_resolve,
            patch("sqldeps.parallel.np.array_split") as mock_array_split,
        ):
            # Setup mocks
            mock_resolve.return_value = 2
            mock_sql_files = [
                Path("test1.sql"),
                Path("test2.sql"),
                Path("test3.sql"),
                Path("test4.sql"),
            ]
            mock_array_split.return_value = [
                [mock_sql_files[0], mock_sql_files[1]],
                [mock_sql_files[2], mock_sql_files[3]],
            ]

            # Mock the manager
            manager_instance = MagicMock()
            mock_manager.return_value.__enter__.return_value = manager_instance

            # Mock the limiter
            mock_limiter = MagicMock()
            mock_limiter_class.return_value = mock_limiter

            # Mock the ProcessPoolExecutor
            executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = executor_instance

            # Setup futures and their results
            future1 = MagicMock(spec=Future)
            future2 = MagicMock(spec=Future)
            future1.result.return_value = {
                str(mock_sql_files[0]): "result1",
                str(mock_sql_files[1]): "result2",
            }
            future2.result.return_value = {
                str(mock_sql_files[2]): "result3",
                str(mock_sql_files[3]): "result4",
            }

            # Mock the futures dictionary
            executor_instance.submit.side_effect = [future1, future2]

            # Mock as_completed to return futures in order
            with patch(
                "sqldeps.parallel.as_completed", return_value=[future1, future2]
            ):
                # Call the function
                results = process_files_in_parallel(
                    mock_sql_files,
                    framework="groq",
                    model="test-model",
                    n_workers=2,
                    rpm=60,
                    use_cache=True,
                )

                # Verify results
                assert len(results) == 4
                assert results[str(mock_sql_files[0])] == "result1"
                assert results[str(mock_sql_files[1])] == "result2"
                assert results[str(mock_sql_files[2])] == "result3"
                assert results[str(mock_sql_files[3])] == "result4"

                # Verify worker resolution
                mock_resolve.assert_called_once_with(2)

                # Verify batch splitting
                mock_array_split.assert_called_once()

                # Verify executor was created with correct workers
                mock_executor_class.assert_called_once_with(max_workers=2)

                # Verify submit was called for each batch
                assert executor_instance.submit.call_count == 2
