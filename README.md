# Backend проекта «Инициатива» (`initiative-back`)

<p align="center">
   <a href="https://its-bmstu.ru/">
      <picture>
         <img src="https://avatars.githubusercontent.com/u/124603745?s=200" alt="ITS Tech logo" width="10%" height="auto" />
      </picture>
   </a>
</p>

Backend системы для управления активистами Студенеского совета ИУ.

Разработано отделом **ITS Tech** направления ITS BMSTU студенческого совета факультету ИУ МГТУ им. Баумана.

## Идея проекта

**Цель проекта** — автоматизировать учет и управление структурой студенческой организации. Система предоставляет удобный API для ведения единой базы данных участников, отслеживания их принадлежности к отделам и направлениям, а также управления руководителями.

## Стек технологий

[![Python 3.13.3](https://img.shields.io/badge/Python-3.13.3-blue)](https://docs.python.org/3.13/)
[![wemake.services](https://img.shields.io/badge/%20-wemake.services-green.svg?label=%20&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC%2FxhBQAAAAFzUkdCAK7OHOkAAAAbUExURQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP%2F%2F%2F5TvxDIAAAAIdFJOUwAjRA8xXANAL%2Bv0SAAAADNJREFUGNNjYCAIOJjRBdBFWMkVQeGzcHAwksJnAPPZGOGAASzPzAEHEGVsLExQwE7YswCb7AFZSF3bbAAAAABJRU5ErkJggg%3D%3D)](https://wemake-services.github.io)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)
[![Modern REST](https://img.shields.io/badge/Modern%20REST-0C4B33?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTA4MCIgaGVpZ2h0PSIxMDgwIiB2aWV3Qm94PSIwIDAgMTA4MCAxMDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJNMiA3MDQuMDJMMTQ1LjQ1OSA0NjYuMTlMMjc3Ljg4MyA3MDQuMDJMMTQ1LjQ1OSA5NDEuODQ5TDIgNzA0LjAyWiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTE0NS40NTkgOTQxLjg0OUwyIDcwNC4wMkgyNzcuODgzTDE0NS40NTkgOTQxLjg0OVoiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik02NzguOTQ4IDcwNC4wMzVMMzQxLjIzIDEzOEwyMjcuMDcxIDMyOC4yNjRMNDM2LjM2MiA3MDQuMDM1TDMwMy4xNzcgOTQxLjg2NEg1MzYuMjVMNjc4Ljk0OCA3MDQuMDM1WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTY3OC45MzcgNzA0LjAyNkg0MzYuMzVMMzAzLjE2NiA5NDEuODU2SDUzNi4yMzlMNjc4LjkzNyA3MDQuMDI2WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTEwNzguMTcgNzA0LjAzNUw3NDAuNDUxIDEzOEw2MjYuMjkzIDMyOC4yNjRMODM1LjU4MyA3MDQuMDM1TDcwMi4zOTkgOTQxLjg2NEg5MzUuNDcyTDEwNzguMTcgNzA0LjAzNVoiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0xMDc4LjE3IDcwNC4wMzVIODM1LjU4M0w3MDIuMzk5IDk0MS44NjRIOTM1LjQ3MkwxMDc4LjE3IDcwNC4wMzVaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K&color=35544A)](https://github.com/wemake-services/django-modern-rest)
[![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-336791)](https://www.postgresql.org/docs/18/index.html)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Проект создан на основе шаблона [`wemake-django-template`]((https://github.com/wemake-services/wemake-django-template)). Версия шаблона: [fb03a37](https://github.com/wemake-services/wemake-django-template/tree/fb03a37fbc9282dc8a521c2b620ab8e3e68a01b5). Разница с обновлённой версией шаблона [тут]([updated](https://github.com/wemake-services/wemake-django-template/compare/fb03a37fbc9282dc8a521c2b620ab8e3e68a01b5...master)).

**Контейнирезация:** `Docker` и `Docker Compose` последнией версии

**Ядро:**

* `Python 3.13.3`
* `Django 6.0.4`
* `DMR (Django Modern REST) 0.7.0` и `msgspec 0.21.1`
* `Pydantic 2.13.3`
* `Punq 0.7.0`

**База данных:** `PostgreSQL 18`

**Безопасность:**

* `Authlib 1.7.0` и `PyJWT 2.12.1`
* `django-axes 8.3.1`
* `django-cors-headers 4.9.0`
* `django-csp 4.0` и `django-permissions-policy 4.29.0`

**Тестирование:**

* `Pytest 9.0.3` и `pytest-django 4.12.0`
* `Polyfactory 3.3.0` и `Faker 40.15.0`
* `Schemathesis 4.15.2`
* `django-test-migrations 1.5.0`

**Контроль качества кода**:

* `Ruff 0.15.12`
* `Mypy 1.20.2` и `django-stubs 6.0.3`
* `django-zeal 2.1.0`
* `wemake-python-styleguid 1.6.1`

## Руководство по развертыванию (Локальная разработка)

### Клонирование репозитория

Склонируйте репозиторий на свой локальный компьютер и перейдите в директорию проекта:

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd initiative-back
```

### Настройка переменных окружения

Скопируйте шаблон и создайте свой локальный `.env` файл:

```bash
cp config/.env.template config/.env

```

**Важно**: Откройте созданный файл `config/.env` и обязательно измените значение `DJANGO_SECRET_KEY`.
По умолчанию там стоит `__CHANGEME__` (12 символов), однако алгоритмы шифрования (`HMAC-SHA256`) требуют, чтобы секретный ключ был длиной не менее `32` символов, иначе сервер будет выдавать ошибку `InsecureKeyLengthWarning` при попытке входа (генерации токена).

Вы можете сгенерировать надежный ключ прямо в терминале:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Скопируйте результат и вставьте его в `DJANGO_SECRET_KEY=...` в вашем `.env` файле.

### Сборка и запуск контейнеров

Запустите проект с помощью Docker Compose:

```bash
docker compose up -d --build
```

### Применение миграций БД

Когда контейнеры успешно запустятся, вам нужно создать структуру базы данных:

```bash
docker compose exec web python manage.py migrate

```

### Создание суперпользователя (Админа)

Для доступа к панели администратора создайте первого суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser

```

Следуйте подсказкам в терминале (введите логин и пароль).

### Проверка работоспособности

Если все шаги выполнены успешно, проект доступен по следующим адресам:

* **Swagger UI:** [http://localhost:8000/docs/swagger/](http://localhost:8000/docs/swagger/)
* **Stoplight:** [http://localhost:8000/docs/stoplight/](http://localhost:8000/docs/stoplight/)
* **Scalar:** [http://localhost:8000/docs/scalar/](http://localhost:8000/docs/scalar/)
* **Redoc:** [http://localhost:8000/docs/redoc/](http://localhost:8000/docs/redoc/)
* **django-health-check:** [http://localhost:8000/health/](http://localhost:8000/health/)
* **Панель Администратора:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

### Разработка вне Docker

Для разработки все Docker-а следует использовать пакетного менеджера `uv`. Сборка виртуального окружения и установка всех зависимостей выполняется одной командой:

```bash
uv sync
```

После этого вы можете использовать `uv run python manage.py ...` или `uv run pytest` для локального запуска.

## Структура данных и Сущности

**Soft Delete (Мягкое удаление)**:

Для предотвращения случайной потери данных все основные сущности наследуются от `SoftDeleteModel`. При удалении записи (через API) она физически остается в базе данных, но помечается датой в поле `deleted_at` и скрывается из всех стандартных запросов. Уникальные ограничения (`Unique Constraints`) учитывают этот флаг: можно создать нового активиста с Telegram-ником ранее удаленного пользователя.

### Активист (`Member`)

Центральная сущность системы, описывающая профиль студента.

| Поле | Тип | Обязательно | Размер | По умолчанию | Валидация / Примечание |
| --- | --- | --- | --- | --- | --- |
| `id` | Целое число | Да | `> 0` | Auto | Автоинкремент (PK) |
| `first_name` | Строка | Да | 1 - 64 симв. | - | - |
| `last_name` | Строка | Да | 1 - 64 симв. | - | - |
| `patronymic` | Строка | Нет | до 64 симв. | `""` (пустая строка) | - |
| `telegram` | Строка | Да | 5 - 32 симв. | - | RegEx: `^[a-zA-Z0-9_]{5,32}$` (без `@`) |
| `group` | Строка | Нет | до 32 симв. | `""` (пустая строка) | RegEx: форматы групп МГТУ (напр. *ИУ5-41Б*) |
| `birth_date` | Дата (YYYY-MM-DD) | Нет | - | `null` | - |
| `join_date` | Дата (YYYY-MM-DD) | Да* | - | Auto (текущая) | *Только для чтения. Заполняется сервером. |
| `departments` | Массив чисел | Нет | - | `[]` (пустой массив) | Массив `id` существующих отделов |

**Бизнес-правила:**

* **Уникальность ФИО:** В системе не может быть двух активных (не удаленных) студентов с абсолютно одинаковыми `first_name`, `last_name` и `patronymic`.
* **Уникальность Telegram:** Значение `telegram` должно быть строго уникальным среди всех активных участников.

### Направление (`Direction`)

Крупное структурное подразделение Студенческого совета.

| Поле | Тип | Обязательно | Размер | По умолчанию | Валидация / Примечание |
| --- | --- | --- | --- | --- | --- |
| `id` | Целое число | Да | `> 0` | Auto | Автоинкремент (PK) |
| `name` | Строка | Да | 1 - 32 симв. | - | - |

**Бизнес-правила:**

* **Уникальность названия:** Поле `name` должно быть строго уникальным в рамках всей системы.

### Отдел (`Department`)

Внутренняя структурная единица, подчиняющаяся конкретному Направлению.

| Поле | Тип | Обязательно | Размер | По умолчанию | Валидация / Примечание |
| --- | --- | --- | --- | --- | --- |
| `id` | Целое число | Да | `> 0` | Auto | Автоинкремент (PK) |
| `name` | Строка | Да | 1 - 32 симв. | - | - |
| `direction_id` | Целое число | Да | `> 0` | - | Внешний ключ (FK) на сущность `Direction` |

**Бизнес-правила:**

* **Уникальность названия:** Связка `(name, direction_id)` должна быть уникальной. Название отдела уникально **только внутри своего направления**.

### Руководитель (`Leader`)

Модель, связывающая Активиста с руководящей должностью в структуре организации.

| Поле | Тип | Обязательно | Размер | По умолчанию | Валидация / Примечание |
| --- | --- | --- | --- | --- | --- |
| `id` | Целое число | Да | `> 0` | Auto | Автоинкремент (PK) |
| `member_id` | Целое число | Да | `> 0` | - | Внешний ключ (FK) на сущность `Member` |
| `position` | Строка | Да | 1 - 32 симв. | - | - |
| `department_id` | Целое число | Нет | `> 0` | `null` | Внешний ключ (FK) на сущность `Department` |
| `direction_id` | Целое число | Нет | `> 0` | `null` | Внешний ключ (FK) на сущность `Direction` |

**Бизнес-правила:**

* **Привязка к структуре:** Руководитель может быть привязан к Отделу (`department_id`), к Направлению (`direction_id`), либо к обоим сразу.
* **Уникальность должности (в Отделе):** Пара `(position, department_id)` уникальна.
* **Уникальность должности (в Направлении):** Пара `(position, direction_id)` уникальна.

## Роли

Система использует ролевую модель доступа (Role-Based Access Control) на базе стандартных групп Django (`django.contrib.auth.models.Group`).

Существует три базовых уровня доступа:

### `Viewer` (Просмотр)

**Разрешено:**

* Выполнение всех `GET` запросов.
* Просмотр списков активистов, отделов, направлений и руководителей.
* Использование фильтрации, поиска и пагинации.

### `Editor` (Редактирование)

**Разрешено:**

* Все права роли `Viewer`.
* Создание, обновление и удаление профилей активистов, отделов, направлений и руководителей.

### `Admin` (Администратор)

**Разрешено:**

* Все права роли `Editor`.
* Управление учетными записями пользователей (выдача логинов/паролей).
* Назначение ролей (`Viewer`/`Editor`/`Admin`) другим пользователям.

## Маршруты

Все бизнес-маршруты API начинаются с префикса `/api/`. В системе реализованы стандартные REST-подходы для выполнения CRUD-операций.

### Авторизация (`/api/auth/`)

Отвечает за выдачу и обновление JWT-токенов доступа.

| Метод | Маршрут | Описание |
| --- | --- | --- |
| `POST` | `/api/auth/login/` | Авторизация пользователя (получение `access_token`). |
| `POST` | `/api/auth/refresh/` | Обновление истекшего токена. |

### Активисты (`/api/members/`)

Управление профилями студентов Студенческого совета.

| Метод | Маршрут | Описание |
| --- | --- | --- |
| `GET` | `/api/members/` | Получение списка всех активистов (с пагинацией, фильтрацией и поиском). |
| `POST` | `/api/members/` | Создание нового профиля активиста. |
| `GET` | `/api/members/{member_id}/` | Получение детальной информации об активисте по ID. |
| `PUT` | `/api/members/{member_id}/` | Обновление данных активиста. |
| `DELETE` | `/api/members/{member_id}/` | Мягкое удаление (Soft Delete) активиста. |
| `GET` | `/api/members/direction/{direction_id}/` | Получить всех активистов, состоящих в этом направлении. |
| `GET` | `/api/members/department/{department_id}/` | Получить всех активистов конкретного отдела. |

### Направления (`/api/members/directions/`)

Управление крупными структурными подразделениями.

| Метод | Маршрут | Описание |
| --- | --- | --- |
| `GET` | `/api/members/directions/` | Получение списка всех направлений. |
| `POST` | `/api/members/directions/` | Создание нового направления. |
| `GET` | `/api/members/directions/{direction_id}/` | Детальная информация о направлении. |
| `PUT` | `/api/members/directions/{direction_id}/` | Обновление названия направления. |
| `DELETE` | `/api/members/directions/{direction_id}/` | Удаление направления. |

### Отделы (`/api/members/departments/`)

Управление отделами внутри направлений.

| Метод | Маршрут | Описание |
| --- | --- | --- |
| `GET` | `/api/members/departments/` | Получение списка всех отделов. |
| `POST` | `/api/members/departments/` | Создание нового отдела (с привязкой к направлению). |
| `GET` | `/api/members/departments/{department_id}/` | Детальная информация об отделе. |
| `PUT` | `/api/members/departments/{department_id}/` | Обновление данных отдела. |
| `DELETE` | `/api/members/departments/{department_id}/` | Удаление отдела. |

### Руководители (`/api/members/leaders/`)

Назначение активистов на руководящие должности.

| Метод | Маршрут | Описание |
| --- | --- | --- |
| `GET` | `/api/members/leaders/` | Получение списка всех руководителей. |
| `POST` | `/api/members/leaders/` | Назначение активиста на должность в отдел/направление. |
| `GET` | `/api/members/leaders/{leader_id}/` | Детальная информация о должности. |
| `PUT` | `/api/members/leaders/{leader_id}/` | Обновление должности или перераспределение. |
| `DELETE` | `/api/members/leaders/{leader_id}/` | Снятие с должности. |

### Служебные маршруты и Документация

Система предоставляет автоматически генерируемую документацию (OpenAPI) и инструменты мониторинга состояния.

**Интерактивная документация:**

* `GET /docs/swagger/` — Swagger UI (классический интерфейс тестирования API).
* `GET /docs/redoc/` — Redoc (строгий и читаемый формат документации).
* `GET /docs/stoplight/` — Stoplight Elements.
* `GET /docs/scalar/` — Scalar (современный минималистичный клиент).
* `GET /docs/openapi.json/` — Сырой JSON-файл спецификации OpenAPI.
* `GET /docs/openapi.yaml/` — Сырой YAML-файл спецификации OpenAPI.

**Мониторинг и Администрирование:**

* `GET /health/` — Состояние системы (проверка подключения БД, кэша и хранилища файлов).
* `GET /admin/` — Классическая панель администратора Django.
* `GET /admin/doc/` — Автогенерируемая документация по моделям Django.

**Статические файлы (Мета-данные):**

* `GET /robots.txt` — Правила индексации для поисковых систем.
* `GET /humans.txt` — Информация о проекте.
* `GET /__debug__/` — *(Только в режиме разработки)* Интерфейс Django Debug Toolbar.

## Структура проекта

Проект базируется на строгом шаблоне `wemake-django-template`. Бизнес-логика изолирована от фреймворка, а доступ к данным осуществляется через паттерн `Repository`.

### Корневая директория

* `pyproject.toml` / `uv.lock` — конфигурация пакетов и строгий лок-файл зависимостей для менеджера `uv`.
* `docker-compose.yml` / `docker-compose.override.yml` — оркестрация контейнеров для разработки.
* `manage.py` — стандартная точка входа для команд Django.
* `schemathesis.toml` — конфигурация для property-based тестирования API.
* `.github/workflows/test.yml` — пайплайн непрерывной интеграции (CI) для автоматического запуска тестов и линтеров.

### `config/`

Хранит конфигурационные файлы окружения.

* `.env.template` — безопасный шаблон переменных (хранится в Git).
* `.env` — ваши локальные секреты (игнорируется Git).

### `docker/`

Вся инфраструктура для сборки контейнеров.

* `django/` — Dockerfile, скрипты инициализации (`entrypoint.sh`), настройки Gunicorn для backend-сервера.
* `caddy/` — настройки веб-сервера (если используется для раздачи статики в prod).

### `server/` (Ядро приложения)

Главная директория с исходным кодом бэкенда.

* `settings/` — настройки разбиты по компонентам (`api.py`, `caches.py`, `logging.py`) и окружениям (`development.py`, `production.py`) с помощью `django-split-settings`.
* `urls.py` — корневой роутер проекта.
* `common/` — общие утилиты и DI-контейнеры (Dependency Injection).

#### `server/apps/` (Бизнес-домены)

Разбиение функционала на модули (приложения):

**1. `auth/` (Аутентификация и Роли):**

* `controllers/` — эндпоинты для JWT (логин, рефреш).
* `logic/` — RBAC (Role-Based Access Control), проверка прав доступа (`permissions.py`, `roles.py`).

**2. `members/` (Ядро Студсовета):**

* `models.py` / `migrations/` — схемы таблиц БД и миграции.
* `controllers/` — слой API (обработчики HTTP-запросов, роутинг).
* `logic/` — ядро бизнес-логики, не зависящее от БД:
  * `usecases/` — сценарии использования (создание, удаление, выдача ролей).
  * `value_objects.py` — схемы `msgspec` (`...In` / `...Out`) для валидации контрактов.
  * `exceptions.py` — кастомные доменные ошибки.
* `infra/` — слой работы с данными:
* `repository.py` — инкапсуляция ORM-запросов (паттерн Репозиторий).
* `mappers.py` — преобразование моделей ORM в Value Objects.

### `tests/`

Сборник тестов для обеспечения 100% покрытия.

* `test_server/` — тесты конфигурации и инфраструктуры.
* `test_apps/` — функциональные и юнит-тесты приложений:
  * `test_factories.py` / `test_fixtures.py` — генерация мок-данных через Polyfactory.
  * `test_members/test_api/` — проверка API-рутов и кодов ответа.
  * `test_members/test_logic/` — изоляция бизнес-правил.
  * `test_members/test_models/test_migrations.py` — проверка целостности и отката миграций БД (в т.ч. дедупликация данных при изменении схем).
