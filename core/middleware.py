"""Request logging and performance monitoring middleware."""
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Logs every request with timing, method, path, status, and correlation ID."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.correlation_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "[%s] %s %s -> %s (%.1fms)",
            request.correlation_id,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )

        response["X-Correlation-ID"] = request.correlation_id
        response["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
        return response
