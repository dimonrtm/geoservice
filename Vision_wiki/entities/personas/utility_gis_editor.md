---
title: Utility GIS Editor
type: entity
status: active
created: 2026-06-02
updated: 2026-06-12
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md; RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; RAW_inputs/meetings/utility_gis_editor_answers.md"
tags: [persona, discovery, phase-f2, utility-network, authoritative-editing, research, synthetic-evidence]
---

# Utility GIS Editor

## Статус

Primary design-persona GeoService. Синтетическая репетиция интервью принята владельцем проекта как подтверждение связности сценария для проектирования. Персона не подтверждена интервью или наблюдением реального пользователя.

## Роль

- Роль: GIS-редактор инженерной сети.
- Контекст: регулярная эксплуатационная работа utility-организации с authoritative network layer.
- Частота-гипотеза: ежедневно или еженедельно; для активной организации базовая гипотеза - ежедневно.
- Финальный контроль перед публикацией: reviewer.

## Уровень Evidence

- Подтверждено для проектирования: отдельная edit version, проверки connectivity/topology/trace, reconcile, review, post и сохранение lineage образуют связный workflow.
- Поддержано синтетическим сценарием: основной расход времени связан с разрозненными исходными материалами и повторным поднятием контекста.
- Не подтверждено внешне: частота задач, длительность 2-4 часа, конкретное распределение ролей и распространенность используемых инструментов.

## Рабочая Задача

Полевая бригада заменила старый трансформатор и переподключила отходящую линию. `Utility GIS editor` должен внести изменения так, чтобы сеть осталась корректной для трассировки, анализа аварий и downstream-систем.

## Рабочий Процесс

1. Получить work order с замененным оборудованием и измененными подключениями.
2. Создать named branch version, например `WO-2026-145-transformer-replace`.
3. Обновить линии, устройства, узлы, associations и связанные nonspatial objects.
4. Провалидировать topology и разобрать dirty areas.
5. Выполнить reconcile с `Default`.
6. Если есть конфликт, открыть `Conflicts view`, сравнить изменения и выбрать корректный результат.
7. Передать подготовленные изменения reviewer.
8. После подтверждения выполнить post в `Default` и повторно проверить сеть.

## Боли-Гипотезы

- Две бригады или два редактора меняют один участок сети или связанное оборудование.
- Другой редактор публикует изменения в `Default` до reconcile текущей версии.
- Один пользователь меняет геометрию или associations, а другой - атрибуты или статус того же объекта.
- После reconcile другой пользователь снова меняет `Default`, поэтому перед post требуется повторная сверка.
- Контекст изменения разорван между work order, PDF, фотографиями, Excel, справочниками и сообщениями.
- После возврата reviewer приходится восстанавливать контекст и повторять validation, trace и reconcile.
- Визуально корректная карта может скрывать ошибочную association и неверный trace.

## Приоритет Ущерба

1. Неверное состояние сети.
2. Потеря данных или части правок.
3. Ручная сверка.
4. Задержка публикации, если она предотвращает ошибку сети.

## Desired Outcome

- Reconcile выполнен, конфликты разобраны.
- Reviewer подтвердил корректность изменения.
- Post в `Default` завершен.
- Topology провалидирована, dirty areas закрыты.
- Trace и анализ сети возвращают ожидаемый результат.
- Рабочую версию можно закрыть или удалить.

## Synthetic Validation

Сценарий можно проверить без закрытых данных на synthetic utility-наборе: линии, устройства, associations, несколько dirty areas и конфликты `attribute vs attribute`, `geometry/association`, `edit after reconcile`.

## Канонический Язык

- Сохранение правки в `Edit version` не равно публикации в `Default`.
- Общий объект сети называется `Network feature`; непространственная связь - `Association`.
- Безопасный outcome включает validation, reconcile, conflict resolution, review, post и audit trail.
- Полный словарь и границы текущего demo описаны в [[../../concepts/utility_gis_editing_domain]].

## Связи

- [[../../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../../chats/2026-06-07-utility-gis-editor-domain-dictionary]]
- [[../../chats/2026-06-12-utility-gis-editor-synthetic-interview-rehearsal]]
- [[../../concepts/utility_gis_editing_domain]]
- [[../../concepts/jtbd]]
- [[../../concepts/collaborative_editing_models]]
- [[../../solution/USM]]
- [[../../decisions/followups/index]]
