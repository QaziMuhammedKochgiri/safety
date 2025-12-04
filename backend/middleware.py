"""
Middleware components for SafeChild Backend
- Rate Limiting
- Request Logging
- Security Headers
"""
import time
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict
import os

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger

logger = get_logger("safechild.middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    Limits requests per IP address.
    """

    def __init__(self, app, calls_per_minute: int = 60, auth_calls_per_minute: int = 10):
        super().__init__(app)
        self.calls_per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE", calls_per_minute))
        self.auth_calls_per_minute = int(os.environ.get("RATE_LIMIT_AUTH_PER_MINUTE", auth_calls_per_minute))
        self.requests: Dict[str, list] = defaultdict(list)
        self.auth_requests: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, ip: str, requests_dict: Dict[str, list]) -> None:
        """Remove requests older than 1 minute."""
        current_time = time.time()
        cutoff = current_time - 60
        requests_dict[ip] = [t for t in requests_dict[ip] if t > cutoff]

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxy headers."""
        # Check for forwarded headers (nginx proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Determine if this is an auth endpoint (stricter limits)
        is_auth_endpoint = "/auth/" in request.url.path and request.method == "POST"

        if is_auth_endpoint:
            self._clean_old_requests(client_ip, self.auth_requests)
            if len(self.auth_requests[client_ip]) >= self.auth_calls_per_minute:
                logger.warning(
                    f"Auth rate limit exceeded for IP: {client_ip}",
                    extra={"extra_fields": {"ip": client_ip, "endpoint": str(request.url.path)}}
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many authentication attempts. Please try again later.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
            self.auth_requests[client_ip].append(current_time)
        else:
            self._clean_old_requests(client_ip, self.requests)
            if len(self.requests[client_ip]) >= self.calls_per_minute:
                logger.warning(
                    f"Rate limit exceeded for IP: {client_ip}",
                    extra={"extra_fields": {"ip": client_ip, "endpoint": str(request.url.path)}}
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many requests. Please slow down.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
            self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks to reduce noise
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)

        start_time = time.time()

        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                    request.headers.get("X-Real-IP") or \
                    (request.client.host if request.client else "unknown")

        # Log incoming request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "method": request.method,
                "path": str(request.url.path),
                "query": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown")[:100]
            }}
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                extra={"extra_fields": {
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": client_ip
                }}
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={"extra_fields": {
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": client_ip
                }},
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers (some may be handled by nginx, but belt & suspenders)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header to hide implementation details
        if "server" in response.headers:
            del response.headers["server"]

        return response
