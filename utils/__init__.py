"""
Utilities package for Door Installation Assistant
"""

from .file_utils import (
    ensure_directory,
    get_file_hash,
    get_file_type,
    save_uploaded_file,
    list_files_by_extension,
    get_file_size,
    get_file_size_human_readable,
    create_temp_file,
    delete_file
)

from .text_utils import (
    extract_keywords,
    normalize_text,
    extract_sentences,
    identify_door_type,
    extract_step_number,
    extract_tools,
    extract_measurements,
    calculate_text_similarity,
    STOPWORDS,
    DOOR_KEYWORDS
)

from .logging_utils import (
    setup_logger,
    get_class_logger,
    log_function_call,
    LoggerAdapter,
    create_session_logger,
    create_timed_log_directory,
    configure_async_logging
)

__all__ = [
    # File utilities
    "ensure_directory",
    "get_file_hash",
    "get_file_type",
    "save_uploaded_file",
    "list_files_by_extension",
    "get_file_size",
    "get_file_size_human_readable",
    "create_temp_file",
    "delete_file",
    
    # Text utilities
    "extract_keywords",
    "normalize_text",
    "extract_sentences",
    "identify_door_type",
    "extract_step_number",
    "extract_tools",
    "extract_measurements",
    "calculate_text_similarity",
    "STOPWORDS",
    "DOOR_KEYWORDS",
    
    # Logging utilities
    "setup_logger",
    "get_class_logger",
    "log_function_call",
    "LoggerAdapter",
    "create_session_logger",
    "create_timed_log_directory",
    "configure_async_logging"
]