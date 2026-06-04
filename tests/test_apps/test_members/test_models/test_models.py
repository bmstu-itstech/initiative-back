import pytest

from server.apps.members.models import Department, Direction, Leader, Member


@pytest.mark.django_db
class TestModelProperties:
    """Тестирование строковых свойств (__str__) моделей БД."""

    def test_direction_str(self, direction: Direction) -> None:
        """Тест свойств модели Direction."""
        assert direction.id is not None
        assert str(direction) == direction.name

    def test_department_str(self, department: Department) -> None:
        """Тест свойств модели Department."""
        assert department.id is not None
        assert department.name in str(department)
        assert department.direction.name in str(department)

    def test_member_str(self, member: Member) -> None:
        """Тест свойств модели Member (без отчества)."""
        member.patronymic = ''
        member.save()

        assert member.id is not None
        assert member.last_name in str(member)
        assert member.first_name in str(member)
        assert str(member) == f'{member.last_name} {member.first_name}'

    def test_member_str_with_patronymic(self, member: Member) -> None:
        """Тест свойств модели Member (с отчеством)."""  # noqa: RUF002
        member.patronymic = 'Иванович'
        member.save()

        assert member.id is not None
        assert member.last_name in str(member)
        assert member.first_name in str(member)
        assert 'Иванович' in str(member)
        assert str(member) == f'{member.last_name} {member.first_name} Иванович'

    def test_leader_str_department(self, leader: Leader) -> None:
        """Тест свойств модели Leader (с привязкой только к отделу)."""  # noqa: RUF002
        assert leader.id is not None
        assert leader.department is not None
        assert leader.position in str(leader)
        assert str(leader.member) in str(leader)
        assert leader.department.name in str(leader)

    def test_leader_str_direction(self, leader_direction: Leader) -> None:
        """Тест свойств модели Leader (с привязкой только к направлению)."""  # noqa: RUF002
        assert leader_direction.id is not None
        assert leader_direction.direction is not None
        assert leader_direction.position in str(leader_direction)
        assert str(leader_direction.member) in str(leader_direction)
        assert leader_direction.direction.name in str(leader_direction)

    def test_leader_str_both_units(
        self,
        leader: Leader,
        direction: Direction,
    ) -> None:
        """Тест свойств модели Leader при привязке к отделу и направлению."""
        leader.direction = direction
        leader.save()

        assert leader.id is not None
        assert leader.department is not None
        assert leader.direction is not None
        assert leader.position in str(leader)
        assert leader.department.name in str(leader)

    def test_leader_str_neither_unit(self, leader: Leader) -> None:
        """Тест свойств модели Leader без привязки к подразделениям."""
        leader.department = None
        leader.direction = None
        leader.save()

        assert leader.id is not None
        assert 'Без подразделения' in str(leader)
        assert leader.position in str(leader)


@pytest.mark.django_db
def test_soft_delete_restore(member: Member) -> None:
    """Тест восстановления мягко удаленной записи."""
    member_id = member.id

    member.delete()
    deleted_member = Member.all_objects.get(id=member_id)
    assert deleted_member.deleted_at is not None

    deleted_member.restore()
    restored_member = Member.objects.get(id=member_id)
    assert restored_member.deleted_at is None
