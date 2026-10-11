# День 7 Sprint 2: план реализации отказов, событий и Revert

> **Для агента-исполнителя:** использовать `superpowers:executing-plans` для последовательного исполнения либо `superpowers:subagent-driven-development`, если пользователь выберет этот способ. Читать план вместе со спецификацией. Отмечать шаги только после проверки. Запрет репозитория на staging, commit и push имеет приоритет над соответствующими шагами навыков.

**Цель:** завершить внутренний Save/Revert с durable rejection, access retry, атомарной history и доказательствами M2.

**Архитектура:** одна transaction в `EditVersionService`, persistence в существующем `EditVersionRepository`. Сохранить geom-v1, добавить отдельный contextless fingerprint для ранних отказов. Записывать succeeded перед event внутри общей transaction.

**Стек:** Python 3.12, SQLAlchemy 2, asyncpg, GeoAlchemy2, Decimal, PostgreSQL 16/PostGIS 3.4, pytest; существующие зависимости.

**Спецификация:** [День 7: terminal rejection, история и Revert](2026-10-11-day-7-rejections-events-revert-design.md), принята пользователем 11 октября 2026 года.

**Статус:** реализация разрешена пользователем и завершена последовательным исполнением. M2 подтверждена. Фактические проверки и отклонения от тестовых шагов описаны в [отчёте](2026-10-11-day-7-rejections-events-revert-implementation-report.md). Отметки ниже обозначают закрытие требований; точные названия и группировка тестов могут отличаться.

## Общие ограничения

- Одна внешняя transaction и общая session; никаких savepoints, отдельного commit running, автоматического повторного исполнения всей mutation или второго repository-класса.
- READ COMMITTED; root lock удерживается до commit. Не добавлять конфликтующий WorkOrder lock после root. AOI/baseline/assignment неизменны в пределах одного вызова Save.
- Ordinary rejection неизменен, пока существует registry. Только access-rejected row с разрешённым флагом допускает resume.
- Новые expected rejections существующего target сохраняются; request/auth до use case и отсутствующий target не резервируют ID. Чужой занятый ID не перезаписывается.
- Старый `geom-v1` не менять. Формат существующей команды определяет алгоритм сравнения после ремонта baseline.
- No-op/replay/rejection не создают event и не повышают revision. Content change: ровно один event и revision +1.
- Revert восстанавливает точный baseline EWKB; response: `unchanged`, `hasPersistedChangeSet=false`, `basicValidation=null`.
- История обязательна только для новых команд Дня 7. Старые events не восстанавливать; старые данные не очищать.
- Нет нового endpoint, UI, workspace projection, dependencies, schema migration или изменения geometry policy. D5-Q1 о нулевых соседних сегментах сохраняется.
- DB tests только в isolated `geoservice-db-tests` / `geo_test`. Не применять destructive checks к demo-БД.
- Документация по-русски в `docs/sprint_2`; соблюдать `docs/agent-memory/patterns/2026-10-07-python-formatting-style.md`, включая SQL. Изменения unstaged; git add/commit/push запрещены.

## Особое внимание при ревью

1. Access rejection создан с contextless fingerprint, затем восстановлены и baseline, и доступ: resume не должен менять fingerprint или обойти domain validation — задача 3.
2. Новый payload, попавший по другую сторону границы округления при отличии меньше шага, должен дать reuse — задача 1.
3. Конкурентный владелец ID успел сохранить другой outcome, пока локально готовился отказ: проигравший не перезаписывает победителя — задача 5.
4. INSERT event уже выполнен, но commit падает: ни успешный ответ, ни snapshot/history не должны сохраниться — задачи 4–5.
5. Версия уже имеет revision 5 без events: новая mutation даёт только event 5 -> 6, а replay команды Дня 6 не делает backfill — задача 4.

## Файлы и зависимости

Пути ниже относительны `apps/backend`, кроме `docs/` и `infra/`.

| Файл | Изменение |
| --- | --- |
| `utility_service/domain_services/edit_geometry/contextless_fingerprint.py` | Новый чистый модуль нового fingerprint; старый алгоритм не переносить |
| `utility_service/domain_services/tests/test_contextless_fingerprint.py` | Новые equivalence/golden tests |
| `utility_service/infrastructure/postgresql/repositories/edit_version_commands.py` | Добавить reject/resume SQL helpers |
| `utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` | Reject/resume/event methods с root provenance |
| `utility_service/use_cases/schemas/edit_version/geometry_save_out.py` | Добавить frozen rejection outcome |
| `utility_service/use_cases/services/edit_version_save_identity.py` | Новый внутренний helper нормализации identity; без отдельного service-класса и persistence |
| `utility_service/use_cases/services/edit_version_service.py` | Outcome orchestration, ранние отказы, replay/resume, event |
| `utility_service/use_cases/tests/save_geometry_service_support.py` | Расширить fake transaction/repository вместе с первыми тестами |
| `utility_service/use_cases/tests/test_save_geometry_service.py` и `test_save_geometry_replay.py` | Обновить ожидания Дня 6 |
| `utility_service/use_cases/tests/test_save_geometry_rejections.py` | Новая матрица ранних отказов, identity и access retry |
| `tests/integration_tests/test_edit_version_command_repository.py` | Реальные transition/provenance tests |
| `tests/integration_tests/save_geometry_support.py` | Снимки command/history и fixtures без очистки demo |
| `tests/integration_tests/test_save_geometry_events.py` | Новые цепочки событий, Revert, старые revisions |
| `tests/integration_tests/test_save_geometry_rejections_integration.py` | Durable rejection/replay/repair/access на БД |
| `tests/integration_tests/test_save_geometry_atomicity.py` и `test_save_geometry_concurrency.py` | Fault injection и конкурентные outcomes |
| `docs/sprint_2/2026-10-11-day-7-rejections-events-revert-implementation-report.md` | Создать после реализации с фактическими результатами M2 |

Порядок: 1 → 2 → 3 → 4 → 5 → 6. Каждая задача содержит отдельный test cycle. Планирование не создаёт worktree; перед исполнением проверить текущий checkout и пользовательские изменения согласно применимым правилам.

## Команды проверки

PowerShell из корня репозитория. В test image исходники копируются при build: после изменения кода/тестов перед очередным запуском пересобирать image.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

Далее **U(path)** означает подстановку указанного в задаче backend-relative пути вместо `TEST_PATH`:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest TEST_PATH --tb=short
```

**D(path)** — то же для isolated DB tests:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest TEST_PATH --tb=short
```

RED означает падение конкретного assertion/отсутствие вводимого интерфейса; отсутствие Docker, network или dependency failure не является RED. GREEN означает exit 0 и выполненные проверки без пропуска обязательных DB tests.

## Задача 1. Contextless fingerprint

**Файлы:** новый domain module и его tests из таблицы. **Потребляет:** `FingerprintContext`, `GeometryPolicy`, `GeometryValue`, `quantize_ordinate`, `decimal_text`, `canonical_bytes`.

**Предоставляет:**

```python
def contextless_fingerprint_payload(context: FingerprintContext, policy: GeometryPolicy, geometry: GeometryValue) -> bytes
def contextless_command_fingerprint(context: FingerprintContext, policy: GeometryPolicy, geometry: GeometryValue) -> str
```

Envelope фиксируется здесь: `fingerprintVersion=1`, `identityMode="contextless"`, `commandType="replace_feature_geometry"`, ID-поля как у geom-v1; `baseline` содержит только `defaultStateId` и `networkRevision`; `draftVersionToken`; прежняя форма `geometryPolicy`; `geometryRepresentation="grid_aligned"`; полная округлённая `geometry`. Нет structureHash и vertexIndex. Выход: `geom-contextless-v1:sha256:<hex>`.

- [x] Написать `test_contextless_grid_equivalence`: при шаге `0.0000001` подстановка Decimal `65.52500001` вместо `65.525` даёт одинаковые payload bytes/hash; `1`, `1.0`, `1e0` равнозначны.
- [x] Написать `test_contextless_rounding_boundary`: `65.525000049` и `65.525000051` дают разные hashes, хотя расстояние меньше шага; проверить положительные и отрицательные midpoint.
- [x] Написать параметризованный identity test: изменение token, каждого ID, policy, count, порядка различимых координат и значимой geometry меняет hash. Golden fixture содержит точные expected bytes и SHA-256, рассчитанные независимо от тестируемой функции, а не вызовом той же функции в assertion.
- [x] Выполнить U(`utility_service/domain_services/tests/test_contextless_fingerprint.py`) и подтвердить RED.
- [x] Реализовать два интерфейса; использовать существующие Decimal/canonical JSON helpers, не читать current или baseline geometry.
- [x] Повторить U нового файла и U(`utility_service/domain_services/tests/test_geometry_fingerprint.py`); ожидать GREEN без изменения старых golden vectors.

## Задача 2. Registry: reject и resume

**Файлы:** command SQL helpers, основной repository, `test_edit_version_command_repository.py`. **Потребляет:** locked root, существующие command model/row и constraints.

**Предоставляет — методы `EditVersionRepository`:**

```python
async def reject_command(self, root: LockedEditVersion, *, command_id: UUID, status_code: int, code: str, message: str, retry_on_access_change: bool = False) -> None
async def resume_access_command(self, root: LockedEditVersion, *, command_id: UUID) -> None
```

SQL helpers в `edit_version_commands.py` имеют соответствующие имена `reject_running_command` и `resume_rejected_access_command`, принимают `session: AsyncSession`, `version_id: UUID` вместо root и возвращают bool совпадения UPDATE. Public repository проверяет root scope и превращает false в `RepositoryProtocolError`.

- [x] Добавить DB test `test_reject_and_replay_fields_are_durable`: reserve → reject → commit; новая session видит state/status/code/message/completed_at, payload NULL, без running.
- [x] Добавить `test_access_resume_transitions_and_rollback`: разрешён только rejected+flag; очистить result fields/flag/completed_at при running; identity/created_at прежние; rollback восстанавливает старый отказ.
- [x] Проверить запрет обычного rejection/success resume, чужого root/version, root другой transaction; нельзя перезаписать уже terminal row. Проверить deferred commit running.
- [x] Выполнить D(`tests/integration_tests/test_edit_version_command_repository.py`), подтвердить RED новых checks.
- [x] Реализовать conditional UPDATE с `RETURNING`, общую session и `no_autoflush`; rejected payload NULL; completed_at задаётся БД. Не менять schema/triggers.
- [x] Повторить D этого файла и D(`tests/integration_tests/test_first_save_command_constraints.py`), ожидать GREEN.

## Задача 3. Durable rejection, выбор identity и replay

**Файлы:** service, identity helper, result schema, use-case support/tests. **Потребляет:** задачи 1–2, старый `command_fingerprint`, context, request и normal geometry preparation.

**Предоставляет:** frozen `SaveGeometryRejection(status_code: int, code: str, message: str, retry_on_access_change: bool = False)` в `geometry_save_out.py`. Внешний `save_geometry()` сохраняет нынешнюю сигнатуру и success result/`WorkOrderApiError`. Внутренний `_save_geometry_locked()` возвращает union success/rejection; API-исключение только после commit.

В helper определить frozen `SaveGeometryIdentity(fingerprint: str, preparation_rejection: SaveGeometryRejection | None)` и:

```python
def build_save_geometry_identity(context: EditGeometryContext, *, actor_id: UUID, request: GeometrySaveRequest, stored_fingerprint: str | None = None) -> SaveGeometryIdentity
```

Helper не пишет в БД и не выдаёт repository handles. Читаемый, согласованный baseline позволяет geom-v1 даже для неeligible Point/короткой line: идентичность и eligibility разделены. Missing/invalid/inconsistent baseline выбирает contextless только для новой команды. Stored prefix принудительно выбирает прежний алгоритм; normal baseline недоступен → error context, неизвестный prefix → protocol error. Preparation rejection задаёт ранний отказ новой команды, но не заменяет matching replay.

- [x] Написать `test_rejection_is_raised_only_after_commit`: после `WorkOrderApiError` fake transaction committed, registry rejected; при commit failure вместо domain error выходит infrastructure error и row отсутствует.
- [x] Параметризовать stale, structure, invalid, outside AOI, multiple-feature, eligibility, context, role, lifecycle. Проверять точные status/code, unchanged snapshot/revision/history. Роль до use case и отсутствующий target не занимают ID; роль внутри use case при существующем target сохраняется.
- [x] Написать `test_repaired_baseline_keeps_contextless_rejection`: первый отказ, ремонт, exact/grid-equivalent retry дают прежние status/code/message, mutation count 0; новый token/значимая geometry дают reuse. Старый unmatched_structure сохраняет точное сравнение.
- [x] Написать `test_access_recovery_keeps_identity_and_revalidates`: доступ отсутствует, затем восстановлен; success либо stale по исходному token; retry flag очищен. Отдельный вариант — одновременно восстановлен baseline contextless-команды; fingerprint неизменен, domain validation выполняется.
- [x] Зафиксировать guards перед раскрытием чужого результата, early baseline/eligibility перед token, invalid перед AOI, обычный replay перед stale/domain validation; stored geom-v1 с нечитаемым baseline и неизвестный prefix не обходят identity.
- [x] Выполнить U(`utility_service/use_cases/tests/test_save_geometry_rejections.py`), подтвердить RED.
- [x] Реализовать helper и outcome orchestration. Ранние role/access/lifecycle outcomes запоминать, затем при существующем target идентифицировать и сохранять без раскрытия hidden context. Занятый ID никогда не переписывать; reservation conflict читает winner заново. Инфраструктурные исключения не ловить как domain rejection.
- [x] Обновить временные assertions Дня 6: stale/domain rollback становятся durable rejection; access-rejected после восстановления доступа возобновляется. Сохранить tests успешного replay, missing target, commit failure, original command immutability и disappeared winner.
- [x] Выполнить U для трёх файлов `test_save_geometry_service.py`, `test_save_geometry_replay.py`, `test_save_geometry_rejections.py` из `utility_service/use_cases/tests`; ожидать GREEN.

## Задача 4. Event persistence и Revert

**Файлы:** основной repository/service, unit support/tests, новый `test_save_geometry_events.py`, существующий `test_save_geometry_atomicity.py`.

**Предоставляет — метод repository:**

```python
async def append_change_event(self, root: LockedEditVersion, *, command_id: UUID, feature_id: UUID, actor_id: UUID, change: GeometryWriteResult, draft_revision_after: int) -> None
```

Метод требует живой root, `change.changed=True`, after revision = root revision +1. До INSERT проверяет несоответствие аргументов как protocol error. Event type из operation, geometry из before/after EWKB, provenance из root. Не требует consumed context handle. Вызов сервиса только после `complete_command`, до commit.

- [x] Написать `test_save_save_revert_event_chain`: три новых ID, baseline -> A -> B -> baseline; events имеют revisions 1->2, 2->3, 3->4 и persisted/persisted/cleared; actor/IDs/base revision точны.
- [x] Написать `test_noop_and_replay_do_not_append_events`: новые no-op на baseline/current плюс replay старого Revert после нового Save; current не откатывается, event count/revision неизменны.
- [x] Написать `test_old_revision_starts_new_history_without_backfill`: исходная revision 5, registry Дня 6 без events; новый Save создаёт только 5->6, старый replay не создаёт event.
- [x] Проверить off-grid baseline EWKB, `unchanged/false/null` Revert response и неизменность properties/associations/network versions.
- [x] Выполнить D(`tests/integration_tests/test_save_geometry_events.py`), подтвердить RED.
- [x] Реализовать event method и service call. Добавить fault injection после реального INSERT event; проверить rollback всего state и отсутствие premature success.
- [x] Обновить assertions snapshot Дня 6, ожидавшие отсутствие history; усилить их точным содержимым events. Обновить unit fake support; успешные unit сценарии учитывают events.
- [x] Выполнить D нового файла, D(`tests/integration_tests/test_save_geometry_atomicity.py`) и unit suites задачи 3; ожидать GREEN. В atomicity одновременно заменить старый DB-test отказов/resume на контракт задачи 3.

## Задача 5. Реальная долговечность и конкуренция

**Файлы:** DB rejection suite, atomicity/concurrency suites и общий support. **Потребляет:** полный production контракт задач 1–4; новых публичных production interfaces не добавляет.

- [x] Добавить DB matrix всех отказов существующего target и повтор из новой session/service. Assert сохранённые status/code/message, исходные geometry/revision/history, отсутствие running. Reuse проверять по неизменности original row, не требовать второй rejected row под тем же PK.
- [x] Добавить DB repair baseline scenario: убрать/повредить baseline поддерживаемым fixture способом, сохранить отказ, восстановить между transactions, повторить exact/grid-equivalent запрос; результат исходный. Нечитаемые EWKB, запрещённые PostGIS constraints, проверять unit-тестом, не отключать constraints ради фикстуры.
- [x] Добавить реальный access recovery с пригодным и непригодным baseline, stale после восстановления доступа, rollback после resume/finalization. Независимый snapshot видит прежний rejection при rollback.
- [x] Расширить faults: commit нового rejection и event transaction; использовать реальные deferred constraints для commit failure и test-only repository overrides для других фаз. После rollback тот же ID допускает новую попытку, если ранее durable row не было.
- [x] Добавить конкурентные identical rejected команды, success против другого payload с тем же ID, разные ID с одним token, один ID разных versions с commit/rollback победителя. Синхронизировать отдельные sessions по реальным locks/`pg_blocking_pids`, не по произвольным sleeps. Assert единственный winner, исходный terminal result, корректный event count, durable stale проигравшего по token.
- [x] Выполнить D(`tests/integration_tests/test_save_geometry_rejections_integration.py`) и D(`tests/integration_tests/test_save_geometry_concurrency.py`), проверить добавленные требования. Фактически эти acceptance tests проверяли уже реализованные интерфейсы; искусственный RED не создавался, см. отчёт.
- [x] Исправить только дефекты, обнаруженные этими проверками; сохранить Open/Save lock order, fresh actor/root reads и global reservation semantics.
- [x] Повторить обе suites и D(`tests/integration_tests/test_save_geometry_atomicity.py`); ожидать GREEN. Сохранить существующие history-after-registry-delete и Save/Open concurrency tests.

## Задача 6. Регрессия и передача результата

**Файлы:** необходимые исправления по проверкам, README Sprint 2 и будущий implementation report. **Предоставляет:** фактическое evidence M2, не новый функциональный интерфейс.

- [x] Проверить coverage M2-01–M2-24 по таблице ниже; добавить отсутствующие сценарии к owning suite до финального прогона.
- [x] Пересобрать test image и выполнить backend unit regression:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest --tb=short
```

- [x] Выполнить format/lint на текущем image:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps backend_db_tests python -m black --check .
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps backend_db_tests python -m ruff check .
```

- [x] Выполнить полный isolated DB runner `./infra/db-tests.cmd`; ожидать exit 0. Он удаляет только собственный disposable test project. Проверить по output, что обязательные DB suites выполнены, а не skipped.
- [x] Провести review по пяти focus cases, spec coverage и отсутствию scope drift; исправить findings и повторить затронутые проверки. Метод review определяется выбранным workflow исполнения; планирование само по себе не запускает агентов.
- [x] Создать implementation report: фактические команды/результаты, mapping M2 на tests, ограничения, изменения против плана. Не объявлять HTTP/UI/restart готовыми по unit/DB evidence.
- [x] Обновить README и статусы артефактов; выполнить `git diff --check`, проверить `git status --short`. Оставить изменения unstaged, без add/commit/push.
- [x] Оценить durable knowledge: не дублировать спецификацию в agent memory. Repository-change ingest вызывать только при появлении нового устойчивого знания сверх уже сохранённых документов, по правилам репозитория.

## Соответствие спецификации задачам

| Требование / M2 | Задачи |
| --- | --- |
| Старый/новый fingerprint, M2-06–08 | 1, 3, 5 |
| Atomic outcomes/registry, M2-04–05, 09–14, 23 | 2, 3, 5 |
| Event chain/Revert/no-op/replay, M2-01–03, 20–21 | 4 |
| Concurrency/fresh reads, M2-15–18 | 5 |
| Constraints/retention, M2-19, 24 | 2, 4, 5, 6 |
| Новая session/service, M2-22 | 5 |
| Полная регрессия, report и scope | 6 |

План проверен на покрытие спецификации, согласованность интерфейсов и зависимостей задач, тесты пяти focus cases и отсутствие commit-шагов. Исполнение завершено после прямого разрешения пользователя; результаты сохранены в отчёте реализации.
