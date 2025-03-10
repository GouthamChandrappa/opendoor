# door_installation_assistant/config/logging_config.py
import os
import logging
import logging.handlers
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    # General logging settings
    level: str = Field("INFO", description="Default logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    date_format: str = Field(
        "%Y-%m-%d %H:%M:%S",
        description="Date format for logs"
    )
    
    # File logging settings
    log_to_file: bool = Field(True, description="Whether to log to file")
    log_file: str = Field("logs/door_assistant.log", description="Log file path")
    max_bytes: int = Field(10485760, description="Max log file size (10MB)")
    backup_count: int = Field(5, description="Number of backup log files")
    file_level: str = Field("DEBUG", description="Logging level for file handler")
    
    # Console logging settings
    log_to_console: bool = Field(True, description="Whether to log to console")
    console_level: str = Field("INFO", description="Logging level for console handler")
    
    # Module-specific logging levels
    module_levels: Dict[str, str] = Field(
        default_factory=lambda: {
            "door_installation_assistant.vector_storage": "INFO",
            "door_installation_assistant.retrieval": "INFO",
            "door_installation_assistant.llm_integration": "INFO",
            "door_installation_assistant.agent_system": "INFO",
            "door_installation_assistant.data_processing": "INFO",
            "door_installation_assistant.api": "INFO",
        },
        description="Module-specific logging levels"
    )
    
    class Config:
        env_prefix = "LOG_"
        env_file = ".env"
        extra = "ignore"

def get_logging_config() -> LoggingConfig:
    """Get the logging configuration."""
    return LoggingConfig()

def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Set up logging based on configuration.
    
    Args:
        config: Logging configuration. If None, default config is used.
    """
    if config is None:
        config = get_logging_config()
    
    # Create logs directory if it doesn't exist
    if config.log_to_file:
        os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(config.level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(config.format, config.date_format)
    
    # Add file handler if enabled
    if config.log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            config.log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count
        )
        file_handler.setLevel(logging.getLevelName(config.file_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if enabled
    if config.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.getLevelName(config.console_level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Set module-specific logging levels
    for module, level in config.module_levels.items():
        logger = logging.getLogger(module)
        logger.setLevel(logging.getLevelName(level))
    
    # Log startup message
    logging.info("Logging configured")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name, typically __name__ from the calling module.
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)