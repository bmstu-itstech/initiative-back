from http import HTTPStatus
from typing import final, override

from django.db import transaction
from django.http import HttpResponse
from dmr import Body, Controller, Query
from dmr.endpoint import Endpoint, validate
from dmr.errors import ErrorType
from dmr.metadata import ResponseSpec
from dmr.plugins.msgspec import MsgspecSerializer

from server.apps.members.logic import exceptions
from server.apps.members.logic.queries import MemberFilterQuery
from server.apps.members.logic.usecases.members import (
    CreateMember,
    DeleteMember,
    GetMember,
    GetMemberList,
    GetMembersByDepartment,
    GetMembersByDirection,
    UpdateMember,
)
from server.apps.members.logic.value_objects import (
    ErrorResponse,
    MemberIn,
    MemberOut,
)
from server.common.di import HasContainer


@final
class MembersController(HasContainer, Controller[MsgspecSerializer]):
    """Контроллер для списка активистов и создания новых."""

    @validate(
        ResponseSpec(list[MemberOut], status_code=HTTPStatus.OK),
        tags=['Активисты'],
    )
    def get(self, parsed_query: Query[MemberFilterQuery]) -> HttpResponse:
        """Получение списка активистов с фильтрацией и пагинацией."""  # noqa: RUF002
        result = self.resolve(GetMemberList)(parsed_query)
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.CREATED),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        tags=['Активисты'],
    )
    def post(self, parsed_body: Body[MemberIn]) -> HttpResponse:
        """Создание нового активиста."""
        result = self.resolve(CreateMember)(parsed_body)
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
class MemberDetailController(HasContainer, Controller[MsgspecSerializer]):
    """Управление конкретным активистом."""

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    def get(self) -> HttpResponse:
        """Получение детальной информации об активисте."""  # noqa: RUF002
        result = self.resolve(GetMember)(self.kwargs['member_id'])
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    def put(self, parsed_body: Body[MemberIn]) -> HttpResponse:
        """Полное обновление данных активиста."""
        result = self.resolve(UpdateMember)(
            self.kwargs['member_id'],
            parsed_body,
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(dict, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    def delete(self) -> HttpResponse:
        """Мягкое удаление активиста."""
        result = self.resolve(DeleteMember)(self.kwargs['member_id'])
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


@final
class DepartmentMembersController(HasContainer, Controller[MsgspecSerializer]):
    """Контроллер для вывода активистов отдела."""

    @validate(
        ResponseSpec(list[MemberOut], status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    def get(self) -> HttpResponse:
        """Вывод всех активистов конкретного отдела."""
        result = self.resolve(GetMembersByDepartment)(
            self.kwargs['department_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)


@final
class DirectionMembersController(HasContainer, Controller[MsgspecSerializer]):
    """Контроллер для вывода активистов направления."""

    @validate(
        ResponseSpec(list[MemberOut], status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    def get(self) -> HttpResponse:
        """Вывод всех активистов конкретного направления."""
        result = self.resolve(GetMembersByDirection)(
            self.kwargs['direction_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)
