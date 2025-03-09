"""
File handling utilities for Door Installation Assistant
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Union, BinaryIO
import mimetypes
import hashlib
import logging

logger = logging.getLogger(__name__)

def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 hash as a hexadecimal string
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def get_file_type(file_path: Union[str, Path]) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"

def save_uploaded_file(uploaded_file: BinaryIO, directory: Union[str, Path], filename: Optional[str] = None) -> Path:
    """
    Save an uploaded file to a directory.
    
    Args:
        uploaded_file: File-like object containing uploaded data
        directory: Directory to save the file to
        filename: Optional filename to use (if None, uses the uploaded filename or a temporary name)
        
    Returns:
        Path where the file was saved
    """
    # Ensure directory exists
    save_dir = ensure_directory(directory)
    
    # Determine filename
    if filename is None:
        if hasattr(uploaded_file, 'filename'):
            filename = Path(getattr(uploaded_file, 'filename')).name
        else:
            # Create a temporary filename if no name is provided
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                filename = Path(tmp.name).name
    
    # Create full path
    file_path = save_dir / filename
    
    # Save file
    if hasattr(uploaded_file, 'read'):
        # Handle file-like objects
        with open(file_path, 'wb') as f:
            content = uploaded_file.read()
            f.write(content)
    else:
        # Handle string path (copy file)
        shutil.copy2(uploaded_file, file_path)
    
    logger.info(f"Saved uploaded file to {file_path}")
    return file_path

def list_files_by_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    List all files with a specific extension in a directory.
    
    Args:
        directory: Directory to search
        extension: File extension to filter by (e.g., '.pdf')
        
    Returns:
        List of Path objects for matching files
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        logger.warning(f"Directory {directory} does not exist or is not a directory")
        return []
    
    # Normalize extension format
    if not extension.startswith('.'):
        extension = f".{extension}"
    
    return [f for f in dir_path.glob(f"*{extension}") if f.is_file()]

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    path = Path(file_path)
    return path.stat().st_size

def get_file_size_human_readable(file_path: Union[str, Path]) -> str:
    """
    Get file size in human-readable format.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Human-readable file size (e.g., "2.5 MB")
    """
    size_bytes = get_file_size(file_path)
    
    # Convert bytes to human-readable format
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            break
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} {unit}"

def create_temp_file() -> Tuple[Path, BinaryIO]:
    """
    Create a temporary file.
    
    Returns:
        Tuple containing the file path and the open file object
    """
    fd, path = tempfile.mkstemp()
    return Path(path), os.fdopen(fd, 'wb')

def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted file {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False