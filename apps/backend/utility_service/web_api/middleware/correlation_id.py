from __future__ import annotations

import re
from uuid import uuid4

from fastapi import Request
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


CORRELATION_ID_HEADER = "X-Correlation-ID"
CORRELATION_ID_STATE_KEY = "correlation_id"
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def is_valid_correlation_id(value: object) -> bool:
    return isinstance(value, str) and _CORRELATION_ID_PATTERN.fullmatch(value) is not None


def get_correlation_id(request: Request) -> str:
    correlation_id = getattr(request.state, CORRELATION_ID_STATE_KEY, None)
    if not is_valid_correlation_id(correlation_id):
        raise RuntimeError("CorrelationIdMiddleware не установил request correlation ID")
    return correlation_id


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(CORRELATION_ID_HEADER)
        correlation_id = incoming if is_valid_correlation_id(incoming) else str(uuid4())
        scope.setdefault("state", {})[CORRELATION_ID_STATE_KEY] = correlation_id

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[CORRELATION_ID_HEADER] = correlation_id
            await send(message)

        await self.app(scope, receive, send_with_correlation_id)
