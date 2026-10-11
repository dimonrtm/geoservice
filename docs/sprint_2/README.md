# Sprint 2

В этой папке хранятся план, критерии приёмки и итоговые артефакты Sprint 2. Исторические материалы Sprint 1 не изменяются ради описания нового спринта.

## Артефакты

- [Анализ Дня 7: отклонения, события и Revert](2026-10-11-day-7-rejections-events-revert-analysis.md) — текущий код, ответы на вопросы, выбор подхода и согласованные разделы дизайна.
- [Спецификация Дня 7: terminal rejection, история и Revert](2026-10-11-day-7-rejections-events-revert-design.md) — транзакционный контракт, два формата fingerprint, access retry и матрица M2; принята 11 октября 2026 года.
- [План реализации Дня 7](2026-10-11-day-7-rejections-events-revert-plan.md) — шесть выполненных задач, интерфейсы и проверки M2.
- [Отчёт реализации Дня 7](2026-10-11-day-7-rejections-events-revert-implementation-report.md) — durable rejection, access retry, события, Revert и подтверждение M2.
- [Журнал исполнения Дня 7](2026-10-11-day-7-execution-ledger.md) — TDD evidence, review и решения при реализации.
- [Анализ Дня 6: synchronous Save и идемпотентность](2026-10-11-day-6-save-analysis.md) — текущий код, ограничения транзакции и согласованные уточнения требований.
- [Спецификация Дня 6: synchronous Save и идемпотентность](2026-10-11-day-6-save-design.md) — Save в EditVersionService, единый EditVersionRepository, reservation/replay, revision и проверки атомарности; принята 11 октября 2026 года.
- [План реализации Дня 6](2026-10-11-day-6-save-plan.md) — шесть выполненных задач с интерфейсами и проверками.

- [Отчёт реализации Дня 6](2026-10-11-day-6-save-implementation-report.md) — Save, replay, атомарность, конкуренция и полная регрессия.
- [Журнал исполнения Дня 6](2026-10-11-day-6-execution-ledger.md) — TDD evidence, исправление по review и решения при исполнении.

- [Анализ Дня 5: атомарный repository context](2026-10-09-day-5-repository-context-analysis.md) — факты текущего кода, принятые решения и временное правило D5-Q1.
- [Спецификация Дня 5: атомарный repository context](2026-10-10-day-5-repository-context-design.md) — контекст, блокировки, spatial validation, ограниченная запись и матрица M1; принята 10 октября 2026 года.
- [План реализации Дня 5](2026-10-10-day-5-repository-context-plan.md) — шесть выполненных задач с интерфейсами, тестами и командами проверки.
- [Отчёт реализации Дня 5](2026-10-10-day-5-repository-context-implementation-report.md) — EditVersionRepository, подтверждение M1, независимое review и открытое D5-Q1.
- [Журнал исполнения Дня 5](2026-10-10-day-5-execution-ledger.md) — TDD evidence и решения при реализации.

- [Календарный план](2026-07-31-sprint-2-calendar-plan.md) — работы и контрольные результаты на каждый день с 3 по 16 августа 2026 года.
- [Техническое задание](2026-07-31-sprint-2-technical-requirements.md) — человекочитаемое описание результата, правил, API, интерфейса и приёмки.
- [Спецификация Дня 2: схема первого сохранения](2026-10-01-day-2-first-save-schema-design.md) — принятый контракт revision, registry, истории и проверок.
- [План реализации Дня 2](2026-10-01-day-2-first-save-schema-plan.md) — выполненные задачи migration и SQL integration tests.
- [Отчёт реализации Дня 2](2026-10-01-day-2-first-save-schema-implementation-report.md) — изменения, результаты проверок и границы следующего этапа.
- [Анализ кода и обсуждение Дня 2](2026-10-01-day-2-schema-analysis.md) — основания решений, рассмотренные варианты и уточнения требований.
- [Анализ кода и обсуждение Дня 3](2026-10-06-day-3-model-schema-analysis.md) — расхождения ORM и migration, согласованные границы и матрица приёмки.
- [Спецификация Дня 3: соответствие моделей схеме](2026-10-06-day-3-model-schema-design.md) — модели registry/history, metadata parity, ORM integration, migration lifecycle и конкурентные проверки; принята 7 октября 2026 года.
- [План реализации Дня 3](2026-10-07-day-3-model-schema-plan.md) — пять выполненных задач с тестами и командами проверки.
- [Отчёт реализации Дня 3](2026-10-07-day-3-model-schema-implementation-report.md) — изменения, фактические результаты проверок и статус финального ревью.
- [Анализ кода и обсуждение Дня 4](2026-10-08-day-4-geometry-analysis.md) — текущее состояние canonicalization, structure guard и fingerprint, неоднозначности контракта и вопросы для уточнения.
- [Спецификация Дня 4: детерминированная геометрия](2026-10-08-day-4-geometry-design.md) — canonicalization, structure guard, fingerprint, policy и точный readback; принята 8 октября 2026 года.
- [План реализации Дня 4](2026-10-08-day-4-geometry-plan.md) — семь выполненных задач с интерфейсами, тестами и командами проверки.
- [Отчёт реализации Дня 4](2026-10-08-day-4-geometry-implementation-report.md) — реализованные правила, проверки и решения при исполнении.
- [Runbook geometry policy](2026-10-08-day-4-geometry-runbook.md) — backfill, миграция при остановленном API и последствия downgrade.
- `2026-08-16-sprint-2-acceptance-report.md` — будущий отчёт о фактической приёмке; создаётся после реализации и полного прогона сценария.

Все новые human-readable материалы этого спринта следует добавлять в `docs/sprint_2/` и писать на русском, сохраняя paths, commands, API names, types и identifiers без перевода.
