from datetime import UTC, datetime, timedelta

import pytest
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.db.migrations.state import ProjectState
from django.test import RequestFactory
from django_test_migrations.migrator import Migrator

from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member

HOST_ROLE = 'Ведущий'
MEMBERS_APP = 'members'
EVENTS_APP = 'events'


@pytest.mark.django_db
def test_event_database_constraints(member: Member) -> None:
    """База запрещает обратные даты и повторные назначения."""
    start = datetime(2026, 10, 28, tzinfo=UTC)
    with pytest.raises(IntegrityError), transaction.atomic():
        Event.objects.create(
            name='Ошибка дат',
            starts_at=start,
            ends_at=start - timedelta(seconds=1),
        )
    event = Event(name='Встреча', starts_at=start, ends_at=start)
    event.save()
    EventOrganizer.objects.create(event=event, member=member, role=HOST_ROLE)
    with pytest.raises(IntegrityError), transaction.atomic():
        EventOrganizer.objects.create(
            event=event,
            member=member,
            role=HOST_ROLE,
        )
    EventOrganizer.objects.create(
        event=event,
        member=member,
        role='Организатор',
    )
    assert EventOrganizer.objects.count() == 2


def _legacy_profile(state: ProjectState) -> tuple[int, int]:
    """Создаёт прежний профиль с принадлежностью к отделу."""  # noqa: RUF002
    direction = state.apps.get_model(MEMBERS_APP, 'Direction').objects.create(
        name='Направление',
    )
    department = state.apps.get_model(MEMBERS_APP, 'Department').objects.create(
        name='Отдел',
        direction=direction,
    )
    member = state.apps.get_model(MEMBERS_APP, 'Member').objects.create(
        first_name='Иван',
        last_name='Иванов',
        telegram='ivanov',
    )
    member.departments.add(department)
    return member.pk, department.pk


def _migrated_assignment(state: ProjectState, member_id: int) -> None:
    """Проверяет назначение прежнего активиста и уникальность тройки."""
    start = datetime(2026, 10, 28, tzinfo=UTC)
    event = state.apps.get_model(EVENTS_APP, 'Event').objects.create(
        name='Встреча',
        starts_at=start,
        ends_at=start,
        locations=['Место'],
    )
    organizer_model = state.apps.get_model(EVENTS_APP, 'EventOrganizer')
    organizer_model.objects.create(
        event=event,
        member_id=member_id,
        role=HOST_ROLE,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        organizer_model.objects.create(
            event=event,
            member_id=member_id,
            role=HOST_ROLE,
        )


def test_event_migration_roundtrip(migrator: Migrator) -> None:
    """Миграция сохраняет активистов и откатывается без потери их связей."""
    state = migrator.apply_initial_migration((
        MEMBERS_APP,
        '0010_alter_department_name_alter_direction_name_and_more',
    ))
    member_id, department_id = _legacy_profile(state)
    state = migrator.apply_tested_migration((EVENTS_APP, '0001_initial'))
    _migrated_assignment(state, member_id)
    state = migrator.apply_tested_migration((EVENTS_APP, None))
    preserved = state.apps.get_model(MEMBERS_APP, 'Member').objects.get(
        pk=member_id,
    )
    assert preserved.departments.get().pk == department_id
    with pytest.raises(LookupError):
        state.apps.get_model(EVENTS_APP, 'Event')


@pytest.mark.django_db
def test_event_admin_soft_delete(member: Member) -> None:
    """Администрирование сохраняет мероприятия и назначения при удалении."""
    assert (
        bool(admin.site.is_registered(Event)),
        bool(admin.site.is_registered(EventOrganizer)),
    ) == (
        True,
        True,
    )
    event_admin = admin.site.get_model_admin(Event)
    start = datetime(2026, 10, 28, tzinfo=UTC)
    event = Event(name='Встреча', starts_at=start, ends_at=start)
    event.save()
    EventOrganizer.objects.create(event=event, member=member, role=HOST_ROLE)
    request = RequestFactory().get('/admin/')
    event_admin.delete_model(request, event)
    assert (
        bool(not Event.objects.exists()),
        bool(event_admin.get_queryset(request).filter(pk=event.pk).exists()),
    ) == (
        True,
        True,
    )
    event.restore()
    event_admin.delete_queryset(request, Event.objects.all())
    assert (
        bool(not Event.objects.exists()),
        bool(Event.all_objects.filter(pk=event.pk).exists()),
        EventOrganizer.objects.count(),
    ) == (
        True,
        True,
        1,
    )
