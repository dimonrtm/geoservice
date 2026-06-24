# Release 2: контракт реализации конфликта геометрии/ассоциации v0.1

Дата: 2026-06-23
Статус: черновик контракта реализации
Расположение: `docs/release_2/geometry_association_conflict`

## Назначение

Этот контракт фиксирует первый инженерный контур Release 2
`geometry/association conflict`: слой поддержки решения перед `post`
поверх штатного процесса utility network.

Цель v0.1 - дать разработчику воспроизводимый контракт для демонстрации
разработчика (`developer demo`): канонический сценарий ассоциации между
`transformer`/`service-device`, пакет последствий (`consequence package`),
жесткие блокеры, sidecar для stale/pre-post, объект аудита (`audit object`),
метрики времени (`timing metrics`) и чеклист реальной проверки с
`Editor`/`Reviewer`.

## Границы

Release 2 работает вокруг цепочки:

```text
reconcile -> consequence package -> review decision -> pre-post check -> post
```

Входит:

- пакет последствий (`consequence package`) в режиме только чтения (`read-only`) после reconcile;
- схема пакета для `Base / Mine / Default`, diff геометрии, delta ассоциаций,
  состояние dirty/validation, согласованность трассировки и статус subnetwork;
- состояния решения `draft_package`, `ready_for_review`, `approved`,
  `blocked_post`, `stale`, `escalated`, `repeated_review`;
- разделение `approve package` / `can post`;
- жесткие блокеры и триггеры stale;
- объект аудита (`audit object`) и телеметрия запуска (`run`);
- канонические положительные/отрицательные demo-фикстуры;
- чеклист реальной проверки для `Editor`/`Reviewer`.

Не входит:

- новый topology engine;
- замена штатного редактора конфликтов (`conflict editor`);
- полный паритет с ArcGIS;
- полноценный in-product UI для редактирования конфликтов;
- очередь пакетной проверки (`batch review queue`) и маршрутизация SLA;
- промышленный hardening для on-prem развертывания;
- утверждения, что demo обеспечивает authoritative-safe `post`.

## Участники

| Участник | Роль в контракте |
|---|---|
| `Editor` | Разрешает конфликт (`conflict`) в штатном процессе редактирования, формирует обоснование (`rationale`) и открывает пакет (`package`). |
| `Reviewer` | Принимает решение по пакету изменений (`change package`): approve, return, escalate или block. |
| `Specialist` | Будущая роль эскалации для High/Critical; в v0.1 не реализуется как отдельный процесс. |
| `System` | Считает пакет, блокеры, актуальность (`freshness`), аудит и метрики времени (`timing metrics`). |

## Семантика Решений

`approve package` означает, что `Reviewer` согласен с пакетом последствий и
объяснением сетевого последствия.

`can post` означает, что:

- пакет не stale;
- состояние target/default не изменилось после reconcile/approval;
- жесткие блокеры отсутствуют;
- обязательные доказательства полны для уровня риска (`risk tier`);
- проверка pre-post прошла.

Эти состояния нельзя объединять. Пакет со статусом `approved` может стать stale или
`blocked_post` до фактического `post`.

## Машина Состояний

| Состояние | Значение | Выходы |
|---|---|---|
| `draft_package` | Пакет строится или пересчитывается. | `ready_for_review`, `blocked_post` |
| `ready_for_review` | Доказательства достаточно полные для проверки (`review`). | `approved`, `blocked_post`, `escalated` |
| `approved` | `Reviewer` утвердил пакет, но это не равно `can post`. | `stale`, `blocked_post`, `post_authorized` |
| `post_authorized` | Проверка pre-post подтвердила отсутствие блокеров. | `posted`, `stale`, `blocked_post` |
| `blocked_post` | Post запрещен жестким блокером (`hard blocker`). | `draft_package` после recompute/fix |
| `stale` | Утверждение/пакет потерял актуальность (`freshness`). | `repeated_review`, `draft_package` |
| `escalated` | Требуется решение `Specialist`/Data Owner. | будущий scope |
| `repeated_review` | Повторная проверка (`Review`) открыта после stale event с контекстом delta. | `approved`, `blocked_post`, `escalated` |
| `posted` | Штатный post завершен; v0.1 может хранить итог (`outcome`). | terminal |

## Схема пакета

Машиночитаемая схема: `appendices/schemas/package.schema.json`.

Минимальный пакет содержит:

- `packageId`, `scenarioId`, `versionIds`, `snapshotIds`;
- `workOrder`;
- `baseMineDefault`;
- `geometryDiff`;
- `associationDelta`;
- `dirtyAreaSnapshot`;
- `validationResult`;
- `traceResult`;
- `subnetworkStatus`;
- `riskTier`;
- `blockers`;
- `evidenceCompleteness`;
- `decisionRecommendation`;
- `freshness`.

Пример: `appendices/evidence-package.example.json`.

## Жесткие Блокеры

Абсолютный запрет независимо от агрегированных метрик:

- `UNRESOLVED_ASSOCIATION_DELTA`;
- `DIRTY_TRACE_PATH`;
- `TOPOLOGY_NOT_VALIDATED`;
- `INVALID_SUBNETWORK`;
- `UPDATE_SUBNETWORK_FAILED`;
- `STALE_APPROVAL`;
- `DEFAULT_CHANGED_AFTER_RECONCILE`;
- `MISSING_REQUIRED_EVIDENCE`;
- `UNEXPLAINED_TRACE_IMPACT`.

Один ложно-безопасный вердикт (`false-safe verdict`) в hard-block-сценарии проваливает developer demo.

## Триггеры Stale

Пакет или approval становится stale при:

- правке geometry в affected scope;
- правке association;
- изменении сетевого атрибута (`network attribute`);
- изменении конфигурации терминала (`terminal configuration`);
- изменении результата проверки (`validation result`);
- новом reconcile против изменившегося target/default;
- изменении состояния target/default после reconcile;
- изменении статуса subnetwork;
- изменении trace consistency/freshness;
- изменении blocker set.

Событие stale должно сохранять id предыдущего пакета, id нового пакета или
id запроса recompute, причину, источник actor/system и сводку delta.

## Объект аудита (Audit Object)

Машиночитаемая схема: `appendices/schemas/audit.schema.json`.

Аудит сохраняет доказательные поля, а не весь поток отладки (`debug stream`):

- `auditId`;
- `packageId`;
- `scenarioId`;
- `seedChecksum`;
- `sourceSnapshotIds`;
- `riskTier`;
- `blockers`;
- `traceConsistency`;
- `subnetworkStatus`;
- `evidenceCompleteness`;
- `actorRole`;
- `decision`;
- `timestamps`;
- `staleEvents`;
- `manualChecksCount`;
- `finalPostOutcome`;
- `technicalLogRef`.

Счетчики производительности, трассировки стека (`stack traces`) и подробные
поля отладки (`debug fields`) остаются в потоке observability/log.

## Метрики времени (Timing Metrics)

Машиночитаемая схема: `appendices/schemas/timing.schema.json`.

Первая демонстрация фиксирует:

- `packageBuildMs`;
- `evidenceLoadMs`;
- `staleInvalidationMs`;
- `auditSaveMs`;
- опционально `prePostCheckMs`.

Черновые пороги (`gates`) для developer demo:

| Метрика | Цель |
|---|---:|
| сводка пакета P95 | `<= 2000 ms` |
| детали пакета P95 | `<= 2500 ms` |
| ответ stale/block P95 | `<= 1000 ms` |
| подтверждение сохранения audit P95 | `<= 1000 ms` |
| доступность audit для чтения P95 | `<= 3000 ms` |

## Канонический Сценарий

Идентификатор канонического сценария: `r2-gac-transformer-terminal-001`.

Сценарий:

- линия среднего напряжения (`medium-voltage line`) содержит midspan tap;
- service transformer содержит high-side terminal;
- `Mine` меняет geometry/terminal association вокруг tap point;
- `Default` меняет конкурирующее представление geometry/association;
- пакет последствий должен показать, что визуально небольшой diff может
  влиять на интерпретацию connectivity/trace/subnetwork.

Манифест фикстуры: `appendices/fixture-manifest.yaml`.
Датасет сценария: `appendices/canonical-scenario-dataset.yaml`.
Снимки: `appendices/base-mine-default-snapshots.json`.

## Критерии прохождения/провала для Developer Demo

Критерии прохождения (`Pass`):

- пакет строится из фикстуры;
- полнота evidence для scenario;
- жесткие блокеры (`hard blockers`) находятся детерминированно;
- sidecar-компонент stale/pre-post помечает предыдущее approval как stale;
- счетчик false-safe verdict равен zero;
- объект аудита (`audit object`) содержит обязательные доказательные поля (`required proof fields`);
- метрики времени (`timing metrics`) сохраняются.

Критерии провала (`Fail`):

- пакет разрешает go/post при наличии любого absolute veto;
- stale approval продолжает выглядеть валидным (`valid`) после изменившегося target/default
  или changed affected evidence;
- пакет только дублирует `Current / Target / Common Ancestor` без network
  consequence;
- объект аудита (`audit object`) не поддерживает повторную проверку (`repeat review`).

## Допустимое утверждение (Claim)

Допустимо:

```text
В developer demo Release 2 собирает пакет последствий для конфликта utility
network, делает видимыми жесткие блокеры (`hard blockers`) и помогает сформировать
более обоснованное go/no-go решение перед post на синтетическом сценарии.
```

Недопустимо до реальной проверки:

- `Release 2 обеспечивает safe post`;
- `Release 2 снижает production errors`;
- `Release 2 заменяет Reviewer`;
- `Release 2 доказывает корректность authoritative state`.

## Приложения

- `appendices/fixture-manifest.yaml`
- `appendices/canonical-scenario-dataset.yaml`
- `appendices/base-mine-default-snapshots.json`
- `appendices/evidence-package.example.json`
- `appendices/decision-run.example.json`
- `appendices/schemas/package.schema.json`
- `appendices/schemas/audit.schema.json`
- `appendices/schemas/run.schema.json`
- `appendices/schemas/timing.schema.json`

## Открытые гипотезы для проверки

До реальных сессий (`sessions`) с `Editor`/`Reviewer` остаются гипотезами:

- точная калибровка (`calibration`) `Normal / High / Critical`;
- матрица полномочий (`authority matrix`) для High/Critical;
- примерная политика проверки (`sample review policy`) для `Normal`;
- пороги достаточности доказательств (`evidence sufficiency thresholds`);
- UX повторной проверки (`repeat-review UX`) и `delta since previous approval`;
- язык доверия (`language of trust`) и доверие к вердикту blocker.
