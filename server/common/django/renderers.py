import json
from collections.abc import Callable
from typing import override

from dmr.parsers import JsonParser, Parser
from dmr.renderers import Renderer


class FallbackHtmlRenderer(Renderer):
    """
    Архитектурный фикс (Content Negotiation) для браузерных запросов.

    Перехватывает заголовок Accept: text/html и отдает ошибки в
    виде JSON, предотвращая падение DMR с KeyError('text/html').
    """  # noqa: RUF002

    content_type = 'text/html'

    @override
    def render(
        self,
        to_serialize: object,
        serializer_hook: Callable[[object], object],
    ) -> bytes:
        """Сериализует ответ в JSON для браузера."""
        return json.dumps(to_serialize, default=serializer_hook).encode('utf-8')

    @property
    @override
    def validation_parser(self) -> Parser:
        """Возвращает парсер для валидации сгенерированного ответа."""
        return JsonParser()
