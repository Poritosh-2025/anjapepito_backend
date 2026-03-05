"""
DRF custom exception handler wrapping all errors into the standard envelope.
FIX #14 (OCP): Replaced if/elif chain with STATUS_MESSAGES mapping.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework import status

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    status.HTTP_401_UNAUTHORIZED: (
        "Authentication credentials were not provided."
    ),
    status.HTTP_403_FORBIDDEN: (
        "You do not have permission to perform this action."
    ),
    status.HTTP_404_NOT_FOUND: "Resource not found.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method not allowed.",
    status.HTTP_429_TOO_MANY_REQUESTS: (
        "Too many requests. Please try again later."
    ),
}


def custom_exception_handler(exc, context):
    """Wrap DRF exceptions into the standard {status, code, message, errors} envelope."""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception(
            "Unhandled exception in %s", context.get("view")
        )
        return None

    errors = {}
    code = response.status_code

    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            message = str(detail)
        else:
            errors = response.data
            message = "Validation failed."
    elif isinstance(response.data, list):
        errors = {"non_field_errors": response.data}
        message = "Validation failed."
    else:
        message = "An error occurred."

    # Override with canonical messages for known status codes
    if code in STATUS_MESSAGES and not errors:
        canonical = STATUS_MESSAGES[code]
        if isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])
        else:
            message = canonical

    response.data = {
        "status": False,
        "code": code,
        "message": message,
        "errors": errors,
    }
    return response
