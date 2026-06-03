import pytest

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

    def test_create_leader_department(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Тест создания руководителя с указанием отдела."""  # noqa: RUF002
        repo = LeaderRepo()
        leader = repo.create(
            member_id=member.id,
            position='Глава',
            department_id=department.id,
            direction_id=None,
        )
        assert leader.id is not None
        assert leader.department_id == department.id

    def test_check_constraint_both_units(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Тест если указаны и отдел, и направление."""
        repo = LeaderRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info:
            repo.create(
                member_id=member.id,
                position='Глава',
                department_id=department.id,
                direction_id=department.direction_id,
            )
        assert 'либо отделу, либо направлению' in str(exc_info.value)

    def test_check_constraint_no_units(self, member: Member) -> None:
        """Тест если не указан ни отдел, ни направление."""
        repo = LeaderRepo()
        with pytest.raises(exceptions.ObjectAlreadyExistsError) as exc_info:
            repo.create(
                member_id=member.id,
                position='Глава',
                department_id=None,
                direction_id=None,
            )
        assert 'либо отделу, либо направлению' in str(exc_info.value)

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
