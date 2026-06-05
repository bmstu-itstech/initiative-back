from http import HTTPStatus
from typing import final, override

from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse
from dmr import Body, Controller
from dmr.endpoint import Endpoint, validate
from dmr.errors import ErrorType
from dmr.metadata import ResponseSpec
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.security import AuthenticatedHttpRequest
from dmr.security.jwt.auth import JWTSyncAuth

from server.apps.auth.logic.permissions import require_role
from server.apps.auth.logic.roles import Role
from server.apps.members.logic import exceptions
from server.apps.members.logic.usecases.departments import (
    CreateDepartment,
    DeleteDepartment,
    GetDepartment,
    GetDepartmentList,
    UpdateDepartment,
)
from server.apps.members.logic.value_objects import (
    DepartmentIn,
    DepartmentOut,
    ErrorResponse,
)
from server.common.di import HasContainer


@final
class DepartmentsController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для списка отделов и создания новых."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(list[DepartmentOut], status_code=HTTPStatus.OK),
        tags=['Отделы'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Получение списка всех отделов."""
        result = self.resolve(GetDepartmentList)()
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(DepartmentOut, status_code=HTTPStatus.CREATED),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        tags=['Отделы'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def post(self, parsed_body: Body[DepartmentIn]) -> HttpResponse:
        """Создание нового отдела."""
        result = self.resolve(CreateDepartment)(parsed_body)
        return self.to_response(result, status_code=HTTPStatus.CREATED)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        """Перехват бизнес-ошибок для Schemathesis."""
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
class DepartmentDetailController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Управление конкретным отделом."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(DepartmentOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Отделы'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Получение данных выбранного отдела."""
        result = self.resolve(GetDepartment)(
            self.kwargs['department_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(DepartmentOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Отделы'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def put(self, parsed_body: Body[DepartmentIn]) -> HttpResponse:
        """Полное обновление данных выбранного отдела."""
        result = self.resolve(UpdateDepartment)(
            self.kwargs['department_id'],
            parsed_body,
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(dict, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Отделы'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def delete(self) -> HttpResponse:
        """Мягкое удаление выбранного отдела."""
        result = self.resolve(DeleteDepartment)(
            self.kwargs['department_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        """Перехват бизнес-ошибок для Schemathesis."""
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
