from enum import Enum

class AppError(Exception):
    """Base class for all custom exceptions in the application."""
    pass


class AuthError(AppError):
    """Raised when credentials are invalid."""
    def __init__(self):
        message = f"Wrong login credentials. Change credentials and try again."
        super().__init__(message)


class TokenError(AppError):
    """Raised when token is invalid."""
    def __init__(self):
        message = f"Wrong token."
        super().__init__(message)


class PlatformError(AppError):
    """Raised when platform return 500."""
    def __init__(self, request_name: Enum):
        message = f"Platform failed to process request {request_name.value}."
        super().__init__(message)



class MaxRetriesExceededError(AppError):
    """Raised when request retries exceeded."""
    def __init__(self, request_name: str):
        message = f"Maximum request tries exceeded for {request_name}."
        super().__init__(message)


class MissingCredentialsError(AppError):
    """Raised when login or password is missing."""
    def __init__(self):
        message = f"Authentication credentials missing."
        super().__init__(message)


class FailedDownloadPolls(AppError):
    """Raised when failed to download poll."""
    def __init__(self, failed_poll_ids: set[int]):
        message = f"Failed download polls."
        self.failed_ids = failed_poll_ids
        super().__init__(message)



