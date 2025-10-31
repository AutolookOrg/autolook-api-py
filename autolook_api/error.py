from typing import TYPE_CHECKING
import aiohttp

if TYPE_CHECKING:
    from .alapi import ApiRespError


class Error(BaseException):
    """Base Error"""
    def __init__(self, message=None):
        self.message = "AL Error"
        if message is not None:
            self.message += ": " + message
        super().__init__(self.message)
        
class ClientError(Error):
    # def __init__(self, message: str):
    #     self.message = message
    #     super().__init__(self.message)
    pass
    
class InvalidDomainError(Error):
    def __init__(self, domain: str):
        self.message = f"InvalidDomainError: The domain: '{domain}' has not been found, it is probably not for sale"
        super().__init__(self.message)

class ClosedClientError(Error):
    def __init__(self):
        self.message = f"ClosedClientError: The API client is closed, open it first with self.start() or use an async context"
        super().__init__(self.message)

class ApiConnectionError(Error):
    def __init__(self, url: str, e: aiohttp.ClientError):
        self.message = f"ApiConnectionError: Failed to connect to the API server: '{url}', internal error: {e}"
        super().__init__(self.message)

class RetriesExceededError(Error):
    def __init__(self, attempts: int, e: aiohttp.ClientError):
        self.message = f"RetriesExceededError: The total retries were exceeded doing an API request, attempts: {attempts}, last attempt err: {e}"
        super().__init__(self.message)

class ApiError(Error):
    def __init__(self, e: "ApiRespError"):
        self.message = f"ApiError: code: {e.code}, msg: {e.message}"
        super().__init__(self.message)

class InternalApiError(Error):
    def __init__(self, message: str):
        self.message = f"InternalApiError: The API server has misbehaved, err: {message}"
        super().__init__(self.message)

class InvalidRouteApiError(Error):
    def __init__(self, route: str):
        self.message = f"InvalidRouteError: The route '{route}' does not exist"
        super().__init__(self.message)

class UnauthorizedApiError(Error):
    def __init__(self, alacctoken: str):
        self.message = f"UnauthorizedError: The token '{alacctoken}' is not authorized"
        super().__init__(self.message)

class OnCooldownApiError(Error):
    def __init__(self, seconds: float):
        self.cooldown = seconds
        self.message = f"OnCooldownError: The action is on cooldown, retry again in: {self.cooldown}s"
        super().__init__(self.message)

class TempLockedApiError(Error):
    def __init__(self):
        self.message = f"TempLockedError: The action is temporarily locked, retry again in a bit"
        super().__init__(self.message)

class TimedOutError(Error):
    def __init__(self, after_seconds: float):
        self.after_seconds = after_seconds
        self.message = f"TimedOutError: Timed out after: {self.after_seconds} seconds"
        super().__init__(self.message)
