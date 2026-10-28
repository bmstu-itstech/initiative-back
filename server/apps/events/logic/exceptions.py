class ObjectNotFoundError(Exception):
    """Исключение: Объект не найден."""


class ObjectAlreadyExistsError(Exception):
    """Исключение: Нарушение уникальности объекта."""


class EventValidationError(Exception):
    """Некорректные данные мероприятия или его оргкомитета."""  # noqa: RUF002
