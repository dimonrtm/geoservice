# День 6 Sprint 2: план реализации synchronous Save

> **Для агента-исполнителя:** использовать `superpowers:executing-plans` при последовательном исполнении либо `superpowers:subagent-driven-development`, если пользователь выберет этот способ. Читать этот план вместе со спецификацией. Отмечать шаги только после проверки. Правила репозитория запрещают staging, commit и push; соответствующие шаги навыков не выполнять.

**Цель:** реализовать внутренний Save с одной transaction, глобальным CommandId, durable successful replay и revision только на content change.

**Архитектура:** метод `EditVersionService.save_geometry()` управляет сценарием и transaction. `EditVersionRepository` содержит geometry, command и revision persistence на той же session. Canonicalization/fingerprint переиспользуют ядро Дня 4; отдельные services/repositories не вводятся.

**Стек:** Python 3.12, SQLAlchemy 2, asyncpg, GeoAlchemy2, Shapely, Decimal, PostgreSQL 16 / PostGIS 3.4, pytest; существующие зависимости.

**Спецификация:** [День 6: synchronous Save и идемпотентность](2026-10-11-day-6-save-design.md), принята 11 октября 2026 года.

**Статус:** реализация завершена 11 октября 2026 года. Все шесть задач проверены; результаты и адаптации группировки тестов — в [отчёте](2026-10-11-day-6-save-implementation-report.md). Отметки ниже означают выполнение соответствующих требований с этими адаптациями.

## Общие ограничения

- Save остаётся в `EditVersionService`; persistence — в `EditVersionRepository`. Не вводить SaveEditVersionService, CommandRepository или EventRepository.
- Одна внешняя transaction; никаких savepoints, отдельного commit running, второй session или implicit retry всей mutation. Repository не делает commit/rollback.
- READ COMMITTED; root lock до чтения context; после root не брать конфликтующий WorkOrder lock. AOI/baseline/assignment неизменны на время Save по допущению Дня 5.
- Token сравнивается как opaque string с `str(draft_revision)`; matching replay распознаётся раньше stale-проверки новой команды.
- Content change, включая возврат baseline: revision +1. No-op/replay: revision неизменна. Новый no-op сохраняет successful command.
- `operation=unchanged` → `hasPersistedChangeSet=false`, `basicValidation=null`; `operation=updated` → true и summary ТЗ.
- В День 6 нет записи событий и новых durable rejections. Failed новая попытка откатывается, исходный registry при reuse неизменен. Access retry rejected → running отложен.
- Нет публичного endpoint, UI, workspace extensions, новых migrations и изменения fingerprints/geometry policy.
- History читается для защиты ID после удаления registry. Бессрочной дедупликации удалённых команд без history нет.
- D5-Q1 о нулевых соседних сегментах действует без изменения; остаётся временным доменным правилом.
- DB tests только в disposable `geoservice-db-tests` / `geo_test`; не использовать demo-БД.
- Соблюдать `docs/agent-memory/patterns/2026-10-07-python-formatting-style.md`, включая SQL. Новые документы на русском в `docs/sprint_2`, изменения unstaged.

## Особое внимание при ревью

1. Fingerprint одного retry после более позднего Save не должен зависеть от нового current; даже spatial validation нового current не должна подменять replay — задача 3.
2. Конфликт одного ID между разными versions не должен превращаться в successful второй Save или делать transaction aborted после unique violation — задачи 1 и 5.
3. Пропавший победитель reservation между DO NOTHING и SELECT не означает разрешение повторной mutation — задача 3.
4. Ошибка именно deferred commit, когда запись succeeded уже выполнена, не должна позволить сервису вернуть success — задача 4.
5. ORM identity map со старой root revision и root handle после `write_current()` не должны дать неверный response token или повторный increment — задачи 1 и 5.

## Файлы и зависимости задач

Пути ниже относительны `apps/backend`, кроме `docs/` и `infra/`.

| Файл | Действие и роль |
| --- | --- |
| `utility_service/use_cases/services/edit_version_service.py` | Изменить: Save orchestration; Open остаётся совместимым |
| `utility_service/use_cases/schemas/edit_version/geometry_save_out.py` | Создать: dataclass `SaveGeometryResult`, payload builder |
| `utility_service/use_cases/schemas/edit_version/__init__.py` | Изменить: экспорт result |
| `utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` | Изменить: публичные command/revision методы агрегата |
| `utility_service/infrastructure/postgresql/repositories/edit_version_commands.py` | Создать: внутренние SQL helpers registry/history; не отдельный repository-класс |
| `utility_service/infrastructure/postgresql/repository_rows/edit_version_command.py` | Создать: frozen `EditVersionCommandRow` |
| `utility_service/infrastructure/tests/test_edit_version_command_protocol.py` | Создать: transaction/root provenance и single-use revision |
| `utility_service/use_cases/tests/test_save_geometry_service.py` | Создать: success/no-op/revert/token и transaction contract |
| `utility_service/use_cases/tests/test_save_geometry_replay.py` | Создать: identity/replay/errors |
| `utility_service/use_cases/tests/save_geometry_service_support.py` | Создать: общий fake transaction и repository для этих двух suites |
| `tests/integration_tests/save_geometry_support.py` | Создать: реальные actor/service fixtures и снимки состояния |
| `tests/integration_tests/test_edit_version_command_repository.py` | Создать: реальный SQL registry/revision |
| `tests/integration_tests/test_save_geometry_atomicity.py` | Создать: full Save и rollback/commit/recovery |
| `tests/integration_tests/test_save_geometry_concurrency.py` | Создать: отдельные sessions и ожидание реальных locks |
| `docs/sprint_2/2026-10-11-day-6-save-implementation-report.md` | Создать только после исполнения; результаты и ограничения |

Зависимости: 1 → 2 → 3 → 4 → 5 → 6. Небольшие test support файлы создаются вместе с первым использующим их тестом. `deps.py` уже собирает EditVersionService с нужными repositories: новая DI boundary не нужна.

## Команды проверки

PowerShell из корня репозитория. После изменения исходников пересобирать image: исходники копируются при build.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

Обозначение **U(path)** — подставить конкретный test path задачи вместо `TEST_PATH`:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest TEST_PATH --tb=short
```

Обозначение **D(path)** — DB tests с разрешённым isolated окружением:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest TEST_PATH --tb=short
```

`RED` — падение целевого assertion или отсутствие ещё не созданного интерфейса; Docker/network/dependency failure не считается RED. `GREEN` — exit code 0, выполненные tests без пропуска требуемых DB сценариев. Перед исполнением проверить checkout/worktree и пользовательские изменения; планирование worktree не создаёт.

## Задача 1. Persistence команд и revision под root lock

**Файлы:** repository, command SQL helpers/row, command protocol tests и `test_edit_version_command_repository.py` из таблицы.

**Потребляет:** существующие `LockedEditVersion`, `EditGeometryScope.require(root)`, `EditVersionCommand`, `EditVersionChangeEvent` и их DB constraints.

**Предоставляет:** frozen `EditVersionCommandRow` с `command_id`, `edit_version_id`, `feature_id`, `actor_user_id: UUID`; `request_fingerprint: str`; `state: EditVersionCommandState`; `retry_on_access_change: bool`; `response_status: int | None`; `response_payload: dict[str, Any] | None`; `rejection_code`, `rejection_message: str | None`.

Новые методы `EditVersionRepository`:

```python
async def get_command(self, root: LockedEditVersion, *, command_id: UUID) -> EditVersionCommandRow | None
async def command_has_history(self, root: LockedEditVersion, *, command_id: UUID) -> bool
async def reserve_command(self, root: LockedEditVersion, *, command_id: UUID, feature_id: UUID, actor_id: UUID, fingerprint: str) -> bool
async def complete_command(self, root: LockedEditVersion, *, command_id: UUID, payload: dict[str, Any]) -> None
async def increment_revision(self, root: LockedEditVersion) -> int
```

Все методы проверяют root provenance. Lookup CommandId глобальный, не фильтруется по root.id. Reservation использует root.id; complete обновляет только running строку с этим command_id и root.id, устанавливает status=200/completed_at. Ноль изменённых строк — `RepositoryProtocolError`. Revision UPDATE проверяет id и `draft_revision=root.draft_revision`, возвращает новое значение; повтор с тем же старым root не допускает второй increment.

- [x] Добавить failing tests `test_reserve_conflict_keeps_existing_command`, `test_command_lookup_is_global`, `test_revision_requires_live_root_and_expected_revision`, `test_running_cannot_commit`. Проверять bool reservation, неизменность исходных identity/payload, revision 1→2 и отказ повторного increment.

Ключевые assertions после вызовов repository в этих tests:

```python
assert first_reserved is True
assert second_reserved is False
assert stored.request_fingerprint == original_fingerprint
assert next_revision == 2
```

- [x] Проверить command protocol и repository; зафиксировать ожидаемые RED. Адаптация исполнения: вместо отдельного U(`utility_service/infrastructure/tests/test_edit_version_command_protocol.py`) provenance проверен реальной session в D(`tests/integration_tests/test_edit_version_command_repository.py`); 4 RED → 4 GREEN.
- [x] Реализовать rows и методы; SQL helpers в `edit_version_commands.py` получают session/аргументы, но не управляют transaction. Для reservation использовать PostgreSQL insert с `on_conflict_do_nothing(index_elements=[command_id])` и RETURNING; complete не является upsert.
- [x] В DB test зарезервировать, финализировать, commit и прочитать через новую session: state=succeeded, status=200, payload полностью совпадает. Проверить history-only ID существующими helpers и запрет complete чужого root.
- [x] Проверить совместимость root после `write_current()`, запрет foreign/expired root и overflow BIGINT с rollback. SQL UPDATE выполняется без autoflush посторонних ORM изменений.
- [x] Повторить те же U/D до GREEN; ревью ограничений PK, state transitions и отсутствия commit/savepoint.

## Задача 2. Новый успешный Save, no-op и возврат baseline

**Файлы:** `edit_version_service.py`, result schema/export, service support, `test_save_geometry_service.py`.

**Потребляет:** persistence задачи 1; существующие `GeometrySaveRequest`, fingerprint, prepare/validate/write, codec.

**Предоставляет:**

```python
@dataclass(frozen=True)
class SaveGeometryResult:
    status_code: int
    payload: dict[str, Any]

def build_geometry_save_payload(*, command_id: UUID, feature_id: UUID, draft_revision: int, operation: Literal["unchanged", "updated"], geometry: dict[str, Any]) -> dict[str, Any]

async def EditVersionService.save_geometry(self, *, work_order_id: UUID, edit_version_id: UUID, feature_id: UUID, actor_id: UUID, request: GeometrySaveRequest) -> SaveGeometryResult
```

`status_code=200`; payload builder использует только поля §7 спецификации. Геометрия передаётся из `geometry_to_geojson(decode_geometry(write_result.after_ewkb))`. Builder не обращается к БД. Frozen dataclass не делает вложенный dict immutable: возвращаемый результат и переданный на persistence payload не должны разделять изменяемый объект с fake/кэшем registry.

- [x] Добавить `test_save_changes_geometry_once`, `test_noop_baseline_has_null_validation`, `test_noop_updated_keeps_summary`, `test_save_baseline_restores_unchanged`. В каждом проверять полный payload; increment вызван ровно один раз только для двух content-change случаев.

Для baseline no-op с исходной revision 1:

```python
assert result.status_code == 200
assert result.payload["draftVersionToken"] == "1"
assert result.payload["operation"] == "unchanged"
assert result.payload["hasPersistedChangeSet"] is False
assert result.payload["basicValidation"] is None
repository.increment_revision.assert_not_awaited()
```

- [x] В fake transaction учитывать вход, commit/rollback и отсутствие возвращённого результата до выхода. U(`utility_service/use_cases/tests/test_save_geometry_service.py`) должен дать RED нового метода.
- [x] Реализовать Save в существующем сервисе: transaction → actor → root/context → assignment/lifecycle → canonical fingerprint → lookup/history/reservation → token → validation/write → revision при changed → payload/finalization → выход transaction → return.
- [x] Для отсутствующего/неактивного/non-Editor actor возвращать ROLE_NOT_ALLOWED, сохранив прежнее поведение Open. Не переиспользовать `get_visible_work_order()` после root lock: этот метод блокирует WorkOrder.
- [x] Добавить `test_fresh_save_requires_exact_opaque_token` с token `01` при revision=1 и `test_save_uses_persisted_geometry_policy`: stale rollback; fingerprint/preparation используют policy root, а не текущие global settings.
- [x] Проверить FK-valid target, missing context и canonical response с baseline вне grid; использовать existing codec/core, без копирования алгоритмов.
- [x] Выполнить U(`utility_service/use_cases/tests/test_save_geometry_service.py`) и U(`utility_service/use_cases/tests/test_edit_version_service.py`) до GREEN. Сценарии занятых ID окончательно закрывает задача 3; промежуточный метод не подключать к API.

## Задача 3. Replay, reuse и ожидаемые отказы

**Файлы:** тот же service, test support и `test_save_geometry_replay.py`.

**Потребляет:** `save_geometry()` и result задачи 2, `get_command/reserve_command/command_has_history` задачи 1. Новых public интерфейсов не вводит.

- [x] Добавить `test_replay_a_after_b_returns_original_result`: current/revision B, исходный token A, сохранённый payload A; assert payload==A и отсутствуют validate/write/increment/complete вызовы. Отдельно проверить, что spy spatial validation, настроенный на падение, не вызывается на replay.

```python
assert result.payload == saved_a_payload
repository.validate_candidate.assert_not_awaited()
repository.write_current.assert_not_awaited()
repository.increment_revision.assert_not_awaited()
repository.complete_command.assert_not_awaited()
```

- [x] Добавить параметризованный `test_reuse_changes_identity` по actor/target/token/canonical intent, `test_equivalent_geometry_replays`, `test_access_and_closed_lifecycle_precede_replay` и `test_history_only_id_is_reused`.
- [x] Выполнить U(`utility_service/use_cases/tests/test_save_geometry_replay.py`) для RED; тесты новых сценариев не должны считаться готовыми из-за заглушки общего исключения.
- [x] Реализовать matching replay и mismatch rejection. После проигранной reservation сделать отдельный get_command. Missing winner → history check → COMMAND_ID_REUSED при event либо RepositoryProtocolError без mutation при отсутствии event. Не выполнять повторную reservation в этой попытке.
- [x] Добавить `test_disappeared_reservation_winner_does_not_mutate` для обоих исходов history; `test_rejected_row_replays_without_access_resume`; `test_response_mutation_does_not_change_saved_payload` через изменение возвращённого dict и повторный вызов.
- [x] Реализовать централизованный mapping status/code из §8 спецификации. Unknown exceptions не превращать в geometry rejection; known RepositoryRejection/GeometryRuleError/InvalidGeometryContext обработать по их смыслу. Matching legacy rejected row воспроизводит status/code/message, без rejected→running даже при retry flag.
- [x] Покрыть каждый mapping и приоритет stale перед новой transition validation; подготовка fingerprint может раньше вернуть missing/corrupt baseline или FEATURE_NOT_EDITABLE. Проверить rollback каждой новой ошибочной попытки, неизменность существующего success и отсутствие раскрытия чужого payload.
- [x] Повторить оба новых service suites и Open suite до GREEN; проверить отсутствие новых успешных полей вроде `replayed`.

## Задача 4. Реальный Save: атомарность и durable результат

**Файлы:** `save_geometry_support.py`, `test_save_geometry_atomicity.py`; production меняется только для устранения дефектов, подтверждённых тестом.

**Потребляет:** реальные service/repository задач 1–3, существующие `seed_repository_context`, `snapshot_repository_state`, `run_committed_scenario`.

**Предоставляет test-only:**

```python
async def seed_save_context(connection: AsyncConnection) -> dict[str, UUID]
def build_save_service(session: AsyncSession) -> EditVersionService
async def snapshot_save_state(connection: AsyncConnection, ids: dict[str, UUID]) -> dict[str, Any]
```

`seed_save_context` дополняет geometry fixture реальным active Editor в таблице user.users с actor_user_id и уникальным email; существующий fixture создаёт только UUID actor, не User. `build_save_service` использует реальные User/WorkOrder/DefaultState/EditVersion repositories одной session. Snapshot включает existing geometry snapshot, command rows и history count без datetime-зависимых утверждений.

- [x] Добавить `test_save_commits_snapshot_revision_and_result`, `test_noop_and_revert_committed_payloads`, `test_retry_new_session_returns_durable_result`. Проверить exact baseline EWKB, отсутствие изменений associations/properties/network_version, revision и payload из независимой session.
- [x] Запустить D(`tests/integration_tests/test_save_geometry_atomicity.py`). Если уже GREEN за счёт предыдущих задач, зафиксировать это честно; не портить код для искусственного RED.
- [x] Добавить parameterized `test_save_rolls_back_after_write_revision_and_finalize`: test-only subclass/monkeypatch repository вызывает реальный метод и затем выбрасывает ошибку. После каждой ошибки snapshot целиком прежний, новая command row отсутствует. Проверить повтор с тем же ID после rollback.

```python
assert snapshot_after_failure == snapshot_before_save
assert command_after_failure is None
```

- [x] Добавить `test_deferred_commit_failure_never_returns_success`: в test-only override complete_command оставить зарезервированную строку running без finalization, не выбрасывая исключение внутри body; реальный deferred trigger должен отклонить commit. Независимое чтение доказывает rollback geometry/revision/registry. Production fault hooks не добавлять.
- [x] Добавить `test_response_lost_after_commit_replays`: первый реальный вызов committed, его результат не используется; новая session повторяет request и читает прежний payload, revision не меняется. Это тест потерянного ответа, а не имитация доказанного сетевого сбоя внутри commit.
- [x] Добавить `test_history_only_command_is_rejected` на корректно созданном event и удалённом старом root/registry; target новой попытки доступен, mutation не выполняется. Проверить legacy rejected rows без новых durable отказов.
- [x] Повторить D до GREEN, исправляя только найденные дефекты. Собственные Save этого этапа не добавляют событий: проверять unchanged history count, а не игнорировать таблицу.

## Задача 5. Конкурентные Save и Open

**Файлы:** `test_save_geometry_concurrency.py`, test support; существующий `test_edit_geometry_concurrency.py` — источник паттерна наблюдения locks.

**Потребляет:** весь production Save и support задачи 4. Протокол production не расширяется ради orchestration тестов.

- [x] Добавить `test_same_command_concurrent_save_mutates_once`: две реальные sessions вызывают один request. Test-only barrier после root lock держит первый вызов; observer через pg_blocking_pids доказывает ожидание второго. После release ответы одинаковы, mutation одна, revision=2 и одна successful row.

```python
assert first_result.payload == second_result.payload
assert persisted_revision == 2
assert successful_command_count == 1
assert running_command_count == 0
```

- [x] Добавить `test_different_commands_same_token_make_second_stale`: первый выполняет content change; второй со своим ID/token=1 получает stale, его registry row отсутствует. Обе задачи завершаются, committed running отсутствует.
- [x] Добавить `test_same_id_different_versions_has_one_owner` и `test_reservation_rollback_allows_other_version`: barrier после успешной reservation первой version; второй вызов ожидает conflict по ID. При commit первого второй получает reuse; при rollback первый ничего не сохраняет, второй может выполнить свой допустимый intent. Не использовать общий root в этом тесте.
- [x] Добавить `test_waiting_save_uses_fresh_revision_with_loaded_orm`: внутри test-only repository override до ожидания root загрузить ORM root/feature со старым состоянием, не завершая внешнюю transaction; после commit первого Save второй должен видеть новую revision и дать stale. Не начинать transaction до вызова service извне.
- [x] Добавить `test_save_and_open_do_not_deadlock` в обоих порядках с реальными service методами. Включить bounded asyncio timeout, observer locks и гарантированные cancel/gather/rollback в finally.
- [x] Выполнить D(`tests/integration_tests/test_save_geometry_concurrency.py`), исправить доказанные ошибки. Тесты не используют sleep как единственное доказательство порядка или ожидания; observer может опрашивать pg_blocking_pids с bounded timeout по существующему образцу.
- [x] Проверить оба новых DB suites вместе и протокол repository Дня 5; занятый PK не должен вести к savepoint или обращению к root другой version для изменения.

## Задача 6. Регрессия, ревью и отчёт

**Файлы:** только необходимые исправления из проверок; report и README в `docs/sprint_2`.

- [x] Пересобрать test image. Выполнить весь non-DB backend suite:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest --tb=short
```

- [x] Выполнить полный fresh isolated DB suite штатным runner из корня:

```powershell
infra\db-tests.cmd
```

Runner очищает только disposable test project; проверить target перед исполнением. Exit code 0 и выполненные DB tests обязательны; skips не заменяют доказательство. Если cmd недоступен в выбранном окружении, воспроизвести его Compose lifecycle с тем же project и isolation guards.

- [x] Выполнить `python -m black --check .` и `python -m ruff check .` из backend test image командами U-окружения с заменой pytest-команды на соответствующий инструмент. Проверить SQL форматирование вручную и `git diff --check`. Не форматировать несвязанный код.
- [x] Провести итоговое ревью diff против пяти focus cases и §1–12 спецификации. Способ независимого review определяется выбранным execution workflow; self-review не выдавать за независимое. Не создавать PR, не staging/commit/push.
- [x] Написать implementation report: сценарии/команды/exit codes, ограничения Дня 6, D5-Q1, фактические отклонения и состояние требований. Если обязательные DB проверки недоступны, День 6 не объявлять принятым.
- [x] Обновить README и отметки задач только по фактическим результатам. Оценить необходимость repository-change ingest и memory по правилам репозитория; не создавать их ради завершения плана. Завершение кода само по себе не является триггером ingest.

## Самопроверка плана

| Раздел спецификации | Задачи |
| --- | --- |
| Scope и агрегатная граница, единая session | 1–3 |
| Command identity, global reservation, terminal transitions | 1, 3, 5 |
| Geometry/revision/no-op/Revert и successful payload | 1–2, 4 |
| Replay, errors, lifecycle/access и legacy rejection | 3–4 |
| Commit/rollback и неизвестный клиенту исход | 4 |
| Конкуренция и свежие данные после lock | 5 |
| Регрессия и критерий готовности | 6 |

Пять review focus cases имеют адресные тесты в соответствующих задачах. Новые signatures и типы определены до их использования; supporting fixtures включены в задачи проверки. Технические проверки при подготовке плана ограничиваются документом и ссылками: product tests и test DB не запускались.

План принят пользователем и выполнен последовательно в текущем чате. Независимое review завершено без открытых блокирующих замечаний; изменения оставлены unstaged.
