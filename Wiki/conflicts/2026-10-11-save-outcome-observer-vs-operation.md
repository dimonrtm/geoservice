---
title: Неизвестный исход для редактора и состояние операции
type: conflict
status: resolved
created: 2026-10-11
updated: 2026-10-12
source: "RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md; DDD_Wiki/state_machines/edit_version_save_request.md; docs/sprint_2/2026-10-11-day-7-rejections-events-revert-design.md"
tags: [domain-knowledge, conflict, recovery, idempotency]
confidence: high
related: [DDD_Wiki/state_machines/edit_version_save_request, DDD_Wiki/state_machines/editor_save_recovery, Wiki/value_objects/command_id, Wiki/policies/editor_recovery_policy]
---

# Неизвестный Исход Для Редактора И Состояние Операции

## Contradiction

Старая диаграмма `edit_version_save_request` относит `OutcomePending` к operation и связывает его с удержанием зарезервированного id после возможного начала commit. Принятая synchronous Save спецификация Sprint 2 описывает атомарный terminal result либо rollback; потеря ответа сама по себе не устанавливает наличие durable pending state.

Новый research предлагает явно отделить осведомлённость редактора от фактического состояния операции. Неясно, была ли старая диаграмма абстрактной моделью наблюдения или требованием дополнительного persisted состояния. Это расхождение описаний, не доказательство дефекта работающего кода.

## Blocks

Однозначную модель восстановления для ближайшего API/UI: нельзя механически переносить `OutcomePending` в новую таблицу или трактовать потерю ответа как подтверждённый отказ. Уже реализованный synchronous Save этим конфликтом не объявляется заблокированным.

## Evidence

- Старая [[DDD_Wiki/state_machines/edit_version_save_request]]: разделы `State Meaning` и диаграмма.
- `docs/sprint_2/2026-10-11-day-7-rejections-events-revert-design.md`: общая транзакция результата, rollback при инфраструктурной ошибке, replay.
- Ответы 8–10 нового RAW research и предложенная [[DDD_Wiki/state_machines/editor_save_recovery]].

## Resolution Question

Пользователь 2026-10-12 принял правила последнего исследования. `OutcomePending` трактуется как неопределённость наблюдателя; серверный synchronous terminal/rollback контракт сохраняется, нового durable статуса нет. Старая диаграмма и формулировки `CommandId` согласованы с решением.

## Next Action

Основание закрытия: [прямое решение пользователя](../../docs/sprint_2/2026-10-12-save-recovery-rules-decision.md). Реализация недостающего поведения API/UI запланирована отдельной [S2-X01](../../docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md) вне календарных дней. Закрытие конфликта не означает выполнение подзадачи.
