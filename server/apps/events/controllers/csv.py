from collections.abc import Mapping
from http import HTTPStatus
from typing import ClassVar, override

from django.http import HttpResponse
from dmr.cookies import NewCookie
from dmr.metadata import ResponseSpec
from dmr.renderers import FileRenderer, JsonRenderer, Renderer

from server.apps.events.controllers.base import EventController
from server.common.django.renderers import FallbackHtmlRenderer
from server.common.value_objects import ErrorResponse

CSV_MIME = 'text/csv'


class CsvController(EventController):
    """Разделяет файловый ответ и JSON-ошибки независимо от Accept."""

    renderers: ClassVar[tuple[Renderer, ...]] = (
        JsonRenderer(),
        FileRenderer(content_type=CSV_MIME),
        FallbackHtmlRenderer(),
    )
    responses: ClassVar[tuple[ResponseSpec, ...]] = tuple(
        ResponseSpec(
            ErrorResponse,
            status_code=status,
            limit_to_content_types={'application/json'},
        )
        for status in (
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.NOT_ACCEPTABLE,
        )
    )

    @override
    def to_error(  # noqa: WPS211 — сигнатура метода DMR
        self,
        raw_data: object,
        *,
        status_code: HTTPStatus,
        headers: Mapping[str, str] | None = None,
        cookies: Mapping[str, NewCookie] | None = None,
        renderer: Renderer | None = None,
    ) -> HttpResponse:
        """Сериализует ошибки в JSON при запросе CSV-файла."""
        return super().to_error(
            raw_data,
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            renderer=JsonRenderer(),
        )
