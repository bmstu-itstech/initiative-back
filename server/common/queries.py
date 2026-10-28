from typing import Annotated

import msgspec

MAX_OFFSET = 2147483647


class PaginationQuery(msgspec.Struct):
    """Параметры пагинации."""

    limit: Annotated[int, msgspec.Meta(ge=1, le=1000)] = 20
    offset: Annotated[int, msgspec.Meta(ge=0, le=MAX_OFFSET)] = 0
