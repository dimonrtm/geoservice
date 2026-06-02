---
title: Discover Ф2 - Пользователи И Боль
type: session
status: active
created: 2026-06-02
updated: 2026-06-02
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md"
tags: [discover, phase-f2, persona, jtbd, research]
---

# Discover Ф2 - Пользователи И Боль

## Контекст

Фаза Ф2 уточнила направление исследования GeoService после ingest `RAW_inputs/documents/Ф2.md`. Первый проход оставил два модельных архетипа для сравнения: `Utility GIS editor` и `Кадастровый инженер`. Второй проход выбрал `Utility GIS editor` как primary research-persona.

## Подтверждено Ответом Пользователя

- Primary research-persona: `Utility GIS editor`.
- Кадастровый инженер остается deferred research-сценарием: пользователь считает его более сложным для реализации.
- Все утверждения являются research-гипотезами на основе документации существующих продуктов. Заказчиков и реальных пользователей GeoService для интервью пока нет.
- Сценарий можно безопасно воспроизвести на synthetic utility dataset без закрытых данных.

## Research-Гипотезы

- `Utility GIS editor` получает work order на замену трансформатора и переподключение линии, создает named branch version, обновляет объекты сети, валидирует topology, выполняет reconcile и после review публикует изменения в `Default`.
- Главный ущерб для проверки - неверное состояние сети. Потеря данных, ручная сверка и задержка публикации вторичны.
- Базовый workflow обработки конфликта: `reconcile -> Conflicts view -> ручное разрешение -> topology validation -> review -> post`.
- Финальное содержательное решение перед публикацией принимает reviewer.
- Scope Release 1 не расширяется автоматически до branch versioning, reviewer workflow или topology validation: решение относится к Ф4.

## Не Подтверждено

- Подтверждаются ли модельные боли реальным рабочим опытом.
- Какие результаты даст synthetic pilot выбранного сценария.
- Какие capabilities должны войти в Release 1: этот вопрос относится к Ф4.

## Следующие Шаги

1. Подготовить synthetic utility dataset и проверить topology, `attribute vs attribute`, `geometry/association`, `edit after reconcile`.
2. Перейти к Ф3 и сравнить альтернативы в контексте utility authoritative editing.
3. На Ф4 решить, какие capabilities относятся к Release 1, а какие остаются Later.

## Связи

- [[../entities/personas/authoritative_gis_editing_candidates]]
- [[../entities/personas/utility_gis_editor]]
- [[../entities/personas/collaborative_editing_archetypes]]
- [[../concepts/jtbd]]
- [[../concepts/collaborative_editing_models]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/USM]]
