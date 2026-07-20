from __future__ import annotations

import json
import logging

from fastapi import Request

from utility_service.web_api.middleware.correlation_id import get_correlation_id


API_ERROR_LOGGER_NAME = "utility_service.api_errors"
_logger = logging.getLogger(API_ERROR_LOGGER_NAME)


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) and path else "<unmatched>"


def _event(request: Request, *, event: str, code: str, status: int) -> dict[str, object]:
    return {
        "event": event,
        "correlationId": get_correlation_id(request),
        "code": code,
        "status": status,
        "method": request.method,
        "route": _route_template(request),
    }


def log_handled_api_error(request: Request, *, code: str, status: int) -> None:
    level = logging.INFO if status < 500 else logging.ERROR
    payload = _event(request, event="api_error_handled", code=code, status=status)
    _logger.log(level, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def log_unhandled_api_error(request: Request, error: Exception) -> None:
    payload = _event(
        request,
        event="api_error_unhandled",
        code="INTERNAL_ERROR",
        status=500,
    )
    _logger.error(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        exc_info=(type(error), error, error.__traceback__),
    )
