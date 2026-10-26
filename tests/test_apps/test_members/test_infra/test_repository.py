from collections.abc import Callable
from contextlib import AbstractContextManager
from unittest.mock import patch

import pytest
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext

from server.apps.members.infra.mappers import (
    DepartmentMapper,
    DirectionMapper,
    LeaderMapper,
    MemberListMapper,
    MemberMapper,
    StructureDepartmentMapper,
    StructureDirectionMapper,
    StructureLeaderMapper,
)
from server.apps.members.infra.repository import (
    DepartmentRepo,
    DirectionRepo,
    LeaderRepo,
    MemberRepo,
)
from server.apps.members.logic import exceptions
from server.apps.members.logic.queries import MemberFilterQuery
from server.apps.members.logic.value_objects import MemberIn
from server.apps.members.models import Department, Direction, Leader, Member


@pytest.mark.django_db
class TestDirectionRepo:
    """Тесты для DirectionRepo."""

    def test_create_and_get(self) -> None:
        """Тест создания и получения направления."""
        repo = DirectionRepo()
        direction = repo.create(name='Новое направление')

        assert direction.id is not None
        assert repo.get_by_id(direction.id).name == 'Новое направление'
        assert len(repo.get_all()) == 1

    def test_unique_name_constraint(self, direction: Direction) -> None:
        """Тест уникальности названия направления."""
        repo = DirectionRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError):
            repo.create(name=direction.name)

    def test_not_found(self) -> None:
        """Тест получения несуществующего направления."""
        repo = DirectionRepo()
        with pytest.raises(exceptions.ObjectNotFoundError):
            repo.get_by_id(9999)

    def test_get_structure(
        self,
        direction: Direction,
        department: Department,
        leader: Leader,
        member: Member,
        django_assert_num_queries: Callable[
            [int],
            AbstractContextManager[None],
        ],
    ) -> None:
        """Проверяет загрузку структуры и преобразование без лишних запросов."""
        department.members.add(member)  # type: ignore[attr-defined]
        second_direction = Direction.objects.create(name='Second direction')
        second_department = Department.objects.create(
            name='Second department',
            direction=second_direction,
        )
        second_department.members.add(member)
        direction_leader = Leader.objects.create(
            member=member,
            position='Direction head',
            direction=direction,
        )
        member_mapper = MemberListMapper()
        leader_mapper = StructureLeaderMapper(member_mapper)
        direction_mapper = StructureDirectionMapper(
            leader_mapper,
            StructureDepartmentMapper(leader_mapper, member_mapper),
        )
        with django_assert_num_queries(4):
            directions = DirectionRepo().get_structure()
        with django_assert_num_queries(0):
            structure = [direction_mapper(item) for item in directions]
        assert len(structure) == 2
        first = next(item for item in structure if item.id == direction.pk)
        second = next(
            item for item in structure if item.id == second_direction.pk
        )
        assert first.leaders[0].id == direction_leader.pk
        assert first.departments[0].id == department.pk
        assert first.departments[0].leaders[0].id == leader.pk
        assert first.departments[0].members[0].id == member.pk
        assert second.leaders == []
        assert second.departments[0].leaders == []
        assert second.departments[0].members[0].id == member.pk

        member.delete()
        second_direction.delete()
        direction_leader.delete()
        with django_assert_num_queries(4):
            directions = DirectionRepo().get_structure()
        with django_assert_num_queries(0):
            result = [direction_mapper(item) for item in directions]
        assert len(result) == 1
        assert result[0].leaders == []
        assert len(result[0].departments) == 1
        assert result[0].departments[0].members == []
        assert result[0].departments[0].leaders[0].member.id == member.pk

        direction.delete()
        with django_assert_num_queries(1):
            assert DirectionRepo().get_structure() == []


@pytest.mark.django_db
class TestDepartmentRepo:
    """Тесты для DepartmentRepo."""

    def test_create_and_get(self, direction: Direction) -> None:
        """Тест создания и получения отдела."""
        repo = DepartmentRepo()
        department = repo.create(name='Новый отдел', direction_id=direction.id)

        assert department.id is not None
        assert repo.get_by_id(department.id).name == 'Новый отдел'
        assert department.direction.name == direction.name

    def test_unique_in_direction_constraint(
        self,
        department: Department,
    ) -> None:
        """Тест уникальности названия отдела внутри одного направления."""
        repo = DepartmentRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError):
            repo.create(
                name=department.name,
                direction_id=department.direction_id,
            )

    def test_same_name_different_direction(
        self,
        department: Department,
        direction: Direction,
    ) -> None:
        """Тест создания отдела с одним названием и разными направлениями."""  # noqa: RUF002
        repo = DepartmentRepo()
        new_direction = DirectionRepo().create(name='Другое направление')

        new_dep = repo.create(
            name=department.name,
            direction_id=new_direction.id,
        )
        assert new_dep.id is not None


@pytest.mark.django_db
class TestLeaderRepo:
    """Тесты для LeaderRepo."""

    @pytest.mark.parametrize('count', [1, 5, 20])
    def test_get_all_without_mapping_queries(
        self,
        count: int,
        member: Member,
        department: Department,
        django_assert_num_queries: Callable[
            [int],
            AbstractContextManager[None],
        ],
    ) -> None:
        """Загружает все вложенные связи за постоянное число запросов."""
        second_direction = Direction.objects.create(name='Другое направление')
        second_department = Department.objects.create(
            name='Другой отдел',
            direction=second_direction,
        )
        member.departments.add(department, second_department)
        for index in range(count):
            Leader.objects.create(
                member=member,
                position=f'Должность {index}',
                department=department if index % 4 in {0, 2} else None,
                direction=second_direction if index % 4 in {1, 2} else None,
            )
        direction_mapper = DirectionMapper()
        department_mapper = DepartmentMapper(direction_mapper)
        mapper = LeaderMapper(
            MemberMapper(department_mapper),
            department_mapper,
            direction_mapper,
        )
        with CaptureQueriesContext(connection) as queries:
            leaders = LeaderRepo().get_all()
        with django_assert_num_queries(0):
            result = [mapper(item) for item in leaders]
        assert len(queries) == 2
        assert len(result) == count
        for item in result:
            assert item.member.id == member.pk
            assert {dep.id for dep in item.member.departments} == {
                department.pk,
                second_department.pk,
            }
            assert {dep.direction.id for dep in item.member.departments} == {
                department.direction_id,
                second_direction.pk,
            }
            original = next(lead for lead in leaders if lead.pk == item.id)
            assert (item.department.id if item.department else None) == (
                original.department_id
            )
            assert (item.direction.id if item.direction else None) == (
                original.direction_id
            )

    def test_get_all_empty(
        self,
        django_assert_num_queries: Callable[
            [int],
            AbstractContextManager[None],
        ],
    ) -> None:
        """Загружает пустой список без запросов вложенных связей."""
        with django_assert_num_queries(1):
            assert LeaderRepo().get_all() == []

    def test_create_leader_department(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Тест создания руководителя с указанием только отдела."""  # noqa: RUF002
        repo = LeaderRepo()
        leader = repo.create(
            member_id=member.id,
            position='Глава',
            department_id=department.id,
            direction_id=None,
        )
        assert leader.id is not None
        assert leader.department_id == department.id
        assert leader.direction_id is None

    def test_create_leader_both_units(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Тест успешного создания, если указаны и отдел, и направление."""
        repo = LeaderRepo()
        leader = repo.create(
            member_id=member.id,
            position='Глава всего',
            department_id=department.id,
            direction_id=department.direction_id,
        )
        assert leader.id is not None
        assert leader.department_id == department.id
        assert leader.direction_id == department.direction_id

    def test_create_leader_no_units(self, member: Member) -> None:
        """Тест успешного создания, если не указан ни отдел, ни направление."""
        repo = LeaderRepo()
        leader = repo.create(
            member_id=member.id,
            position='Независимый лидер',
            department_id=None,
            direction_id=None,
        )
        assert leader.id is not None
        assert leader.department_id is None
        assert leader.direction_id is None

    def test_unique_position_in_department(self, leader: Leader) -> None:
        """Тест если должность уже занята в отделе."""
        repo = LeaderRepo()
        new_member = Member.objects.create(
            telegram='new_tg',
            first_name='A',
            last_name='B',
        )

        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info:
            repo.create(
                member_id=new_member.id,
                position=leader.position,
                department_id=leader.department_id,
                direction_id=None,
            )
        assert 'занята в этом отделе' in str(exc_info.value)

    def test_generic_integrity_error(self) -> None:
        """Тест обобщенного целостности данных."""
        repo = LeaderRepo()
        with pytest.raises(exceptions.ObjectNotFoundError) as exc_info:
            repo.create(
                member_id=9999999,
                position='Глава',
                department_id=None,
                direction_id=None,
            )
        assert ' активист, отдел или направление не существует' in str(
            exc_info.value,
        )

    def test_unique_position_in_direction(
        self,
        leader_direction: Leader,
    ) -> None:
        """Тест если должность уже занята в направлении."""
        repo = LeaderRepo()
        new_member = Member.objects.create(
            telegram='new_tg_dir',
            first_name='C',
            last_name='D',
        )

        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info:
            repo.create(
                member_id=new_member.id,
                position=leader_direction.position,
                department_id=None,
                direction_id=leader_direction.direction_id,
            )
        assert 'занята в этом направлении' in str(exc_info.value)

    def test_update_success_change_units(
        self,
        leader: Leader,
        direction: Direction,
    ) -> None:
        """Успешное обновление руководителя (смена отдела на направление)."""
        repo = LeaderRepo()
        updated = repo.update(
            leader=leader,
            member_id=leader.member_id,
            position='Новая позиция',
            department_id=None,
            direction_id=direction.id,
        )
        assert updated.position == 'Новая позиция'
        assert updated.department_id is None
        assert updated.direction_id == direction.id

    def test_update_generic_integrity_error(self, leader: Leader) -> None:
        """Тест перехвата ObjectNotFoundError при обновлении с фейковым ID."""  # noqa: RUF002
        repo = LeaderRepo()
        with pytest.raises(exceptions.ObjectNotFoundError) as exc_info:
            repo.update(
                leader=leader,
                member_id=9999999,
                position='Глава',
                department_id=None,
                direction_id=None,
            )
        assert 'не существует' in str(exc_info.value)


@pytest.mark.django_db
class TestMemberRepo:
    """Тесты для MemberRepo."""

    def test_create_and_get(
        self,
        department: Department,
        member_in: MemberIn,
    ) -> None:
        """Тест создания активиста."""
        repo = MemberRepo()

        member_in.department_ids = [department.id]

        member = repo.create(data=member_in)
        assert member.id is not None
        assert member.telegram == member_in.telegram

        assert member.departments.count() == 1
        first_dept = member.departments.first()
        assert first_dept is not None
        assert first_dept.id == department.id

    def test_unique_telegram(self, member: Member, member_in: MemberIn) -> None:
        """Тест уникальности поля telegram при создании активиста."""
        repo = MemberRepo()

        member_in.telegram = member.telegram

        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info:
            repo.create(data=member_in)
        assert 'Telegram уже существует' in str(exc_info.value)

    def test_department_update(
        self,
        department: Department,
        direction: Direction,
    ) -> None:
        """Тест обновления отдела."""
        repo = DepartmentRepo()
        updated = repo.update(
            department,
            name='Новое имя',
            direction_id=direction.id,
        )
        assert updated.name == 'Новое имя'

    def test_leader_delete(self, leader: Leader) -> None:
        """Тест мягкого удаления руководителя."""
        repo = LeaderRepo()
        repo.delete(leader)

        leader.refresh_from_db()
        assert leader.is_deleted is True

    def test_direction_update_integrity(self, direction: Direction) -> None:
        """Попытка обновить направление на уже существующее имя."""
        repo = DirectionRepo()
        Direction.objects.create(name='Какое-то Имя')
        with pytest.raises(exceptions.ObjectAlreadyExistsError):
            repo.update(direction, name='Какое-то Имя')

    def test_department_create_invalid_direction(self) -> None:
        """Создание отдела с несуществующим ID направления."""  # noqa: RUF002
        repo = DepartmentRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc:
            repo.create(name='Отдел', direction_id=999999)
        assert 'неверный ID направления' in str(exc.value)

    def test_department_update_invalid_direction(
        self,
        department: Department,
    ) -> None:
        """Обновление отдела с несуществующим ID направления."""  # noqa: RUF002
        repo = DepartmentRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc:
            repo.update(department, name='Отдел', direction_id=999999)
        assert 'неверный ID направления' in str(exc.value)

    def test_leader_create_with_direction(
        self,
        member: Member,
        direction: Direction,
    ) -> None:
        """Создание руководителя, привязанного напрямую к направлению."""
        repo = LeaderRepo()
        leader = repo.create(
            member_id=member.id,
            position='Главный',
            department_id=None,
            direction_id=direction.id,
        )
        assert leader.direction is not None
        assert leader.direction.id == direction.id

    def test_leader_update_integrity(self, leader: Leader) -> None:
        """Конфликт при обновлении руководителя (должность уже занята)."""
        repo = LeaderRepo()
        second_member = Member.objects.create(
            first_name='2',
            last_name='2',
            telegram='tg2',
        )
        second_leader = repo.create(
            member_id=second_member.id,
            position='Другая должность',
            department_id=leader.department_id,
            direction_id=None,
        )
        with pytest.raises(exceptions.ObjectAlreadyExistsError):
            repo.update(
                second_leader,
                member_id=second_member.id,
                position=leader.position,
                department_id=leader.department_id,
                direction_id=None,
            )

    def test_member_get_list_search_trigram(self, member: Member) -> None:
        """Поиск через pg_trgm (сработает блок query.search)."""
        repo = MemberRepo()
        query = MemberFilterQuery(search=member.last_name)
        res = repo.get_list(query)
        assert len(res) > 0

    def test_member_get_list_invalid_sort(self, member: Member) -> None:
        """Сортировка по неизвестному полю."""
        repo = MemberRepo()
        query = MemberFilterQuery(sort_by='invalid_sort_field')
        res = repo.get_list(query)
        assert len(res) > 0

    def test_member_get_list_group(self, member: Member) -> None:
        """Фильтрация по номеру группы (сработает if query.group)."""
        member.group = 'ИУ5-11Б'  # noqa: RUF001
        member.save()
        repo = MemberRepo()
        query = MemberFilterQuery(group='ИУ5-11Б')  # noqa: RUF001
        res = repo.get_list(query)
        assert len(res) > 0

    def test_member_get_by_relations(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Проверка методов get_by_department и get_by_direction."""
        member.departments.add(department)
        repo = MemberRepo()
        assert len(repo.get_by_department(department.id)) == 1
        assert len(repo.get_by_direction(department.direction_id)) == 1

    def test_member_create_no_departments(self, member_in: MemberIn) -> None:
        """Создание активиста с пустым списком отделов."""  # noqa: RUF002
        repo = MemberRepo()
        member_in.department_ids = []
        res = repo.create(member_in)
        assert res.departments.count() == 0

    def test_member_update_success(
        self,
        member: Member,
        member_in: MemberIn,
        department: Department,
    ) -> None:
        """Успешное полное обновление активиста."""
        repo = MemberRepo()
        member_in.department_ids = [department.id]
        res = repo.update(member, member_in)
        assert res.first_name == member_in.first_name
        assert res.departments.count() == 1

    def test_member_update_integrity(
        self,
        member: Member,
        member_in: MemberIn,
    ) -> None:
        """Конфликт уникальности при обновлении активиста."""
        repo = MemberRepo()
        second_member = Member.objects.create(
            first_name='2',
            last_name='2',
            telegram='telegram2',
        )
        member_in.telegram = second_member.telegram
        with pytest.raises(exceptions.ObjectAlreadyExistsError):
            repo.update(member, member_in)

    def test_member_get_list_no_sort_and_no_search(
        self,
        member: Member,
    ) -> None:
        """Покрытие ветки, где search и sort_by пустые."""
        repo = MemberRepo()
        query = MemberFilterQuery(
            search=None,
            sort_by='',
            group=None,
            offset=0,
            limit=10,
        )
        res = repo.get_list(query)
        assert len(res) > 0

    def test_member_update_generic_integrity_error(
        self,
        member: Member,
        member_in: MemberIn,
    ) -> None:
        """Эмуляция неизвестной ошибки БД для проверки базового обработчика."""
        repo = MemberRepo()

        with (
            patch(
                'server.apps.members.models.Member.save',
                side_effect=IntegrityError('Random DB error'),
            ),
            pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info,
        ):
            repo.update(member, member_in)

        assert 'возможно, указан несуществующий отдел' in str(exc_info.value)

    def test_member_create_no_join_date(
        self,
        member_in: MemberIn,
    ) -> None:
        """Создание активиста без даты вступления."""
        repo = MemberRepo()
        member_in.join_date = None
        member_in.department_ids = []

        res = repo.create(member_in)
        assert res.id is not None
