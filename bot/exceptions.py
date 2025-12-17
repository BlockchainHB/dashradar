"""Custom exceptions for the DoorDash Restaurant Finder bot."""


class BotError(Exception):
    """Base exception for all bot errors."""

    def __init__(self, message: str, user_message: str = None):
        """
        Args:
            message: Technical error message for logging
            user_message: User-friendly message to display
        """
        super().__init__(message)
        self.user_message = user_message or message


# Apify-related errors

class ApifyError(BotError):
    """Base exception for Apify API errors."""
    pass


class ApifyQuotaExceeded(ApifyError):
    """Monthly Apify quota exceeded."""

    def __init__(self):
        super().__init__(
            "Apify monthly quota exceeded",
            "Service temporarily unavailable. Please try again tomorrow."
        )


class ApifyTimeout(ApifyError):
    """Apify actor took too long to complete."""

    def __init__(self):
        super().__init__(
            "Apify actor timeout",
            "Search is taking longer than expected. Try a more specific address or smaller radius."
        )


class ApifyRateLimited(ApifyError):
    """Too many concurrent Apify requests."""

    def __init__(self):
        super().__init__(
            "Apify rate limited",
            "Too many searches in progress. Please wait a moment and try again."
        )


# Google-related errors

class GoogleError(BotError):
    """Base exception for Google API errors."""
    pass


class GoogleRateLimited(GoogleError):
    """Too many requests to Google."""

    def __init__(self):
        super().__init__(
            "Google rate limited",
            "Too many requests. Please wait a few minutes and try again."
        )


# Address-related errors

class InvalidAddressError(BotError):
    """Address could not be geocoded or is invalid."""

    def __init__(self, message: str = None):
        user_msg = message or "Could not find that address. Try including city and province/state."
        super().__init__(
            f"Invalid address: {message}",
            user_msg
        )


# Rate limiting errors

class RateLimitExceeded(BotError):
    """User has exceeded their rate limit."""

    def __init__(self, message: str):
        super().__init__(
            f"Rate limit exceeded: {message}",
            message
        )


class ConcurrentSearchError(BotError):
    """User already has a search in progress."""

    def __init__(self):
        super().__init__(
            "Concurrent search attempted",
            "You already have a search in progress. Please wait for it to complete."
        )


# Search-related errors

class NoResultsError(BotError):
    """No restaurants found in the search area."""

    def __init__(self, address: str = None):
        msg = "No restaurants found in that area."
        if address:
            msg = f"No restaurants found near {address}."
        super().__init__(
            f"No results: {address}",
            f"{msg} Try a larger radius or different location."
        )


class NoDoorDashError(BotError):
    """Restaurants found but none have DoorDash."""

    def __init__(self, restaurant_count: int):
        super().__init__(
            f"No DoorDash among {restaurant_count} restaurants",
            f"Found {restaurant_count} restaurants, but none have DoorDash on Google Maps."
        )


# Network errors

class NetworkError(BotError):
    """Network connectivity error."""

    def __init__(self, original_error: Exception = None):
        msg = "Connection error"
        if original_error:
            msg = f"Connection error: {type(original_error).__name__}"
        super().__init__(
            msg,
            "Connection error. Please check your internet and try again."
        )


# Helper function to get user-friendly message

def get_user_message(error: Exception) -> str:
    """
    Get a user-friendly error message from any exception.

    Args:
        error: Any exception

    Returns:
        User-friendly error message string
    """
    if isinstance(error, BotError):
        return error.user_message

    # Map common exceptions to friendly messages
    error_type = type(error).__name__

    if "Timeout" in error_type:
        return "The request timed out. Please try again."
    if "Connection" in error_type or "Network" in error_type:
        return "Connection error. Please check your internet and try again."

    return "An unexpected error occurred. Please try again later."
