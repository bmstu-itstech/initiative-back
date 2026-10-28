# Создание мероприятий и назначений оргкомитета.

from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('members', '0010_alter_department_name_alter_direction_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'deleted_at',
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        null=True,
                        verbose_name='Дата удаления',
                    ),
                ),
                (
                    'name',
                    models.CharField(max_length=64, verbose_name='Название'),
                ),
                (
                    'starts_at',
                    models.DateTimeField(db_index=True, verbose_name='Начало'),
                ),
                ('ends_at', models.DateTimeField(verbose_name='Окончание')),
                (
                    'description',
                    models.CharField(
                        blank=True,
                        default='',
                        max_length=512,
                        verbose_name='Описание',
                    ),
                ),
                (
                    'locations',
                    ArrayField(
                        base_field=models.CharField(max_length=64),
                        blank=True,
                        default=list,
                        verbose_name='Места проведения',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Мероприятие',
                'verbose_name_plural': 'Мероприятия',
                'constraints': [
                    models.CheckConstraint(
                        condition=models.Q((
                            'starts_at__lte',
                            models.F('ends_at'),
                        )),
                        name='event_start_before_end',
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name='EventOrganizer',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('role', models.CharField(max_length=64, verbose_name='Роль')),
                (
                    'event',
                    models.ForeignKey(
                        db_index=True,
                        on_delete=models.CASCADE,
                        related_name='organizers',
                        to='events.event',
                        verbose_name='Мероприятие',
                    ),
                ),
                (
                    'member',
                    models.ForeignKey(
                        db_index=True,
                        on_delete=models.CASCADE,
                        related_name='event_memberships',
                        to='members.member',
                        verbose_name='Активист',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Член оргкомитета',
                'verbose_name_plural': 'Члены оргкомитета',
                'constraints': [
                    models.UniqueConstraint(
                        fields=('event', 'member', 'role'),
                        name='unique_event_member_role',
                    ),
                ],
            },
        ),
    ]
