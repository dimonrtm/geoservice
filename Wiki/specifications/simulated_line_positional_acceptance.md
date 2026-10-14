---
title: Учебная позиционная приёмка линейной сети
type: specification
status: active
created: 2026-10-13
updated: 2026-10-13
source: RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md
tags: [domain-knowledge, simulated-organization]
confidence: high
related: [Wiki/policies/positional_accuracy_acceptance_policy, Wiki/specifications/edit_version_ready_for_review]
---

# Учебная позиционная приёмка линейной сети

## Predicate

SIM-UGIS-POS-001 v1.0 от 2026-10-13 принята агентом за условную организацию по прямому поручению пользователя. Scope — синтетические существующие 2D-линии между неизменными узлами; одна внутренняя вершина, без изменения endpoints/associations. Решение активно как правило модели, не как реализованная функция.

Для полного непрерывного соответствия эталонной и проверяемой линии по идентичным сегментам: max(e(s) + u(s)) <= 0,50 м по всей принимаемой области; 0 <= u(s) <= 0,10 м. e — расстояние соответствующих точек, u — консервативная граница неопределённости эталона. Это детерминированная учебная модель, не RMSE/доверительная вероятность/соответствие ASPRS.

## Inputs

Отдельно фиксированные эталон и candidate, identity/provenance/дата/метод/CRS, scope и bound u. Аналитический CRS SIM-LOCAL-M — декартова плоскость в метрах, не EPSG и не CRS существующего dataset. Для SRID 4326 нужен отдельно проверенный метрический/геодезический метод; storage grid не заменяет T.

## Пример SIM-EVID-001 v1

Синтетический объект SIM-LINE-01, дата 2026-10-13, аналитический эталон A=(0,0), B=(5.24,2.18), C=(10,0), u=0,05 м на всей линии. Candidate B=(5,2), концы те же. Соответствие по одинаковому параметру каждого прямого сегмента: ошибка на концах ноль, у B 0,30 м; линейность даёт max(e)=0,30 м на всей ломаной. Итог 0,35 <= 0,50 — учебный pass. Candidate B=(4.64,2.18) даёт 0,65 > 0,50 — fail. Нет evidence части сегмента — unverified.

Эталон отдельный от output Save и не получен из candidate; это независимость входов теста, а не натурная съёмка. Координаты не относятся к L-003. Пример не изменяет её, БД или статус точности.

## Failure Meaning

Недостаток применимого evidence/охвата/метода/допустимого u — UNVERIFIED. При достаточном evidence доказанное превышение T — EXCEEDED. Подтверждённая точка не подтверждает весь сегмент или линию. First-save остаётся UNVERIFIED; положительная аналитическая симуляция не разрешает review/post. Mapping к backend VERIFIED требует отдельного evaluator и проверки привязки evidence.

## Связи и пределы

[[Wiki/policies/positional_accuracy_acceptance_policy]] задаёт событийную переоценку; [[Wiki/specifications/edit_version_ready_for_review]] сохраняет все downstream gates. Топология остаётся отдельной проверкой. Веб-основание различения единиц: [PostGIS ST_Distance](https://postgis.net/docs/ST_Distance.html). Числовые пределы выбраны нами для эксперимента, не заимствованы из норм.
