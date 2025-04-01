"""Parallel processing utilities for SQL dependency extraction.

This module provides functions for extracting SQL dependencies in parallel
using multiple worker processes, with shared rate limiting.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from multiprocessing import Manager, cpu_count
from pathlib import Path

import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from sqldeps.cache import load_from_cache, save_to_cache
from sqldeps.models import SQLProfile
from sqldeps.rate_limiter import MultiprocessingRateLimiter


def resolve_workers(n_workers: int) -> int:
    """Resolve the number of worker processes to use.

    Args:
        n_workers: Requested number of workers (-1 for all, >0 for specific count)

    Returns:
        int: Actual number of worker processes to use

    Raises:
        ValueError: If n_workers is invalid (not -1, or not between 1 and cpu_count)
    """
    max_workers = cpu_count()

    if n_workers == -1:
        return max_workers
    if 1 <= n_workers <= max_workers:
        return n_workers

    raise ValueError(
        f"Invalid worker count: {n_workers}. "
        f"Must be -1 (all), 1 (single), or up to {max_workers}."
    )


def _extract_from_file(
    file_path: Path,
    rate_limiter: MultiprocessingRateLimiter,
    framework: str,
    model: str,
    prompt_path: Path | None = None,
    use_cache: bool = True,
) -> tuple[Path, object]:
    """Process a single file with rate limiting and extraction.

    Args:
        file_path: Path to SQL file
        rate_limiter: Rate limiter instance
        framework: LLM framework to use
        model: Model name within the framework
        prompt_path: Optional path to custom prompt
        use_cache: Whether to use cache

    Returns:
        Tuple of (file_path, result) or (file_path, None) on failure
    """
    from sqldeps.llm_parsers import create_extractor

    # Check cache if enabled
    if use_cache:
        result = load_from_cache(file_path)
        if result:
            return file_path, result

    try:
        # Create extractor
        extractor = create_extractor(
            framework=framework, model=model, prompt_path=prompt_path
        )

        # Apply rate limiting and extract with retry
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
        def extract_with_rate_limit() -> SQLProfile:
            rate_limiter.wait_if_needed()
            logger.debug(f"Extracting from file: {file_path}")
            return extractor.extract_from_file(file_path)

        result = extract_with_rate_limit()

        # Save to cache if enabled
        if use_cache:
            save_to_cache(result, file_path)

        return file_path, result
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        return file_path, None


def _process_batch_files(
    batch_files: list[Path],
    rate_limiter: MultiprocessingRateLimiter,
    framework: str,
    model: str,
    prompt_path: Path | None = None,
    use_cache: bool = True,
) -> dict:
    """Process a batch of files with shared rate limiting.

    Args:
        batch_files: List of file paths to process
        rate_limiter: Shared rate limiter
        framework: LLM framework to use
        model: Model name
        prompt_path: Optional path to custom prompt
        use_cache: Whether to use cache

    Returns:
        Dictionary mapping file paths to results
    """
    results = {}

    for file_path in batch_files:
        path, result = _extract_from_file(
            file_path, rate_limiter, framework, model, prompt_path, use_cache
        )
        if result:
            results[str(path)] = result

    return results


def process_files_in_parallel(
    sql_files: list[Path],
    framework: str = "groq",
    model: str | None = None,
    prompt_path: Path | None = None,
    n_workers: int = 1,
    rpm: int = 100,
    use_cache: bool = True,
) -> dict:
    """Extract SQL dependencies from SQL files in parallel with rate limiting.

    Args:
        sql_files: List of Paths to SQL files to process
        framework: LLM framework to use (e.g., groq, openai, deepseek)
        model: Model name within the selected framework
        prompt_path: Path to custom prompt YAML file
        n_workers: Number of worker processes to use (-1 for all)
        rpm: Requests per minute limit across all workers
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping file paths to SQLProfile objects

    Raises:
        ValueError: If no SQL files provided or no dependencies extracted
    """
    # Resolve number of workers
    n_workers = resolve_workers(n_workers)

    # Ensure we have a list of Path objects
    sql_files = [Path(f) for f in sql_files]

    if not sql_files:
        raise ValueError("No SQL files provided")

    logger.info(f"Processing {len(sql_files)} SQL files")
    logger.info(
        f"Using {n_workers} workers with global rate limit of {rpm} requests per minute"
    )
    logger.info(f"Cache usage: {'enabled' if use_cache else 'disabled'}")

    # Calculate optimal number of workers (don't use more workers than files)
    n_workers = min(n_workers, len(sql_files))

    # Split files into batches
    batches = np.array_split(sql_files, n_workers)
    batches = [list(batch) for batch in batches if len(batch) > 0]

    all_results = {}

    # Create shared rate limiter
    with Manager() as manager:
        rate_limiter = MultiprocessingRateLimiter(manager, rpm)

        # Process batches in parallel
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            process_func = partial(
                _process_batch_files,
                rate_limiter=rate_limiter,
                framework=framework,
                model=model,
                prompt_path=prompt_path,
                use_cache=use_cache,
            )

            futures = {
                executor.submit(process_func, batch): i
                for i, batch in enumerate(batches)
            }

            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    batch_results = future.result()
                    all_results.update(batch_results)
                    logger.info(
                        f"Completed batch {batch_idx + 1}/{len(batches)} with "
                        f"{len(batch_results)} results"
                    )
                except Exception as e:
                    logger.error(f"Batch {batch_idx + 1} failed: {e}")

    # If no results were extracted
    if not all_results:
        raise ValueError("No dependencies could be extracted from any SQL file")

    return all_results
