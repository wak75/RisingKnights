"""Logging configuration for Jenkins MCP Server."""

import logging
import sys
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

from ..config import config


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration with Rich formatting."""
    
    # Install rich traceback handler
    install(show_locals=config.debug)
    
    # Create console for rich output
    console = Console(stderr=True, force_terminal=True)
    
    # Configure logging level
    log_level = level or config.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("jenkins_mcp_server")
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create rich handler
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=config.debug,
        show_level=True,
        rich_tracebacks=True,
        tracebacks_show_locals=config.debug,
    )
    
    # Set formatter
    formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Set logging level for jenkins and httpx
    logging.getLogger("jenkins").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    if config.debug:
        logging.getLogger("jenkins").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"jenkins_mcp_server.{name}")


# Global logger instance
logger = setup_logging()