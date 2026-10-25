# Sprint 2

В этой папке хранятся план, критерии приёмки и итоговые артефакты Sprint 2. Исторические материалы Sprint 1 не изменяются ради описания нового спринта.

- [Анализ Дня 13: сквозная автоматическая проверка](2026-10-25-day-13-smoke-analysis.md) — сверка кода и модели, четыре уточнения пользователя; выбран подход расширения существующего API smoke и CI.
- [Спецификация Дня 13](2026-10-25-day-13-smoke-design.md) — принята пользователем; Save → restart → verify/retry/revert, отрицательные исходы и доказательство неизменности геометрии baseline L-003.
- [План реализации Дня 13](2026-10-25-day-13-smoke-plan.md) — пять задач выполнены; remote CI ожидает запуска после действий пользователя.
- [Отчёт реализации Дня 13](2026-10-25-day-13-smoke-implementation-report.md) — live fresh/restart smoke, suites, review и ограничения.
- [Runbook Дня 13](2026-10-25-day-13-smoke-runbook.md) — локальная изоляция, команды фаз, evidence и диагностика.
- [Журнал Дня 13](2026-10-25-day-13-execution-ledger.md) — RED→GREEN и решения исполнения.

- [Спецификация Дня 12: восстановление после сбоев](2026-10-20-day-12-recovery-design.md) — принята пользователем; retry/readback/stale/Revert, подтверждения и M4; Playwright принят отдельно.
- [План реализации Дня 12](2026-10-20-day-12-recovery-plan.md) — продуктовая часть и оба сценария M4 выполнены.
- [Анализ Дня 12: восстановление после сбоев](2026-10-20-day-12-recovery-analysis.md) — 16 согласованных ответов, сверка кода и модели, принятый подход и матрица M4; состояние реализации — в отчёте.

- [Отчёт реализации Дня 12](2026-10-20-day-12-recovery-implementation-report.md) — recovery actions, Revert, 287 frontend и 270 DB tests, browser evidence и M4.
- [Результат M4](2026-10-21-day-12-m4-report.md) — два объединённых сценария прошли; счётчики и доказательства отсутствия duplicate mutation.
- [Выбор инструмента M4](2026-10-21-day-12-m4-tool-options.md) — сравнение вариантов и отдельно принятое решение.
- [Журнал исполнения Дня 12](2026-10-21-day-12-execution-ledger.md) — RED→GREEN и исправление review.

- [Спецификация Дня 11: пользовательские команды](2026-10-18-day-11-user-commands-design.md) — принята пользователем 18 октября 2026 года; реализация отражена в отчёте.
- [План реализации Дня 11](2026-10-18-day-11-user-commands-plan.md) — пять последовательных задач; код реализован, настоящий browser zoom 200% остаётся непроверенным.
- [Отчёт реализации Дня 11](2026-10-18-day-11-user-commands-implementation-report.md) — панель, Save/Cancel, placeholder Revert, 271 tests, browser demo, responsive evidence и ограничения.
- [Журнал исполнения Дня 11](2026-10-18-day-11-execution-ledger.md) — RED→GREEN, решения исполнения и результаты review.
- [Анализ Дня 11 и ответы пользователя](2026-10-18-day-11-user-commands-analysis.md) — сверка текущего кода и модели, границы Save/Cancel/Revert, состояния и доступность.

- [Анализ и принятый дизайн Дня 10: взаимодействие с линией на карте](2026-10-17-day-10-map-interaction-analysis.md) — ответы пользователя, проверка текущего кода и Wiki/DDD_Wiki, технические ограничения и дизайн, принятый 17 октября 2026 года.
- [Отчёт реализации Дня 10](2026-10-17-day-10-map-interaction-implementation-report.md) — выбор, ограниченный drag, подтверждения, 230 frontend tests и ручная проверка demo со скриншотами.

## Подзадачи Вне Календарных Дней

- [S2-X01 — принятые правила восстановления сохранения](2026-10-12-s2-x01-save-recovery-followup.md) — реализовано и проверено поверх S2-06/07/08/09; подзадача вне дней, календарь не изменён.
- [Анализ S2-X01](2026-10-22-s2-x01-recovery-analysis.md) — сверка кода и доменной модели, 16 уточнений, выбор отдельного recovery store и согласование разделов дизайна.
- [Спецификация S2-X01](2026-10-23-s2-x01-recovery-design.md) — принята пользователем; независимое восстановление нарядов, IndexedDB, доступ, навигация и приёмка; реализована и проверена.
- [План реализации S2-X01](2026-10-23-s2-x01-recovery-plan.md) — девять выполненных задач с интерфейсами, проверками и уточнениями исполнения.
- [Решение о принятии правил](2026-10-12-save-recovery-rules-decision.md) — подтверждение пользователя от 2026-10-12, разрешение конфликта observer/operation и границы открытых организационных вопросов.

## Артефакты По Дням

- [Анализ Дня 9: frontend contracts и state](2026-10-14-day-9-frontend-state-analysis.md) — сверка frontend/backend и wiki, ответы на вопросы и согласование разделов дизайна.
- [Спецификация Дня 9: frontend contracts и state](2026-10-14-day-9-frontend-state-design.md) — local draft, pending command, canonical readback, sessionStorage и автоматические retry; принята пользователем 14 октября 2026 года.
- [План реализации Дня 9](2026-10-14-day-9-frontend-state-plan.md) — семь последовательных задач с интерфейсами и проверками; выполнен 15 октября 2026 года.

- [Анализ Дня 8: API и durable readback](2026-10-12-day-8-api-readback-analysis.md) — сверка кода, Wiki/DDD_Wiki и уточнения, включая сохранение parsing boundary Дня 4.
- [Спецификация Дня 8: API и durable readback](2026-10-12-day-8-api-readback-design.md) — расширение workspace и подключение Save API; принята пользователем 12 октября 2026 года.
- [План реализации Дня 8](2026-10-12-day-8-api-readback-plan.md) — шесть выполненных задач API/readback/OpenAPI.
- [Отчёт реализации Дня 8](2026-10-12-day-8-api-readback-implementation-report.md) — публичный PUT, согласованный workspace, полная регрессия и независимое review.
- [Журнал исполнения Дня 8](2026-10-12-day-8-execution-ledger.md) — TDD evidence, результаты проверок и решения при исполнении.

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

- [Отчёт реализации Дня 9](2026-10-15-day-9-frontend-state-implementation-report.md) — результат, матрица проверок и ограничения.
- [Журнал исполнения Дня 9](2026-10-15-day-9-execution-ledger.md) — решения исполнения и review.

- [Отчёт реализации S2-X01](2026-10-23-s2-x01-recovery-implementation-report.md) — независимое recovery, IndexedDB, навигация, сравнение; 323 frontend / 270 DB / 7 M4 проверок.
- [Журнал исполнения S2-X01](2026-10-23-s2-x01-execution-ledger.md) — решения, review и проверки.
