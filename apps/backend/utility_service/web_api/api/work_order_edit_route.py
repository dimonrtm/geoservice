from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from utility_service.web_api.api.exception_handlers import structured_error_response
from utility_service.web_api.parsers.geometry_save_request import GeometryRequestFormatError


class WorkOrderEditRoute(APIRoute):
    """Strict request errors scoped to the Save and workspace operations."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except (RequestValidationError, GeometryRequestFormatError):
                return structured_error_response(
                    request,
                    422,
                    "REQUEST_VALIDATION_ERROR",
                    "Некорректный формат запроса.",
                )

        return handle
