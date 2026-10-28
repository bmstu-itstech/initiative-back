from server.common.queries import PaginationQuery


class MemberFilterQuery(PaginationQuery):
    """Схема фильтрации для списка активистов."""

    search: str | None = None
    sort_by: str | None = '-join_date'
    group: str | None = None
