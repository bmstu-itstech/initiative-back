import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory

from server.apps.members.admin import (
    LeaderAdmin,
    MemberAdmin,
)
from server.apps.members.models import Department, Leader, Member


@pytest.mark.django_db
class TestAdminNPlusOneOptimization:
    """Проверка кастомных методов оптимизации N+1 в админке."""

    def test_member_admin_get_departments(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Проверка метода get_departments."""
        member.departments.add(department)
        member_admin = MemberAdmin(Member, AdminSite())

        result = member_admin.get_departments(member)
        assert department.name in result

    def test_leader_admin_get_unit_department(self, leader: Leader) -> None:
        """Проверка метода get_unit для руководителя отдела."""
        leader_admin = LeaderAdmin(Leader, AdminSite())

        result = leader_admin.get_unit(leader)
        assert 'Отдел:' in result
        assert leader.department is not None
        assert leader.department.name in result

    def test_leader_admin_get_unit_direction(
        self,
        leader_direction: Leader,
    ) -> None:
        """Проверка метода get_unit для руководителя направления."""
        leader_admin = LeaderAdmin(Leader, AdminSite())

        result = leader_admin.get_unit(leader_direction)
        assert 'Направление:' in result
        assert leader_direction.direction is not None
        assert leader_direction.direction.name in result

    def test_leader_admin_get_unit_none(self, leader: Leader) -> None:
        """Проверка метода get_unit, когда подразделение не указано."""
        leader_admin = LeaderAdmin(Leader, AdminSite())

        leader.department = None
        leader.direction = None

        assert leader_admin.get_unit(leader) == '-'

    def test_formfield_optimizations(self, rf: RequestFactory) -> None:
        """Проверка подмены queryset в формах (formfield_for_X)."""
        request = rf.get('/')

        member_admin = MemberAdmin(Member, AdminSite())
        leader_admin = LeaderAdmin(Leader, AdminSite())

        m2m_field = Member._meta.get_field('departments')  # noqa: SLF001
        m2m_formfield = member_admin.formfield_for_manytomany(
            m2m_field,
            request,
        )
        assert m2m_formfield is not None
        assert m2m_formfield.queryset is not None
        assert 'JOIN' in str(m2m_formfield.queryset.query)

        m2m_groups_field = User._meta.get_field('groups')  # noqa: SLF001
        m2m_false_formfield = member_admin.formfield_for_manytomany(
            m2m_groups_field,
            request,
        )
        assert m2m_false_formfield is not None
        assert m2m_false_formfield.queryset is not None
        assert 'direction' not in str(m2m_false_formfield.queryset.query)

        fk_field = Leader._meta.get_field('department')  # noqa: SLF001
        fk_formfield = leader_admin.formfield_for_foreignkey(fk_field, request)
        assert fk_formfield is not None
        assert fk_formfield.queryset is not None
        assert 'JOIN' in str(fk_formfield.queryset.query)

        fk_direction_field = Leader._meta.get_field('direction')  # noqa: SLF001
        fk_dir_formfield = leader_admin.formfield_for_foreignkey(
            fk_direction_field,
            request,
        )
        assert fk_dir_formfield is not None
        assert fk_dir_formfield.queryset is not None
        assert 'JOIN' not in str(fk_dir_formfield.queryset.query)
