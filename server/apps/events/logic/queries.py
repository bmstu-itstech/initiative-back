from typing import Annotated, Literal

import msgspec

from server.common.queries import PaginationQuery


class EventListQuery(PaginationQuery):
    """Пагинация и сортировка мероприятий по началу."""

    sort_by: Literal['starts_at', '-starts_at'] = '-starts_at'


class EventFilterQuery(EventListQuery):
    """Параметры списка мероприятий с нечётким поиском."""  # noqa: RUF002

    search: Annotated[str, msgspec.Meta(pattern=r'^[^\x00]*$')] | None = None
