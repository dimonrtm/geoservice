---
title: Ответы об отзыве и коррекции публикации
type: research-summary
status: active
created: 2026-11-09
updated: 2026-11-09
source: RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md
tags: [research, utility-gis-editor, publication]
---

# Ответы об отзыве и коррекции публикации

## Контекст

Ответы DISC-2026-11-09-01/02 приняты агентом expert_repson за условную организацию по поручению пользователя. Общий корпус с исследованием — 88 документов. Это не интервью, независимый человеческий аудит или runtime-приёмка.

## Решения

Назначенный Editor отзывает точный пакет до допуска исполнения без согласия Reviewer. Отзыв упорядочивается с допуском post; уже допущенная попытка требует выяснения outcome, новые удерживаются. Withdrawn терминален, approval историческое; новая подача получает новый пакет и review.

После post изменение данных оформляется новым связанным WorkOrder с актуальным собственным baseline; исходный закрытый цикл сохраняется. Коррекция учитывает последующие изменения, не откатывает их старым snapshot. Evidence-only ветка выпускает новую редакцию и решение применимости. Закрытие разбора, публикация, доставка и приёмка различаются.

## Канонические связи

[[DDD_Wiki/use_cases/withdraw_review_package]], [[DDD_Wiki/use_cases/correct_published_result]], [[DDD_Wiki/aggregates/review_package]], [[Wiki/specifications/post_allowed]], [[DDD_Wiki/state_machines/work_order_lifecycle]]; [[Wiki/policies/review_package_withdrawal_policy]], [[Wiki/policies/published_result_correction_policy]], [[Wiki/specifications/published_result_correction_closed]].

## Конфликты и follow-up

Новых конфликтов и follow-up нет. FU-2026-10-13-004 включает будущую проверку исполнения этих правил; 15 сценариев RAW аналитические. First-save scope, baseline, CommandId, positional policy и retention неизменны. Два вопроса answered; следующий discover проверяет покрытие зависимых нарядов без заранее заданного числа вопросов.
