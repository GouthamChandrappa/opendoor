"""
Logging utilities for Door Installation Assistant
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union

def setup_logger(
    name: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    rotate: bool = True,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name (if None, use root logger)
        log_file: Log file path
        level: Logging level
        log_format: Log format string
        rotate: Whether to use rotating file handler
        max_bytes: Maximum log file size for rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger
    """
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Default format if not specified
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if rotate:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
        else:
            file_handler = logging.FileHandler(log_file)
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_class_logger(cls: Any) -> logging.Logger:
    """
    Get a logger for a class.
    
    Args:
        cls: Class to get logger for
        
    Returns:
        Logger for the class
    """
    return logging.getLogger(f"{cls.__module__}.{cls.__name__}")

def log_function_call(logger: logging.Logger, level: int = logging.DEBUG):
    """
    Decorator to log function calls.
    
    Args:
        logger: Logger to use
        level: Logging level
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.log(level, f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context information to log messages.
    """
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any] = None):
        """
        Initialize the adapter.
        
        Args:
            logger: Logger to adapt
            extra: Extra context to add to log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the log message.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (modified message, modified kwargs)
        """
        context_str = ' '.join(f"[{k}={v}]" for k, v in self.extra.items())
        return f"{context_str} {msg}", kwargs

def create_session_logger(session_id: str, name: Optional[str] = None) -> logging.LoggerAdapter:
    """
    Create a logger adapter with session context.
    
    Args:
        session_id: Session ID
        name: Logger name (if None, use root logger)
        
    Returns:
        Logger adapter with session context
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, {"session_id": session_id})

def create_timed_log_directory(base_dir: Union[str, Path], prefix: str = "log_") -> Path:
    """
    Create a log directory with timestamp.
    
    Args:
        base_dir: Base directory
        prefix: Directory name prefix
        
    Returns:
        Path to created directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(base_dir) / f"{prefix}{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def configure_async_logging(base_dir: Union[str, Path] = "logs") -> logging.Logger:
    """
    Configure logging for async applications.
    
    Args:
        base_dir: Base log directory
        
    Returns:
        Configured logger
    """
    # Create timed log directory
    log_dir = create_timed_log_directory(base_dir)
    
    # Configure root logger
    logger = setup_logger(
        log_file=log_dir / "app.log",
        level=logging.INFO,
        log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        rotate=True
    )
    
    # Configure library loggers to be less verbose
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured in directory: {log_dir}")
    return logger