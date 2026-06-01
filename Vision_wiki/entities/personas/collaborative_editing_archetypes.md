---
title: Архетипы Пользователей Collaborative Editing
type: entity
status: draft
created: 2026-06-01
updated: 2026-06-01
source: RAW_inputs/documents/Ф2.md
tags: [persona, discovery, collaborative-editing, research]
---

# Архетипы Пользователей Collaborative Editing

## Статус

Это вымышленные, но реалистичные архетипы из research. Они помогают выбрать направление Ф2, но не являются подтвержденными персонами GeoService.

## Архетипы

| Архетип | Контекст | Основная Боль | Приоритет |
|---|---|---|---|
| Дежурный GIS-оператор | Инциденты и перекрытия в operational live-layer | Незаметная конкуренция за один feature, устаревший статус на dashboard | Скорость, простой UX, прозрачность изменений |
| Utility GIS editor | Эксплуатация инженерной сети | Конфликты authoritative state, риск неверного сетевого состояния | Контролируемый merge, review, audit trail |
| Кадастровый инженер | Parcel split/merge и lineage | Юридически значимые ошибки границ и истории изменений | Прослеживаемость, отсутствие потерь |
| Полевой инвентаризатор | Offline asset inventory | Sync conflicts, schema drift, ручная сверка данных | Надежный sync и простой мобильный UX |
| Полевой эколог | Мониторинг между QGIS и мобильной командой | Overwrite пакетов, плохие ключи, повторный выезд | Offline-устойчивость и понятный sync |
| Волонтер-маппер и validator | Массовое гуманитарное картирование | Overlap задач, upload conflicts, неоднородное качество | Task partitioning и validation |
| GIS-администратор тематического портала | Self-hosted web editing | Пересечение write-зон и недостаточный conflict UX | Контроль доступа, AOI scopes, on-premises |

## Неясно

- Какой архетип или их комбинация ближе всего к реальному рабочему контексту GeoService?
- Кто должен стать primary user для следующего прохода Ф2?

## Источники

- `RAW_inputs/documents/Ф2.md`

## Связи

- [[../../concepts/collaborative_editing_models]]
- [[../../chats/2026-06-01-phase-f2-collaborative-editing-research]]
- [[../../decisions/followups/index]]
- [[../../solution/USM]]
