---
title: Edit Version Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-11-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md; docs/planning/network-editor-backlog.md"
tags: [domain-knowledge, ddd, aggregate]
confidence: high
related: [Wiki/entities/edit_version, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/glossary/base_work_state, Wiki/policies/edit_geometry_precision_policy, Wiki/policies/positional_accuracy_acceptance_policy, Wiki/commands/update_edit_version_feature_geometry, Wiki/value_objects/draft_version_token, Wiki/value_objects/command_id, DDD_Wiki/invariants/edit_version_persisted_edit_invariants, DDD_Wiki/state_machines/edit_version_persisted_change_set, DDD_Wiki/state_machines/edit_version_save_request]
---

# Edit Version Aggregate

## Aggregate Root

`EditVersion` - root для изолированной рабочей копии features и associations.

## Consistency Boundary

В реализованном первом срезе рабочая версия уже сохраняет и возвращает геометрию выбранной линии. Исходный снимок, общий `DraftVersionToken` и регистрация `CommandId` защищают результат. Следующее расширение обобщает этот механизм на весь редактируемый набор. [Сверка реализованного среза](../../docs/verification/2026-11-09-model-health-code-reconciliation.md).

## Целевая модель полного редактора

Решение о направлении от 24.11.2026. Единица работы — рабочая версия наряда. Её исходный снимок содержит сеть на момент открытия. Редактор ведёт в ней несколько объектов и связывающих их записей. Постановка задач и сквозной пример — в [очереди редактора](../../docs/planning/network-editor-backlog.md).

| Данные | Идентичность и связи | Какое решение это позволяет принять |
| --- | --- | --- |
| Объект сети | Внутри версии устойчивый идентификатор представляет конкретный узел, участок или оборудование. Код используется для поиска и сверки, класс определяет геометрию и смысл свойств. | Исправление положения или атрибута сохраняет идентичность. При создании участка редактор указывает учётный код, а рабочая версия сохраняет идентификатор нового объекта. |
| Геометрия и свойства | Участок имеет упорядоченные координаты линии. Узел и оборудование имеют положение точки. Учитываются общие свойства и свойства класса, например напряжение участка и нормальное положение выключателя. | Можно изменить форму, концы, положение точки и учётную характеристику независимо. Состояние оборудования на дату наблюдения требует отдельного основания. |
| Связь сети | Собственный идентификатор, тип, ссылки на два объекта того же фидера. В рабочей версии допустимы ссылки на вновь созданные объекты этой версии. | Можно исправить ошибочный конец при корректных координатах, переназначить связь перед удалением объекта и отличить соединение от размещения или крепления. |
| Набор изменений | Для каждого объекта и каждой связи сопоставляются исходная и текущая записи. Общая ревизия рабочей версии и идентичность команды позволяют обнаружить конкурирующую запись и повтор. | Редактор видит все добавления, изменения и удаления и может отменять их выборочно с учётом зависимостей. Возврат геометрии одной линии сохраняет остальные правки, включая изменения атрибутов той же линии. |

### Правила для реализации в спринтах

- Исходная запись сохраняется для сравнения. Создание нового объекта и последующая отмена создания дают пустое итоговое отличие по нему. Изменение нескольких свойств существующего объекта даёт одно отличие с указанием затронутых полей. Удаление исходного объекта видно как удаление в составе рабочей версии.
- Линия сохраняет минимум две различные точки и допустимую геометрию. При вставке или удалении вершины сравниваются формы до и после. Из позиции в массиве координат нельзя вывести неизменную идентичность вершины после перестройки линии.
- Перед сохранением соединения оба конца должны существовать в допустимой области. Совпадение координат и перенос точки сами по себе не создают и не удаляют запись соединения. Связь с объектом, снятым с учёта в этой версии, требует явного разрешения до завершения удаления.
- Права редактора, границы наряда, неизменяемый исходный снимок и защита от потери изменений продолжают действовать для всех операций. Число уже исправленных линий или вершин не служит основанием отклонить следующую правку.
- Текущие таблицы рабочей версии уже различают объекты и связи. В спринте следует проверить их ограничения, чтение состава изменений и совместимость ранее сохранённых нарядов. Физическая схема, миграции и API относятся к реализации.

## Protected Invariants

Ниже записан контракт первого среза Save/Revert. Ограничения числа объектов, вершин и типов мутаций относятся к этой реализации. Целевое поведение для будущих спринтов определено выше.

- `baseNetworkRevision` неизменяем после создания.
- `baseNetworkRevision` / `BaselineRevisionRef` задаёт единое базовое состояние всей назначенной работы; feature-level `networkVersion` остаётся историей линии и не является отдельным baseline.
- Workspace features фильтруются по `WorkOrder.scope.aoi`.
- Associations включаются только когда присутствуют оба endpoint features.
- Непустой first-slice change set содержит geometry только одной существующей line feature во всей версии и отличается от baseline ровно одной внутренней вершиной. Resulting geometry, равная baseline, отдельно допустима как revert; endpoint move, изменение остальных координат, vertex insert/delete, split/merge, `part count` change, create/delete, attributes и association mutation запрещены.
- Resulting line валидна, проста и целиком `covered by` AOI; граница AOI допустима.
- `operation` является текущей проекцией diff относительно baseline и может вернуться в `unchanged`, если diff исчез.
- `DraftVersionToken` является version всего агрегата, выдается при read/open и меняется только на content-changing mutation; no-op/read/refresh его не меняют.
- `CommandId` обязателен: одинаковый id + canonical payload fingerprint присоединяется к одной operation и возвращает её состояние/результат, другой fingerprint с тем же id отклоняется. Операционный record живёт весь lifecycle `EditVersion`, переживает reconnect/relogin/device switch и запоминает domain rejection; долгосрочная append-only history хранится отдельно.
- После закрытия save context старый retry отклоняется и не трактуется как новая команда. Точный срок хранения immutable operation history остаётся открытым records-policy выбором.
- Stale token и hard-invariant failure отклоняют mutation атомарно; stale error возвращает актуальные persisted object и token.
- `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff; revert создает `EditVersionChangeSetCleared`; no-op и retry событий не создают.
- История каждого content-changing save хранит line identity, before/after geometry, editor, time, базовое состояние и `CommandId`; current diff является отдельной materialized projection.
- Draft summary/evidence могут жить рядом с `EditVersion` до submit; durable review snapshot создается позже в `ReviewPackage`.
- `POSITIONAL_ACCURACY_UNVERIFIED` допускается в technical working draft, но блокирует downstream review/completion/post; storage grid и positional acceptance остаются разными правилами.
