"""Logging utilities for Integro."""

import logging
import warnings
from typing import Optional


def setup_logging(level: str = "INFO", suppress_warnings: bool = True) -> None:
    """
    Setup logging configuration for Integro.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        suppress_warnings: Whether to suppress warnings from dependencies
    """
    # Ben, set up basic logging format for the whole app
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if suppress_warnings:
        # Ben, quiet down all the noise from libraries
        warnings.filterwarnings("ignore")
        
        # Ben, hide deprecation warnings we can't fix right now
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # Ben, Pydantic v2 migration warnings are annoying
        warnings.filterwarnings("ignore", message=".*model_fields.*")
        warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*")
        
        # Ben, only show errors from these chatty libraries
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("httpcore").setLevel(logging.ERROR)
        logging.getLogger("openai").setLevel(logging.ERROR)
        logging.getLogger("anthropic").setLevel(logging.ERROR)
        logging.getLogger("groq").setLevel(logging.ERROR)
        logging.getLogger("agno").setLevel(logging.ERROR)
        logging.getLogger("pydantic").setLevel(logging.ERROR)
        logging.getLogger("qdrant_client").setLevel(logging.ERROR)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (defaults to 'integro')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name or "integro")