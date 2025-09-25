"""
Security Utility Module

Provides secure path validation and file operation utilities to prevent
directory traversal attacks and ensure file operations stay within
allowed directories.
"""

import os
import logging
from pathlib import Path
from typing import Union, Optional
from ..config import settings

logger = logging.getLogger(__name__)


class PathTraversalError(Exception):
    """Raised when a path traversal attempt is detected"""
    pass


class SecurityConfig:
    """Security configuration constants"""
    
    # Characters and patterns that indicate potential path traversal
    DANGEROUS_PATTERNS = [
        "..",           # Parent directory references
        "~",            # Home directory reference
        "//",           # Double slashes (can bypass some filters)
        "\x00",         # Null bytes
        "\r",           # Carriage return
        "\n",           # Line feed
    ]
    
    # Dangerous path components
    DANGEROUS_COMPONENTS = {
        "..",
        ".",
        "~",
        "",             # Empty components from double slashes
    }
    
    # Maximum allowed path length (prevent DoS via extremely long paths)
    MAX_PATH_LENGTH = 4096
    
    # Maximum directory depth from base (prevent deep nesting attacks)
    MAX_DIRECTORY_DEPTH = 10


def validate_filename(filename: str) -> str:
    """
    Validate and sanitize a filename to prevent security issues.
    
    Args:
        filename: The filename to validate
        
    Returns:
        Sanitized filename
        
    Raises:
        PathTraversalError: If the filename contains dangerous patterns
        ValueError: If the filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")
    
    # Check if it's only whitespace
    if filename.isspace():
        raise ValueError("Filename must not be only whitespace")
    
    # Check length
    if len(filename) > SecurityConfig.MAX_PATH_LENGTH:
        raise PathTraversalError(f"Filename too long: {len(filename)} > {SecurityConfig.MAX_PATH_LENGTH}")
    
    # Check for dangerous patterns (before sanitization to detect attacks)
    filename_lower = filename.lower()
    for pattern in SecurityConfig.DANGEROUS_PATTERNS:
        if pattern in filename_lower:
            raise PathTraversalError(f"Dangerous pattern '{pattern}' detected in filename: {filename}")
    
    # Check for backslashes (Windows path separators)
    if "\\" in filename:
        raise PathTraversalError(f"Backslash path separator detected in filename: {filename}")
    
    # Check for null bytes and control characters
    if any(ord(char) < 32 and char not in '\t' for char in filename):
        raise PathTraversalError(f"Control characters detected in filename: {filename}")
    
    # Remove any forward slashes from filename (should only be a filename, not a path)
    sanitized = filename.replace("/", "_")
    
    # Ensure we still have a valid filename after sanitization
    if not sanitized or sanitized.isspace():
        raise ValueError("Filename becomes empty after sanitization")
    
    return sanitized


def secure_path_join(base_dir: Union[str, Path], *path_components: str) -> Path:
    """
    Securely join path components and validate the result stays within base_dir.
    
    Args:
        base_dir: The base directory that the result must stay within
        *path_components: Path components to join
        
    Returns:
        Resolved absolute path within base_dir
        
    Raises:
        PathTraversalError: If path traversal is attempted
        ValueError: If inputs are invalid
    """
    if not base_dir:
        raise ValueError("Base directory must be provided")
    
    # Convert base_dir to absolute Path
    base_path = Path(base_dir).resolve()
    
    # Validate base directory exists
    if not base_path.exists():
        logger.warning(f"Base directory does not exist: {base_path}")
        # Create it if it's the configured upload directory
        if str(base_path) == str(Path(settings.get_upload_path()).resolve()):
            base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created upload directory: {base_path}")
        else:
            raise ValueError(f"Base directory does not exist: {base_path}")
    
    if not base_path.is_dir():
        raise ValueError(f"Base path is not a directory: {base_path}")
    
    # Validate and sanitize path components
    sanitized_components = []
    for component in path_components:
        if not component or not isinstance(component, str):
            continue
            
        # Check component length
        if len(component) > SecurityConfig.MAX_PATH_LENGTH:
            raise PathTraversalError(f"Path component too long: {len(component)} > {SecurityConfig.MAX_PATH_LENGTH}")
        
        # Check for dangerous patterns in each component
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if pattern in component:
                raise PathTraversalError(f"Dangerous pattern '{pattern}' detected in path component: {component}")
        
        # Check for backslashes
        if "\\" in component:
            raise PathTraversalError(f"Backslash detected in path component: {component}")
        
        # Split by path separators and validate each part
        parts = []
        if "/" in component:
            parts.extend(component.split("/"))
        else:
            parts = [component]
        
        # Validate each part
        for part in parts:
            if part in SecurityConfig.DANGEROUS_COMPONENTS:
                raise PathTraversalError(f"Dangerous path component detected: {part}")
            if part.strip():  # Only add non-empty parts
                sanitized_components.append(part.strip())
    
    # Join components with base path
    if not sanitized_components:
        return base_path
    
    # Construct the target path
    target_path = base_path
    for component in sanitized_components:
        target_path = target_path / component
    
    # Resolve the final path
    try:
        resolved_path = target_path.resolve()
    except (OSError, RuntimeError) as e:
        raise PathTraversalError(f"Failed to resolve path: {e}")
    
    # Critical security check: ensure resolved path is within base directory
    try:
        resolved_path.relative_to(base_path)
    except ValueError:
        raise PathTraversalError(
            f"Path traversal attempt detected. Resolved path {resolved_path} "
            f"is outside base directory {base_path}"
        )
    
    # Check directory depth
    relative_path = resolved_path.relative_to(base_path)
    depth = len(relative_path.parts)
    if depth > SecurityConfig.MAX_DIRECTORY_DEPTH:
        raise PathTraversalError(f"Directory depth {depth} exceeds maximum {SecurityConfig.MAX_DIRECTORY_DEPTH}")
    
    return resolved_path


def secure_file_path(file_path: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Securely resolve a file path relative to a base directory.
    
    Args:
        file_path: The file path to resolve
        base_dir: Base directory (defaults to upload directory)
        
    Returns:
        Secure resolved file path
        
    Raises:
        PathTraversalError: If path traversal is attempted
        ValueError: If inputs are invalid
    """
    if not file_path:
        raise ValueError("File path must be provided")
    
    if base_dir is None:
        base_dir = settings.get_upload_path()
    
    # Handle absolute paths by extracting just the filename
    path_obj = Path(file_path)
    if path_obj.is_absolute():
        # Extract just the filename for security
        file_path = path_obj.name
        logger.warning(f"Absolute path provided, using filename only: {file_path}")
    
    return secure_path_join(base_dir, file_path)


def validate_file_access(file_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None, 
                        must_exist: bool = True) -> Path:
    """
    Validate that a file can be safely accessed.
    
    Args:
        file_path: Path to the file
        base_dir: Base directory (defaults to upload directory)  
        must_exist: Whether the file must exist
        
    Returns:
        Validated secure file path
        
    Raises:
        PathTraversalError: If path traversal is attempted
        FileNotFoundError: If must_exist=True and file doesn't exist
        ValueError: If inputs are invalid
    """
    secure_path = secure_file_path(str(file_path), base_dir)
    
    if must_exist and not secure_path.exists():
        raise FileNotFoundError(f"File not found: {secure_path}")
    
    # Additional validation for existing files
    if secure_path.exists():
        if not secure_path.is_file():
            raise ValueError(f"Path is not a regular file: {secure_path}")
        
        # Check if file is readable
        if not os.access(secure_path, os.R_OK):
            raise PermissionError(f"File is not readable: {secure_path}")
    
    return secure_path


def create_secure_upload_path(filename: str, document_id: Optional[str] = None) -> Path:
    """
    Create a secure path for uploading a file.
    
    Args:
        filename: Original filename
        document_id: Optional document ID to use as base filename
        
    Returns:
        Secure upload path
        
    Raises:
        PathTraversalError: If filename contains dangerous patterns
        ValueError: If inputs are invalid
    """
    # Sanitize the filename
    safe_filename = validate_filename(filename)
    
    # Use document ID as base name if provided
    if document_id:
        # Extract extension from original filename
        extension = Path(safe_filename).suffix
        safe_filename = f"{document_id}{extension}"
    
    # Create secure path in upload directory
    return secure_path_join(settings.get_upload_path(), safe_filename)


def log_security_event(event_type: str, details: dict, level: str = "WARNING"):
    """
    Log security-related events for monitoring.
    
    Args:
        event_type: Type of security event
        details: Event details
        level: Log level
    """
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logger.log(log_level, f"SECURITY EVENT - {event_type}: {details}")


# Convenience functions for common operations

def get_secure_upload_path() -> Path:
    """Get the secure upload directory path."""
    upload_path = Path(settings.get_upload_path()).resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe without raising exceptions.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename is safe, False otherwise
    """
    try:
        validate_filename(filename)
        return True
    except (PathTraversalError, ValueError):
        return False


def normalize_path_separators(path: str) -> str:
    """
    Normalize path separators to forward slashes.
    
    Args:
        path: Path string to normalize
        
    Returns:
        Path with normalized separators
    """
    return path.replace("\\", "/")