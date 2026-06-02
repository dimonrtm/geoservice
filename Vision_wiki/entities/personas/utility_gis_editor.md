---
title: Utility GIS Editor
type: entity
status: draft
created: 2026-06-02
updated: 2026-06-02
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md"
tags: [persona, discovery, phase-f2, utility-network, authoritative-editing, research]
---

# Utility GIS Editor

## Статус

Primary research-persona GeoService после `/discover --phase Ф2`. Это модельная персона на основе документации существующих продуктов, а не подтвержденный реальный пользователь приложения.

## Роль

- Роль: GIS-редактор инженерной сети.
- Контекст: регулярная эксплуатационная работа utility-организации с authoritative network layer.
- Частота-гипотеза: ежедневно или еженедельно; для активной организации базовая гипотеза - ежедневно.
- Финальный контроль перед публикацией: reviewer.

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

## Связи

- [[../../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../../concepts/jtbd]]
- [[../../concepts/collaborative_editing_models]]
- [[../../solution/USM]]
- [[../../decisions/followups/index]]
