from http import HTTPStatus
from typing import final, override

from django.db import transaction
from django.http import HttpResponse
from dmr import Body, Controller
from dmr.endpoint import Endpoint, validate
from dmr.errors import ErrorType
from dmr.metadata import ResponseSpec
from dmr.plugins.msgspec import MsgspecSerializer

from server.apps.members.logic import exceptions
from server.apps.members.logic.usecases.directions import (
    CreateDirection,
    DeleteDirection,
    GetDirection,
    GetDirectionList,
    UpdateDirection,
)
from server.apps.members.logic.value_objects import (
    DirectionIn,
    DirectionOut,
    ErrorResponse,
)
from server.common.di import HasContainer


@final
class DirectionsController(HasContainer, Controller[MsgspecSerializer]):
    """Контроллер для списка направлений и создания новых."""

    @validate(
        ResponseSpec(list[DirectionOut], status_code=HTTPStatus.OK),
        tags=['Направления'],
    )
    def get(self) -> HttpResponse:
        """Получение списка направлений."""
        return self.to_response(
            self.resolve(GetDirectionList)(),
            status_code=HTTPStatus.OK,
        )

    @validate(
        ResponseSpec(DirectionOut, status_code=HTTPStatus.CREATED),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        tags=['Направления'],
    )
    def post(self, parsed_body: Body[DirectionIn]) -> HttpResponse:
        """Cоздание списка направлений."""  # noqa: RUF002
        result = self.resolve(CreateDirection)(parsed_body)
        return self.to_response(result, status_code=HTTPStatus.CREATED)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, exceptions.ObjectAlreadyExistsError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(
                    str(exc),
                    error_type='database_integrity_error',
                ),
                status_code=HTTPStatus.CONFLICT,
            )
        return super().handle_error(
            endpoint,
            controller,
            exc,
        )  # pragma: no cover


@final
class DirectionDetailController(HasContainer, Controller[MsgspecSerializer]):
    """Управление конкретным направлением."""

    @validate(
        ResponseSpec(DirectionOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Направления'],
    )
    def get(self) -> HttpResponse:
        """Получение данных выбранного направления."""
        result = self.resolve(GetDirection)(
            self.kwargs['direction_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(DirectionOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Направления'],
    )
    def put(self, parsed_body: Body[DirectionIn]) -> HttpResponse:
        """Полное обновление данных выбранного направления."""
        result = self.resolve(UpdateDirection)(
            self.kwargs['direction_id'],
            parsed_body,
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(dict, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Направления'],
    )
    def delete(self) -> HttpResponse:
        """Мягкое удаление выбранного направления."""
        result = self.resolve(DeleteDirection)(
            self.kwargs['direction_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, exceptions.ObjectNotFoundError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(str(exc), error_type=ErrorType.not_found),
                status_code=HTTPStatus.NOT_FOUND,
            )
        if isinstance(exc, exceptions.ObjectAlreadyExistsError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(
                    str(exc),
                    error_type='database_integrity_error',
                ),
                status_code=HTTPStatus.CONFLICT,
            )
        return super().handle_error(
            endpoint,
            controller,
            exc,
        )  # pragma: no cover
