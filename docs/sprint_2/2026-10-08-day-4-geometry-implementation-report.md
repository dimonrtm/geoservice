# День 4: результат реализации

Дата: 8 октября 2026 года. Основание: [принятая спецификация](2026-10-08-day-4-geometry-design.md) и [план](2026-10-08-day-4-geometry-plan.md).

## Реализованный результат

Один и тот же запрос при одинаковых baseline, policy и контексте команды формирует одинаковые canonical geometry и `geom-v1:sha256` fingerprint. Текущая геометрия и настройки процесса не входят в fingerprint. Изменение `draftVersionToken`, actor, feature, WorkOrder/EditVersion или baseline меняет идентичность команды.

Чистое ядро `domain_services/edit_geometry` содержит frozen policy/value types, Decimal canonicalization, structure/transition guard и fingerprint. Сетка по умолчанию `0.0000001` градуса, midpoint округляется от нуля для обоих знаков. При совпадении клеток сетки возвращается точная исходная baseline ordinate, включая off-grid значения. Разрешены изменения X/Y одной внутренней вершины; endpoints и структура защищены. Переход с изменённой A на B требует отдельного Revert. No-op определяется относительно current, а operation — относительно baseline.

Raw JSON parser читает координаты непосредственно в Decimal, проверяет числовой token, exponent, диапазоны и форму запроса; отвергает дубли ключей, неизвестные поля, Z/M, нечисловые и неограниченные значения. DTO подготовлен для будущего Save use case. Сам PUT, command reservation/replay, AOI/spatial validation и интерфейс сохранения остаются последующими этапами.

Revision `c8e3f0a5b7d9` добавляет обязательную policy в `EditVersion`: точный NUMERIC, mode и version без постоянных defaults. CHECK и trigger защищают данные при прямом SQL. Backfill получает конфигурацию migrator, не зависит от JWT, сохраняет snapshot, revision и историю. Новая версия получает policy через DI; reopen сохраняет прежнюю policy даже после изменения настроек.

Feature projection существующего workspace использует EWKB hex вместо `ST_AsGeoJSON(..., 9)`. Codec сохраняет storage binary64 через `Decimal(repr(value))` и проверяет обратимость записи. Публичный GeoJSON остаётся числовым, количество SQL-запросов остаётся равным одному. AOI display projection не меняется.

## Проверки

Все команды выполнялись через backend Docker image. DB tests запускались только в `geoservice-db-tests`, база `geo_test`, отдельный PostGIS с tmpfs.

| Проверка | Результат перед финальным ревью |
| --- | --- |
| Полный pytest с `RUN_DB_TESTS=0` и read-only mount `infra` | 514 passed, 161 skipped |
| Полный `tests/integration_tests` на заново созданной БД | 172 passed, без skips |
| Black `--check .` | 275 файлов без изменений |
| Ruff `check .` | Все проверки прошли |
| `git diff --check` | Без ошибок |

Skips автономного прогона относятся к проверкам, требующим БД/окружения; изолированный DB-прогон выполнен отдельно. Два существующих предупреждения: deprecation `passlib/crypt` и Starlette `BlockingPortal`.

RED→GREEN подтверждён для policy/settings, canonicalization/guard, parser, golden fingerprint, schema/backfill, DI/lifecycle и codec/readback. HTTP regression отдельно воспроизвёл потерю `65.5200000499 → 65.52000005` на прежнем пути. После изменения GET возвращает исходные значения; Revert сохраняет EWKB, а canonical candidate проходит цепочку PostGIS → JSON → Decimal без изменения.

Расширенные проверки включают hostile Decimal context, независимый Fraction oracle, оба знака midpoint, grid с конечными нулями, numeric NaN/Infinity, immutable UPDATE с SQLSTATE/constraint name, populated migration и историю, rollback при неверной конфигурации, смену настроек между open/reopen, точные golden bytes/digest и порядок вершин.

Повторный полный DB-прогон поверх ранее committed fixtures обнаружил ограничение старой очистки cross-context tests: FK registry запрещает удалять feature. Для приёмки контейнер disposable БД пересоздан и весь набор выполнен заново. Перед повторным полным DB-прогоном требуется тот же reset тестового проекта; production constraints не ослаблялись.

## Решения при исполнении

- Использован текущий подходящий feature checkout `first-edit-save`, где уже лежали согласованные документы. Цена: изменения разделяют рабочее дерево с возможными будущими правками пользователя.
- POSIX bookkeeping заменён PowerShell и локальным Markdown ledger: Windows и запрет commits требуют учитывать unstaged diff. Цена: учёт шагов и evidence выполняется вручную.
- Для точного N/D используется `Decimal.as_integer_ratio`, затем изолированный Decimal context с рассчитанной precision и `ROUND_HALF_UP`. Это сохраняет согласованную семантику без сложного выравнивания exponent tuples; цена — integer arithmetic, проверенная независимым Fraction oracle.
- Завершение сохраняет изменения unstaged, согласно `AGENTS.md`. Коммиты, push и merge не выполняются; вспомогательный ledger сохраняется, поскольку история Git его не заменяет.

## Ревью и эксплуатация

Независимый ревьюер проверил unstaged diff и новые файлы по спецификации и пяти review-focus рискам. Вердикт: Ready — Yes. Critical/Important замечаний нет.

Оставлено одно Minor замечание: invalid configuration проверяет остановку migration до DDL; отдельного failure injection непосредственно в backfill UPDATE после добавления колонок нет. Ревью подтвердило корректную транзакционную границу Alembic. Это пробел дополнительного покрытия, а не обнаруженная ошибка production-кода; исправления в финальном проходе не требуются.

Границы, подтверждённые после ревью:

- Полный Save PUT, mutation/replay и UI остаются вне Дня 4; цена — полного пользовательского Save flow пока нет.
- Spatial validity/simple/AOI и пространственно некорректный current проверяются следующим этапом; цена — structure guard не доказывает пространственную допустимость.
- Online upgrade/downgrade проверены; `alembic --sql` не заявлен как поддержанный сценарий. Цена — offline SQL generation отдельно не проверен.
- Wiki/report проверены исполнителем, а не продуктовым ревьюером. Цена — документы не получили второй независимой проверки.

`repository-change` создал отдельную техническую ноду `Code_wiki/архитектура/edit_geometry_determinism.md` и обновил индекс/реестр. Wiki lint выявил только 37 прежних `missing_frontmatter` в неизменяемых RAW-файлах, новых ошибок в технической документации нет. RAW и общий live state не изменялись.

Перед применением schema требуется остановить старый API, выполнить migration с теми же geometry settings, затем запустить новый API. Downgrade удаляет policy snapshots. Подробности: [runbook](2026-10-08-day-4-geometry-runbook.md).

Устойчивые технические контракты отражаются в `Code_wiki`; отдельная agent-memory запись не требуется, поскольку причины и связи уже сохранены в спецификации, коде и этом отчёте.

Тестовый Compose-проект удалён после приёмки. Рабочие изменения остались unstaged; index пуст. Последняя проверка git diff --check прошла.
