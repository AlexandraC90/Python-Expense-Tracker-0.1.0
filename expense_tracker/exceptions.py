class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


class StorageError(Exception):
    """Raised on storage-related failures (I/O, permissions, etc.)."""
    pass


class OperationCancelled(Exception):
    """Raised when the user requests to cancel the current operation."""
    pass
