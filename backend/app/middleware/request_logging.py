"""Request timing and correlation ID (no bodies or query values)."""

import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger("app.request")
REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = rid

        path = request.url.path
        t0 = time.perf_counter()
        response: Response | None = None
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            # Path only — never log query string (tokens, etc.).
            log.info(
                "request request_id=%s method=%s path=%s status=%s duration_ms=%s",
                rid,
                request.method,
                path,
                status,
                elapsed_ms,
            )
            if response is not None and REQUEST_ID_HEADER not in response.headers:
                response.headers[REQUEST_ID_HEADER] = rid
