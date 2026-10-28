import msgspec


class ErrorDetail(msgspec.Struct):
    """Детальная информация об ошибке."""  # noqa: RUF002

    msg: str
    type: str


class ErrorResponse(msgspec.Struct):
    """Стандартная схема ответа с ошибкой."""  # noqa: RUF002

    detail: list[ErrorDetail]


class SuccessResponse(msgspec.Struct):
    """Стандартная схема успешного ответа без данных."""

    status: str
    message: str
