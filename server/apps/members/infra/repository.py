from contextlib import nullcontext
from typing import NoReturn, cast, final

import attrs
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Value
from django.db.models.functions import Concat

try:
    from zeal import zeal_ignore
except ImportError:  # pragma: no cover
    zeal_ignore = nullcontext  # pragma: no cover

from server.apps.members.logic import exceptions
from server.apps.members.logic.queries import MemberFilterQuery
from server.apps.members.logic.value_objects import MemberIn
from server.apps.members.models import Department, Direction, Leader, Member


@final
@attrs.define(slots=True, frozen=True)
class DirectionRepo:
    """Изолированный слой работы с БД для Направлений."""  # noqa: RUF002

    def get_all(self) -> list[Direction]:
        """Получение всех направлений."""
        return list(Direction.objects.all())

    def get_by_id(self, direction_id: int) -> Direction:
        """Получение направления по ID."""
        try:
            return cast(Direction, Direction.objects.get(id=direction_id))
        except Direction.DoesNotExist:
            raise exceptions.ObjectNotFoundError(
                'Направление не найдено.',
            ) from None

    def create(self, name: str) -> Direction:
        """Создает новое направление."""
        try:
            return cast(Direction, Direction.objects.create(name=name))
        except IntegrityError:
            raise exceptions.ObjectAlreadyExistsError(
                'Направление с таким названием уже существует.',  # noqa: RUF001
            ) from None

    def update(self, direction: Direction, name: str) -> Direction:
        """Обновляет направление."""
        direction.name = name
        try:
            direction.save()
        except IntegrityError:
            raise exceptions.ObjectAlreadyExistsError(
                'Направление с таким названием уже существует.',  # noqa: RUF001
            ) from None
        else:
            return direction

    def delete(self, direction: Direction) -> None:
        """Удаляет направление."""
        direction.delete()


@final
@attrs.define(slots=True, frozen=True)
class DepartmentRepo:
    """Изолированный слой работы с БД для Отделов."""  # noqa: RUF002

    def get_all(self) -> list[Department]:
        """Получение всех отделов с подгрузкой направлений."""  # noqa: RUF002
        return list(Department.objects.select_related('direction').all())

    def get_by_id(self, department_id: int) -> Department:
        """Получение отдела по ID."""
        try:
            return cast(
                Department,
                Department.objects.select_related('direction').get(
                    id=department_id,
                ),
            )
        except Department.DoesNotExist:
            raise exceptions.ObjectNotFoundError('Отдел не найден.') from None

    def create(self, name: str, direction_id: int) -> Department:
        """Создает новый отдел."""
        if not Direction.objects.filter(id=direction_id).exists():
            raise exceptions.ObjectAlreadyExistsError(
                'Нарушение целостности данных '
                '(возможно, неверный ID направления).',
            )
        try:
            department = cast(
                Department,
                Department.objects.create(name=name, direction_id=direction_id),
            )
            _ = department.direction
        except IntegrityError as e:
            error_msg = str(e)
            if 'unique_active_department_in_direction' in error_msg:
                raise exceptions.ObjectAlreadyExistsError(
                    'Отдел с таким названием уже '  # noqa: RUF001
                    'существует в этом направлении.',
                ) from None
            raise exceptions.ObjectAlreadyExistsError(
                'Нарушение целостности данных '
                '(возможно, неверный ID направления).',
            ) from None  # pragma: no cover
        else:
            return department

    def update(
        self,
        department: Department,
        name: str,
        direction_id: int,
    ) -> Department:
        """Обновляет отдел."""
        if not Direction.objects.filter(id=direction_id).exists():
            raise exceptions.ObjectAlreadyExistsError(
                'Нарушение целостности данных '
                '(возможно, неверный ID направления).',
            )
        department.name = name
        department.direction_id = direction_id
        try:
            department.save()
            department.refresh_from_db()
        except IntegrityError as e:
            error_msg = str(e)
            if 'unique_active_department_in_direction' in error_msg:
                raise exceptions.ObjectAlreadyExistsError(
                    'Отдел с таким названием уже '  # noqa: RUF001
                    'существует в этом направлении.',
                ) from None
            raise exceptions.ObjectAlreadyExistsError(
                'Нарушение целостности данных '
                '(возможно, неверный ID направления).',
            ) from None  # pragma: no cover
        else:
            return department

    def delete(self, department: Department) -> None:
        """Удаляет отдел."""
        department.delete()


@final
@attrs.define(slots=True, frozen=True)
class LeaderRepo:
    """Изолированный слой работы с БД для Руководителей."""  # noqa: RUF002

    def get_all(self) -> list[Leader]:
        """Получение всех руководителей с подгрузкой связей."""  # noqa: RUF002
        return list(
            Leader.objects.select_related(
                'member',
                'department__direction',
                'direction',
            ).all(),
        )

    def get_by_id(self, leader_id: int) -> Leader:
        """Получение руководителя по ID."""
        try:
            return cast(
                Leader,
                Leader.objects.select_related(
                    'member',
                    'department__direction',
                    'direction',
                ).get(id=leader_id),
            )
        except Leader.DoesNotExist:
            raise exceptions.ObjectNotFoundError(
                'Руководитель не найден.',
            ) from None

    def create(
        self,
        member_id: int,
        position: str,
        department_id: int | None,
        direction_id: int | None,
    ) -> Leader:
        """Создает нового руководителя с атомарной проверкой связей."""  # noqa: RUF002
        try:
            with transaction.atomic():
                leader = cast(
                    Leader,
                    Leader.objects.create(
                        member_id=member_id,
                        position=position,
                        department_id=department_id,
                        direction_id=direction_id,
                    ),
                )
                _ = leader.member
                if leader.department:
                    _ = leader.department.direction
                if leader.direction:
                    _ = leader.direction

                return leader
        except IntegrityError as e:
            self._handle_integrity_error(str(e))
        except ObjectDoesNotExist:
            raise exceptions.ObjectNotFoundError(
                'Указанный активист, отдел или направление не существует.',
            ) from None

    def update(
        self,
        leader: Leader,
        member_id: int,
        position: str,
        department_id: int | None,
        direction_id: int | None,
    ) -> Leader:
        """Обновляет данные руководителя."""
        leader.member_id = member_id
        leader.position = position
        leader.department_id = department_id
        leader.direction_id = direction_id
        try:
            with transaction.atomic():
                leader.save()
                _ = leader.member
                if leader.department:
                    _ = leader.department.direction
                if leader.direction:
                    _ = leader.direction
                leader.refresh_from_db()

                return leader
        except IntegrityError as e:
            self._handle_integrity_error(str(e))
        except ObjectDoesNotExist:
            raise exceptions.ObjectNotFoundError(
                'Указанный активист, отдел или направление не существует.',
            ) from None

    def delete(self, leader: Leader) -> None:
        """Удаляет руководителя."""
        leader.delete()

    def _handle_integrity_error(self, error_msg: str) -> NoReturn:
        """Централизованная обработка ошибок БД для Руководителей."""
        if 'unique_active_position_in_department' in error_msg:
            raise exceptions.ObjectAlreadyExistsError(
                'Такая должность уже занята в этом отделе.',
            ) from None
        if 'unique_active_position_in_direction' in error_msg:
            raise exceptions.ObjectAlreadyExistsError(
                'Такая должность уже занята в этом направлении.',
            ) from None
        raise exceptions.ObjectAlreadyExistsError(
            'Нарушение целостности данных при сохранении руководителя.',
        ) from None


@final
@attrs.define(slots=True, frozen=True)
class MemberRepo:
    """Изолированный слой работы с БД для Активистов."""  # noqa: RUF002

    def get_list(self, query: MemberFilterQuery) -> list[Member]:
        """Получение списка активистов с фильтрацией и пагинацией."""  # noqa: RUF002
        queryset = Member.objects.prefetch_related(
            'departments__direction',
        ).all()

        if query.search:
            full_name_expr = Concat(
                'last_name',
                Value(' '),
                'first_name',
                Value(' '),
                'patronymic',
            )

            queryset = (
                queryset
                .annotate(
                    similarity=TrigramSimilarity(full_name_expr, query.search),
                )
                .filter(similarity__gt=0.3)
                .order_by('-similarity')
            )
        elif query.sort_by:
            allowed_sorts = {
                'join_date',
                '-join_date',
                'birth_date',
                '-birth_date',
                'last_name',
                '-last_name',
                'first_name',
                '-first_name',
            }
            if query.sort_by in allowed_sorts:
                queryset = queryset.order_by(query.sort_by)
            else:
                queryset = queryset.order_by('-join_date')

        if query.group:
            queryset = queryset.filter(group=query.group)

        return list(queryset[query.offset : query.offset + query.limit])

    def get_by_id(self, member_id: int) -> Member:
        """Получение активиста по ID."""
        try:
            return cast(
                Member,
                Member.objects.prefetch_related('departments__direction').get(
                    id=member_id,
                ),
            )
        except Member.DoesNotExist:
            raise exceptions.ObjectNotFoundError(
                'Активист не найден.',
            ) from None

    def get_by_department(self, department_id: int) -> list[Member]:
        """Получение активистов конкретного отдела."""
        return list(
            Member.objects.prefetch_related('departments__direction').filter(
                departments__id=department_id,
            ),
        )

    def get_by_direction(self, direction_id: int) -> list[Member]:
        """Получение активистов конкретного направления."""
        return list(
            Member.objects.prefetch_related('departments__direction').filter(
                departments__direction_id=direction_id,
            ),
        )

    def create(self, data: MemberIn) -> Member:
        """Создает нового активиста."""
        try:
            with transaction.atomic():
                member = cast(
                    Member,
                    Member.objects.create(
                        first_name=data.first_name,
                        last_name=data.last_name,
                        patronymic=data.patronymic or '',
                        telegram=data.telegram,
                        group=data.group or '',
                        birth_date=data.birth_date,
                    ),
                )
                if data.department_ids:
                    member.departments.set(data.department_ids)
        except IntegrityError as e:
            self._handle_integrity_error(str(e))
        else:
            with zeal_ignore():
                return self.get_by_id(member.id)

    def update(self, member: Member, data: MemberIn) -> Member:
        """Обновляет данные активиста."""
        member.first_name = data.first_name
        member.last_name = data.last_name
        member.patronymic = data.patronymic or ''
        member.telegram = data.telegram
        member.group = data.group or ''
        member.birth_date = data.birth_date
        try:
            with transaction.atomic():
                member.save()
                member.departments.set(data.department_ids)
        except IntegrityError as e:
            self._handle_integrity_error(str(e))
        else:
            with zeal_ignore():
                return self.get_by_id(member.id)

    def delete(self, member: Member) -> None:
        """Удаляет активиста."""
        member.delete()

    def _handle_integrity_error(self, error_msg: str) -> NoReturn:
        """Централизованная обработка ошибок БД для Активистов."""
        if 'unique_active_fio' in error_msg.lower():
            raise exceptions.ObjectAlreadyExistsError(
                'Активист с таким ФИО уже существует.',  # noqa: RUF001
            ) from None
        if 'unique_active_telegram' in error_msg.lower():
            raise exceptions.ObjectAlreadyExistsError(
                'Пользователь с таким Telegram уже существует.',  # noqa: RUF001
            ) from None
        raise exceptions.ObjectAlreadyExistsError(
            'Нарушение целостности данных при сохранении '
            '(возможно, указан несуществующий отдел).',
        ) from None
