from typing import Annotated

import msgspec


class PaginationQuery(msgspec.Struct):
    """Параметры пагинации."""

    limit: Annotated[int, msgspec.Meta(ge=1, le=100)] = 20
    offset: Annotated[int, msgspec.Meta(ge=0, le=2147483647)] = 0


class MemberFilterQuery(PaginationQuery):
    """Схема фильтрации для списка активистов."""

    search: str | None = None
    sort_by: str | None = '-join_date'
    group: str | None = None
