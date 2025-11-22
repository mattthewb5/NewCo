"""
Simple logging utilities for debugging and monitoring.

Provides consistent logging across all modules with proper formatting
and configurable log levels.

Usage:
    from core.logger_utils import setup_logger

    logger = setup_logger(__name__)
    logger.info("Processing address: 123 Main St")
    logger.debug(f"API response: {response}")
    logger.warning("No results found")
    logger.error(f"API error: {error}")

Last Updated: November 2025
Phase: 4 - Operational Excellence
Status: Production-ready
"""

import logging
import sys
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("System started")
        2025-11-22 10:30:45 - mymodule - INFO - System started

        >>> logger = setup_logger(__name__, level="DEBUG")
        >>> logger.debug("Detailed debugging info")
        2025-11-22 10:30:45 - mymodule - DEBUG - Detailed debugging info
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Set format
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    # Set level
    logger.setLevel(getattr(logging, level.upper()))

    return logger


def setup_file_logger(
    name: str,
    log_file: str,
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up a logger that writes to a file.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level

    Returns:
        Configured file logger

    Example:
        >>> logger = setup_file_logger(__name__, "app.log")
        >>> logger.info("This goes to app.log")
    """
    logger = logging.getLogger(name)

    # Create file handler
    file_handler = logging.FileHandler(log_file)

    # Set format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Add handler
    logger.addHandler(file_handler)
    logger.setLevel(getattr(logging, level.upper()))

    return logger


def log_api_call(logger: logging.Logger, api_name: str, address: str, success: bool):
    """
    Log an API call with standard format.

    Args:
        logger: Logger instance
        api_name: Name of API (e.g., "LCPS School Locator")
        address: Address being queried
        success: Whether call succeeded

    Example:
        >>> logger = setup_logger(__name__)
        >>> log_api_call(logger, "LCPS API", "123 Main St", True)
        2025-11-22 10:30:45 - mymodule - INFO - LCPS API call: 123 Main St - SUCCESS
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"{api_name} call: {address} - {status}")


def log_cache_hit(logger: logging.Logger, cache_key: str):
    """
    Log a cache hit.

    Args:
        logger: Logger instance
        cache_key: Cache key that was hit

    Example:
        >>> logger = setup_logger(__name__)
        >>> log_cache_hit(logger, "school_lookup:abc123")
        2025-11-22 10:30:45 - mymodule - DEBUG - Cache HIT: school_lookup:abc123
    """
    logger.debug(f"Cache HIT: {cache_key}")


def log_performance(logger: logging.Logger, operation: str, duration_ms: float):
    """
    Log operation performance timing.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds

    Example:
        >>> logger = setup_logger(__name__)
        >>> log_performance(logger, "School lookup", 250.5)
        2025-11-22 10:30:45 - mymodule - INFO - Performance: School lookup took 250.5ms
    """
    logger.info(f"Performance: {operation} took {duration_ms:.1f}ms")


# Pre-configured loggers for common use cases
def get_api_logger(name: str = "api") -> logging.Logger:
    """Get a logger configured for API calls."""
    return setup_logger(f"api.{name}", level="INFO")


def get_debug_logger(name: str = "debug") -> logging.Logger:
    """Get a logger configured for debugging."""
    return setup_logger(f"debug.{name}", level="DEBUG")


# Example usage
if __name__ == "__main__":
    # Demo logging
    logger = setup_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    log_api_call(logger, "Test API", "123 Main St", True)
    log_api_call(logger, "Test API", "456 Oak Ave", False)

    log_performance(logger, "Sample operation", 123.45)
