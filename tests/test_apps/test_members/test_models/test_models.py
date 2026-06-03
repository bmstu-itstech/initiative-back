from typing import final

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import django

from server.apps.members.models import Department, Direction, Leader, Member


@final
class TestDirection(django.TestCase):
    """Тест свойств модели Direction."""

    @given(django.from_model(Direction))
    def test_model_properties(self, instance: Direction) -> None:
        """Тест свойств модели Direction."""
        instance.save()
        assert instance.id > 0
        assert str(instance) == instance.name


@final
class TestDepartment(django.TestCase):
    """Тест свойств модели Department."""

    @given(
        django.from_model(Department, direction=django.from_model(Direction)),
    )
    def test_model_properties(self, instance: Department) -> None:
        """Тест свойств модели Department."""
        instance.direction.save()
        instance.save()
        assert instance.id > 0
        assert instance.name in str(instance)
        assert instance.direction.name in str(instance)


@final
class TestMember(django.TestCase):
    """Тест свойств модели Member."""

    @given(django.from_model(Member))
    def test_model_properties(self, instance: Member) -> None:
        """Тест свойств модели Member."""
        instance.save()
        assert instance.id > 0
        assert instance.last_name in str(instance)
        assert instance.first_name in str(instance)


@final
class TestLeader(django.TestCase):
    """Тест свойств модели Leader."""

    @given(
        django.from_model(
            Leader,
            member=django.from_model(Member),
            department=django.from_model(
                Department,
                direction=django.from_model(Direction),
            ),
            direction=st.just(None),
        ),
    )
    def test_model_properties(self, instance: Leader) -> None:
        """Тест свойств модели Leader."""
        assert instance.department is not None

        instance.member.save()
        instance.department.direction.save()
        instance.department.save()
        instance.save()

        assert instance.id > 0
        assert instance.position in str(instance)
        assert str(instance.member) in str(instance)


@pytest.mark.django_db
def test_soft_delete_restore(member: Member) -> None:
    """Тест восстановления мягко удаленной записи."""
    member.delete()
    assert member.is_deleted is True
    assert member.deleted_at is not None

    member.restore()
    assert member.is_deleted is False
    assert member.deleted_at is None  # type: ignore[unreachable]
