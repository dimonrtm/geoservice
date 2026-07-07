# Production-Like Baseline Для Alembic-Миграций

Дата: 2026-07-07
Статус: design approved
Источник: brainstorming по переписыванию destructive demo migrations перед production-like средой

## Контекст

Перед первой production-like средой миграционная цепочка backend должна перестать
нести demo-era cleanup и repair-логику. Целевая production-like БД стартует с
нуля. Старые локальные demo/dev Postgres volumes с уже примененными ревизиями не
являются поддерживаемым migration path и должны пересоздаваться.

Сейчас в Alembic history есть опасные для production-like поведения:

- `b82a5f2d91c3_editor_reviewer_roles.py` удаляет legacy/demo users при
  переходе от `viewer` к `reviewer`.
- `f2b3c4d5e6a7_sprint1_schema_boundaries.py` дропает legacy work-order,
  edit-version и AOI tables через cleanup-переход.
- `c9d0e1f2a3b4_repair_work_order_aoi_scope.py` чинит старые stamped volumes,
  создает fallback AOI и удаляет `utility_network.aois`.

Эти действия были допустимы для local demo, но перед production-like средой
`upgrade` не должен молча удалять данные или чинить неканонические dev volumes.

## Цели

- Сделать Alembic chain безопасной для clean production-like DB.
- Убрать destructive demo cleanup из `upgrade`.
- Сохранить reversible `downgrade` для CI migration-cycle tests.
- Сохранить существующий Alembic graph и revision ids там, где это снижает churn.
- Разделить schema migrations и demo seed data.
- Явно задокументировать, что старые dev/demo volumes пересоздаются.

## Не Цели

- Не поддерживать автоматический upgrade старых local dev/demo volumes.
- Не переносить пользовательские данные из старых demo-схем.
- Не вводить production data migration workflow для уже живой production БД.
- Не менять доменную модель ролей, WorkOrder, AOI или DefaultState вне
  необходимости очистки миграционной истории.
- Не запускать demo seed chain в production-safe startup.

## Выбранный Подход

Выбран подход: переписать цепочку в чистую reversible baseline.

`upgrade head` на пустой БД должен создавать текущую целевую схему без
промежуточного удаления legacy/demo данных. Ревизии, которые нужны только как
исторические checkpoints, становятся compatibility revisions: они сохраняют
место в Alembic graph, но не выполняют destructive действия.

`downgrade` остается поддержанным для тестов. При этом он удаляет только объекты,
созданные соответствующей миграцией или слоем миграций. Downgrade не является
production rollback strategy, но остается проверяемым инженерным контрактом.

## Миграционная Архитектура

`c6cef6320f1d_create_users.py` должен сразу создавать `user.users` в целевом
виде: роли `editor`/`reviewer`, поле `is_active`, без legacy `viewer`.

`b82a5f2d91c3_editor_reviewer_roles.py` должен перестать удалять пользователей.
Так как целевая модель ролей уже создана в baseline, ревизия становится
compatibility revision: `upgrade()` и `downgrade()` не меняют данные и не
перестраивают constraint.

`d3a01f4e9c21_network_model.py` должен создавать только актуальные объекты
`utility_network`: feeders, network features, network associations и связанные
constraints/indexes. Legacy `utility_network.aois` больше не создается.

`e4b7a9c2d5f8_work_orders.py` должен сразу создавать целевой work-order слой:
`work_order.aois`, `work_order.work_orders.aoi_id`, `fk_work_orders_aoi` и
`ix_work_orders_aoi_id`. Тогда отдельная repair-миграция AOI больше не нужна.

`a8c1f2d3e4b5_edit_versions.py` остается местом создания
`utility_network.network_states`, per-WorkOrder default-state tables и
`work_order.edit_versions`/edit slice tables.

`f2b3c4d5e6a7_sprint1_schema_boundaries.py` не должен дропать legacy work-order,
edit-version или default-state tables в `upgrade`. Так как все актуальные
schema-boundary объекты уже создаются в более ранних baseline migrations,
ревизия становится compatibility checkpoint: `upgrade()` и `downgrade()` не
удаляют и не создают таблицы.

`c9d0e1f2a3b4_repair_work_order_aoi_scope.py` должен стать no-op/compat
checkpoint. Fallback AOI и перенос из `utility_network.aois` уходят из
production-like migration path. Demo AOI остается ответственностью
`SeedWorkOrderService` и seed specs. `downgrade()` этой ревизии тоже остается
no-op.

Ревизии, которые реально создают текущие таблицы, индексы и constraints, должны
иметь симметричные downgrade-операции. Если миграция ничего не создает в
новом clean baseline path, ее downgrade тоже не должен удалять чужие объекты.

## Тестирование

DB integration tests должны проверять clean production-like chain:

- `upgrade head` с пустой БД создает все целевые schemas, tables, indexes и
  constraints.
- Migration-cycle tests продолжают выполнять `upgrade -> downgrade -> upgrade`,
  но больше не проверяют repair старых stamped volumes.
- Тесты не должны ожидать legacy `utility_network.aois` как переходное
  состояние.
- `test_schema_repair_migration_handles_stamped_boundary_without_aoi_id`
  удаляется, потому что stamped old-volume repair больше не является
  поддерживаемым поведением.

Нужен статический safety gate для Alembic versions:

- в `upgrade()` запрещены `DELETE`, `TRUNCATE`, destructive `DROP TABLE ... CASCADE`
  и перенос/удаление legacy data без явного allowlist;
- для этой задачи allowlist должен быть пустым;
- `downgrade()` может содержать `DROP`, но тест должен различать upgrade и
  downgrade paths.

Compose/startup tests остаются в текущей логике: production-safe startup не
запускает demo seed chain, demo compose может запускать seed runners после
migrations.

## Операционный Переход

Переход является breaking reset для локальных dev/demo БД до первого
production-like baseline. README, Code_wiki и runbook должны явно сказать:
старый Postgres volume нужно удалить и поднять чистую БД.

Если разработчик применит новую цепочку к старому volume, проект не обещает
автоматический repair. Предпочтительное поведение - ранняя понятная ошибка или
явная инструкция пересоздать volume, а не silent data rewrite.

Production-safe flow остается отделенным от demo flow:

1. Production-like среда получает clean DB.
2. `migrate` применяет Alembic migrations.
3. API стартует без demo seed chain.
4. Demo data создается только в demo/dev startup через seed runners.

## Документация

Нужно обновить:

- `README.md` - добавить предупреждение о reset старых local volumes.
- `Code_wiki/архитектура/data_model.md` - убрать описание `f2b3...` и `c9d0...`
  как repair/cleanup migrations для старых volumes.
- `Code_wiki/deployment/docker_compose.md` или runbook - уточнить clean DB
  expectation для production-like baseline.
- `Code_wiki/сборка/ci_and_quality.md` - обновить описание migration-cycle tests
  после удаления legacy repair сценариев.

## Последствия

Плюсы:

- `upgrade` становится безопаснее и понятнее для production-like среды.
- Demo data остается в seed layer, а не в schema migrations.
- CI сохраняет проверку reversible migrations без зависимости от старых volumes.
- Исторические revision ids можно сохранить без опасных data operations.

Компромиссы:

- Старые local volumes перестают быть поддерживаемыми и требуют пересоздания.
- Часть тестов и Code_wiki нужно переписать синхронно с миграциями.
- No-op compatibility revisions могут выглядеть непривычно, но они дешевле, чем
  полный squash Alembic history перед первым production-like запуском.

## Критерии Готовности

- На чистой PostgreSQL/PostGIS БД `alembic upgrade head` создает целевую схему.
- Migration-cycle tests проходят без legacy repair сценариев.
- В `upgrade()` миграций нет неразрешенных destructive data/table cleanup.
- Production-safe startup по-прежнему не запускает demo seed chain.
- Demo startup по-прежнему создает demo users, utility dataset и work order.
- README и Code_wiki явно говорят, что старые dev/demo volumes нужно пересоздать.
