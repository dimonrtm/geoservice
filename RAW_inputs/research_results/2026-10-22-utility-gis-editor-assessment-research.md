---
title: "Utility GIS Editor: выпуск, применимость и исправление заключений"
type: research
status: active
created: 2026-10-22
updated: 2026-10-22
source: RAW_inputs/documents/UtilityGisEditorRole.md
tags: [domain-knowledge, assessment, simulated-organization]
---

# Utility GIS Editor: выпуск, применимость и исправление заключений

## Задача и происхождение

Исследование выполнено 2026-10-22 по прямому запросу пользователя: углубить UseCase исходного UtilityGisEditorRole, использовать не менее 75 внешних источников, ответить на последние 15 discovery-вопросов, сохранить знания и выполнить ingest. Выбран ближайший незакрытый предметный участок: что происходит с оценкой сохранённой линии после её подготовки, передачи, изменения геометрии и обнаружения ошибки. Это продолжение исследования основания правки от 2026-10-19, а не повтор всего рынка GIS.

Режим условной организации установлен в `docs/agent-memory/decisions/2026-10-13-simulated-domain-organization.md`. Внешние документы описывают практики своих издателей; принятые правила GeoService — решения агента в роли `02_expert_oldman_ufa`. Здесь нет реального интервью, полевых измерений, аккредитации или производственной валидации.

**Корпус: 84 различных прочитанных внешних документа**: 26 по GIS/инженерным сетям, 25 по геодезии/качеству геоданных, 28 по оценке/происхождению/исправлениям и 5 дополнительных отраслевых документов. Оба результирующих файла используют один общий корпус из 84 документов; ответы не объявляются вторым независимым исследованием с ещё 84 источниками. Для каждого документа в реестре указаны вклад, прочитанный участок и ограничение.

## Метод поиска, отбора и новизны

Поиск шёл от конкретных проблем, а не от набора ссылок: `utility as constructed partial final revision`, `survey data lodgement acceptance`, `geospatial data release revisions`, `quality scope metaquality`, `report amendment withdrawal`, `analysis assurance validity`, `provenance version invalidation`. Использованы страницы владельцев сетей, транспортных ведомств, геодезических служб, авторов GIS-продуктов, государственных служб качества и организаций стандартизации. Для ILAC использована копия документа у национального органа аккредитации, с явным указанием издателя и ограничения.

Документы открывались; у длинных руководств читались релевантные разделы, а не заявлялось прочтение всего текста. Search snippets не считаются прочитанным источником. Разделы одного руководства OPUS, один PDF UNIDO и все вопросы EA FAQ считаются каждый одним документом. Разные самостоятельные USGS policies — отдельные документы, но одна институциональная семья, а не независимые голоса.

Сравнение URL со всеми более ранними `RAW_inputs/research_results/*.md`: **74 точных URL ранее не встречались**. После приведения hostname, удаления query/fragment и свёртки номера версии ArcGIS Pro отсутствуют 73 нормализованных адресов. Это показатели навигационной новизны, не число новых публикаций: иной URL/версия NIST TN1297 или Esri может вести к уже известному знанию. Новые предметные уточнения отдельно перечислены ниже. Реестр сохраняет исходные адреса для воспроизводимости.

Не включены в 84: U26 (краткая страница-аннотация California Energy Commission вместо полного отчёта), G09 Preserve и G26 Archiving (слишком общие для этой задачи), R04 GDOT resources (страница с указателем на checklist). Недоступные NUAR attachment, GDOT ZIP checklist, UKAS LAB13 и недоступное зеркало ILAC не считаются. Redirect FHWA PUS → sueindex не даёт второго документа. Пропуски в ID сохраняют аудит отбора.

## Что уточняется в исходном UseCase

Исходный RAW полезен как постановка роли: редактор приводит сведения о сети к согласованному представлению и передаёт результат дальше. Однако его внутренние `turn…` ссылки невоспроизводимы. Из этого исследования нельзя вывести доли рынка, частоту ошибок, экономию времени, готовность промышленной организации или универсальность конкретного workflow.

| Функция редактора | Уточнённый предметный смысл | Основание |
| --- | --- | --- |
| Получить материалы | Принять отдельные утверждения с датой, областью, методом и происхождением; поступление файла не равно принятию его качества | U08, U11, U24, R03 |
| Исправить карту | Различать геометрию, фактический актив, топологическое представление и сценарий расчёта | U01–U02, U16, U20–U21 |
| Проверить качество | Проверять нужное свойство для конкретной цели и состояния; точность хранения, качество GNSS и пригодность всей линии различны | U05, U07, U13, G18, R01 |
| Подготовить результат | Отделить вычисленный вывод от проверенного и выпущенного документа | G08, G12–G14, A11, U27 |
| Передать | Сохранять редакцию, ограничения и отдельные факты доставки/принятия обязанности/приёмки | U22–U25, R03, A05 |
| Исправить ошибку после передачи | Управлять применимостью зависимых утверждений, уведомлением и связанной новой редакцией | G10, A01, A12, A28 |

Версия редактирования не является самим заключением. Поздняя оценка S1 и текущая геометрия S2 могут сосуществовать. Также сосуществуют несколько качественных измерений: техническая допустимость записи, позиционное соответствие, достоверность основания, связность и пригодность для эксплуатации. Их нельзя складывать в один логический pass без определения цели.

## Новое доменное знание относительно текущей Wiki

| № | Уже сохранено | Новое уточнение из корпуса | Решение условной организации / следствие |
| --- | --- | --- | --- |
| N1 | Оценка привязана к сохранению | Выпуск документа и положительность результата — независимые свойства; provisional требует явности | Можно выдать отрицательное/непроверенное заключение, не завершая quality case (G13, A11, U27) |
| N2 | Есть ревизия основания | Ревизия самого заключения имеет причину и последствия использования, даже при неизменных данных | Исправлять по семантическому воздействию; хранить исходную редакцию и объяснение (G04, G07, G10) |
| N3 | Есть provenance | Воспроизводимость требует версии метода, параметров и цепочки преобразований, а не только ссылки на PDF | Искать затронутые заключения по зависимостям; неизвестные зависимости требуют разбора (G06, G11, G15) |
| N4 | Есть частичное evidence | Scope результата качества может отличаться от scope набора; доверие к оценке само нуждается в проверке | Частичный pass не закрывает всю линию; учитывать репрезентативность и общие зависимости (G22, G25) |
| N5 | Передача не равна approval | Отдельны доставка редакции, подтверждение ограничений, принятие обязанности и принятие для цели | Ручной журнал содержит четыре различимых факта, а не «принято» без смысла (R03, U25, A05) |
| N6 | Отзыв источника требует пересмотра | Предупреждение о существенной ошибке может предшествовать готовности заменяющего отчёта | Немедленный отдельный шаг ограничения применимости и уведомления известных адресатов (A01, A12) |
| N7 | Копии не независимы | Изменения должны доходить до получателей и повторяющихся представлений; неконтролируемые копии остаются риском | Реестр передач, ссылка состояния редакции, явный неизвестный остаток распространения (U22, A08, A17) |
| N8 | Координатные системы существенны | Одинаковые наблюдения могут дать иной результат при новой модели обработки; относительная и абсолютная неопределённость различны | Равенство XY не оживляет старый вывод; повторно проверить контекст (G15–G18) |
| N9 | Указаны роли Editor/Reviewer | Авторство, хранение данных и ответственность за новый выпуск могут переходить раздельно | Замещающий автор выпускает собственное мотивированное решение, без задней даты (G27, A11) |
| N10 | Краткий результат имеет ограничения | Выписка должна сохранять смысл метрики, scope и ссылку на применимую редакцию | Ограничения рядом с картой/числом; полная карточка доступна по стабильной ссылке (G14, G17, G21) |
| N11 | Топологическая проверка отдельна | Карта, проверенная топология и физическое состояние могут относиться к разным моментам; row conflict не ловит все смысловые конфликты | Не выводить эксплуатационную корректность из успешного Save/reconcile (U01, U14–U17) |
| N12 | Evidence должно соответствовать цели | Отраслевой quality level характеризует получение сведений; карты сами по себе не заменяют установление положения для работ | Критерий учебного положения не расширяется до разрешения раскопки или управления сетью (R01–R02, R06) |

Это новые уточнения принятой модели, а не утверждение, что все соответствующие идеи впервые появились в литературе. N11–N12 усиливают ранее принятую границу и не создают новые функции текущего среза.

## Глубокий разбор противоречий и исключений

**Идентичность утверждения.** Рабочая единица заключения — объект/состояние × участок × свойство × критерий × цель × evidence/метод × время. Совпадение одного измерения, например координат, недостаточно для замещения всего утверждения. Так объясняются одновременно история S1/S2, частичные исправления и две несопоставимые оценки. Это собственный синтез, а не новая схема таблиц или требование внедрить RDF.

**Неполнота и отрицание.** Нет данных по B — это unverified, а не fail B. Известный fail B для S1 не обязательно fail B для S2. Новый pass A не погашает B. Поэтому сводка обязана показывать границы результатов и несовпадение состояний; простое правило «последний отчёт главный» непригодно.

**Расхождение стандартных трактовок.** EA FAQ A28 прямо приводит разные позиции CASCO и EA относительно выделения изменений в полном заменяющем отчёте. Поэтому требование нашей организации всегда хранить причину и описание изменений принимается осознанно для воспроизводимости. Мы не объявляем его бесспорной универсальной нормой ISO/IEC 17025. Лабораторная практика A01 переносится как аналогия контроля заключений, без заявления, что GeoService — лаборатория.

**Применимость отраслевых практик.** Energex задаёт Partial/Final для выполненных групп работ/листов; эти обозначения не означают автоматически готовность всего проекта. Water Corporation, SA Water и другие владельцы имеют разные требования к методам/поставкам. Не переносим их числовые допуски, лицензии, сроки сдачи и организационные роли. USGS revision levels служат примером оценки воздействия, а не нашим обязательным пятиуровневым классификатором.

**Содержание против оформления.** Прошедший parser metadata, валидный XML, успешная загрузка или корректный checksum не доказывают пригодность для цели. Аналогично GPS receiver рядом с редактором не доказывает, что вручную смещённая точка получена GNSS. Отчёт должен объяснять происхождение вывода, а не только наличие технических артефактов.

**Граница институциональной независимости.** Многие документы USGS, W3C и Esri согласованы внутри одной семьи. 84 документа не означают 84 независимых эксперимента и не дают статистическую уверенность. Отдельный агентский проверочный проход уменьшает риск пропуска, но не моделирует независимую организацию или реальное peer review.

## Соотношение с кодом и прежними инвариантами

По текущим Code_wiki и отчёту M4: реализованы сохранение/возврат одной линии с одной внутренней вершиной, immutable baseline, command replay и current readback; frontend имеет Save/Revert и ручное recovery. Здесь runtime повторно не запускался и фактическая БД не исследовалась. Оценка evidence, выпуск/отзыв заключений, журнал доставки и полноценный review/post не объявляются реализованными.

SIM-UGIS-POS-001 сохраняется: полное соответствие непрерывных сегментов, Q=max(e+u), T=0.50 m, u≤0.10 m; при доказанных границах L≤Q≤U принятие при U≤T, отказ при L>T, иначе непроверено. Нельзя заменить это порогом конкретного utility, выборкой вершин, RMS GNSS или одной относительной погрешностью. First-save остаётся POSITIONAL_ACCURACY_UNVERIFIED; SIM-EVID не является полевым evidence L-003. Правила storage precision и SIM-UGIS-RET-001 неизменны.

Следующий допустимый шаг — ручная карточка и разбор сценариев из файла ответов. Отдельная реализация относится к FU-2026-10-13-004. Два metadata/fixture вопроса и S2-X01 не закрываются литературой. Новых blocking conflicts с принятой моделью не обнаружено; различия внешних процедур отражены как границы переноса, а не молча слиты в одну норму.

## Гипотезы, которые исследование не подтверждает

Удобство карточки, достаточность конкретного интерфейса выписки, скорость обнаружения downstream-зависимостей и полнота распространения исправлений неизвестны. Частота ошибок, эффективность принятой процедуры и производственная стоимость не измерялись. Корпус преимущественно англоязычный, из США, Великобритании, Австралии и Новой Зеландии; он не устанавливает российские или казахстанские юридические обязанности. Эти ограничения не мешают принять согласованные правила учебной организации.

## Покрытие вопросов источниками

- Q1: G13, A11, U27; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q2: A10, A17, G11; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q3: A21, G02, U01; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q4: G22, G25, U22; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q5: G12, A15, A13; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q6: G10, A28, G07; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q7: G06, G11, A13; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q8: G27, A11, A01; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q9: A10, G15, G16; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q10: G22, G25, A16; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q11: R03, U25, A05; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q12: R01, R02, A20; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q13: A01, A12, U22; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q14: A17, A08, U22; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].
- Q15: G14, G17, G21; ответ и пример — в [[RAW_inputs/research_results/2026-10-22-utility-gis-editor-assessment-answers]].

## Реестр прочитанных внешних документов

Дата доступа для всех: 2026-10-22. Дата публикации указана только при её установлении. «Новый URL» означает результат сравнения адресов, а не приоритет научного открытия.

### U01 — Network topology

- Документ: [Network topology](https://pro.arcgis.com/en/pro-app/3.5/help/data/utility-network/about-network-topology.htm); издатель: Esri.
- Дата/версия: не установлена; прочитано: Validate a network topology.
- Внешний факт: Топология отражает последнее enable/validate; карта после правок может отличаться от неё. Проверка не автоматическая и обрабатывает dirty areas.
- Граница: Описание продукта, не стандарт позиционной точности.
- Применение: Q1, Q2, Q4, Q9. Новизна: новый точный URL в прежнем RAW-корпусе.

### U02 — Get started with ArcGIS Utility Network for water

- Документ: [Get started with ArcGIS Utility Network for water](https://learn.arcgis.com/en/projects/get-started-with-arcgis-utility-network-for-water/); издатель: Esri.
- Дата/версия: не установлена; прочитано: Perform quality assurance.
- Внешний факт: Изменение Normal Status клапана создаёт dirty area, потому что это network attribute; до validate изменение не отражается в tracing.
- Граница: Учебный сценарий, не производственное измерение.
- Применение: Q2, Q3, Q7, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### U03 — Life Cycle Status

- Документ: [Life Cycle Status](https://resources.arcgis.com/en/help/data-reviewer-server/rest/lifecyclestatus.html); издатель: Esri.
- Дата/версия: не установлена; прочитано: Correction; Verification.
- Внешний факт: Исправление Resolved ещё требует Verification; Unacceptable возвращает результат в Review. Фиксируются исполнитель, дата и заметки коррекции.
- Граница: Историческая документация Data Reviewer; не предписывает модель GeoService.
- Применение: Q1, Q5, Q6, Q8, Q10. Новизна: новый точный URL в прежнем RAW-корпусе.

### U04 — Sync — ArcGIS Field Maps

- Документ: [Sync — ArcGIS Field Maps](https://doc.arcgis.com/en/field-maps/android/use-maps/sync.htm); издатель: Esri.
- Дата/версия: не установлена; прочитано: Tips; Sync work.
- Внешний факт: Полевые правки до sync существуют только на устройстве. Для hosted/nonversioned данных сохраняется последняя синхронизированная правка; versioned данные требуют reconcile/post.
- Граница: Транспортная синхронизация не доказывает содержательного принятия получателем.
- Применение: Q2, Q11, Q13, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U05 — The GPS Metadata Fields Are Empty When Creating Data in ArcGIS Field Maps

- Документ: [The GPS Metadata Fields Are Empty When Creating Data in ArcGIS Field Maps](https://support.esri.com/en-us/knowledge-base/problem-the-gps-metadata-fields-are-empty-when-creating-000032464); издатель: Esri.
- Дата/версия: не установлена; прочитано: Cause.
- Внешний факт: Ручное перемещение точки и snapping объясняют отсутствие GPS metadata при исправном GNSS. Происхождение координаты необходимо отличать от наличия подключённого приёмника.
- Граница: Конкретное поведение Field Maps; отсутствие metadata само по себе не доказывает ошибку координаты.
- Применение: Q3, Q6, Q9, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U06 — As constructed requirements

- Документ: [As constructed requirements](https://www.melbournewater.com.au/building-and-works/developer-guides-and-resources/standards-and-specifications/constructed); издатель: Melbourne Water.
- Дата/версия: 2021-08-04; прочитано: Land development reference 7.6.
- Внешний факт: Требуются survey control для аудита, CAD с as-constructed, PDF из этого CAD и цифровые сведения о центролиниях/сооружениях; заверенная бумага не заменяет цифровые файлы.
- Граница: Локальные требования Melbourne Water.
- Применение: Q3, Q11, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U07 — S551 Spatial Data Standard

- Документ: [S551 Spatial Data Standard](https://pw-cdn.watercorporation.com.au/-/media/watercorp/documents/about-us/suppliers-and-contractors/resources/design-standards/spatial-data-standards/s551-spatial-data-standard.pdf?hash=89BDD9F67400853882120EC1306E3239&rev=52ed8b38196e44cb970cada69fd4d06e); издатель: Water Corporation.
- Дата/версия: 2025-01-14 (print date); прочитано: p.4, 6.1–6.3.
- Внешний факт: Классы горизонтальной и вертикальной точности связаны с назначением съёмки; RTK/VRS запрещён для DGS-1/2. Требования мониторинга определяют исходя из нужных результатов.
- Граница: Не переносить численные допуски в GeoService как универсальную норму.
- Применение: Q3, Q5, Q7, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U08 — TS 0103 Survey Requirements Specification

- Документ: [TS 0103 Survey Requirements Specification](https://www.sawater.com.au/__data/assets/pdf_file/0010/199216/TS-0103-Survey-Requirements-Specification.pdf); издатель: SA Water.
- Дата/версия: 2019-06-30; прочитано: p.7–8 definitions.
- Внешний факт: Различаются local uncertainty относительно соседних пунктов и positional uncertainty относительно reference frame; для CRS нужны projection, datum и zone. Один project может иметь несколько submissions.
- Граница: Версия 2.00; проверены определения, не весь актуальный комплекс требований.
- Применение: Q3, Q4, Q5, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U09 — Survey Manual

- Документ: [Survey Manual](https://www.mrwa.com.au/sfsites/c/cms/delivery/media/MCBJMIALPLLTXTHFKXAGKZOEDRTY?channelId=0apMn00000001vN&language=en_US&version=11.1); издатель: Melbourne Retail Water Agencies.
- Дата/версия: не установлена; прочитано: Part 1 ch.1; ch.4 p.22–23 PDF.
- Внешний факт: Surveyor записывает горизонтальное/вертикальное положение, материалы и данные для сравнения с проектом. Water Company определяет стандарты, приёмку, quality management и audits.
- Граница: Содержит исторические разделы 1998/2000; не выдавать за новый норматив 2026.
- Применение: Q3, Q8, Q11, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U10 — Tips and Tricks for Your QGIS Project

- Документ: [Tips and Tricks for Your QGIS Project](https://github.com/opengisch/qfield-docs/blob/master/documentation/get-started/tutorials/tips-tricks-qfc.en.md); издатель: OPENGIS.ch / QField.
- Дата/версия: не установлена; прочитано: Managing Unique IDs; Modular File Structure.
- Внешний факт: Параллельный offline сбор с auto-increment IDs вызывает конфликты. Backup ведётся по файлам: восстановление одного слоя из общего GeoPackage откатывает корректные правки других слоёв.
- Граница: Рекомендация разработчика; timestamp ID не следует считать математической гарантией уникальности.
- Применение: Q2, Q7, Q9, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U11 — Prepare for high-accuracy data collection

- Документ: [Prepare for high-accuracy data collection](https://doc.arcgis.com/en/field-maps/latest/prepare-maps/high-accuracy-data-collection.htm); издатель: Esri.
- Дата/версия: не установлена; прочитано: Prepare your data; Supported GPS metadata.
- Внешний факт: GNSS metadata включает source, fix time/type, RMS accuracy, CRS/epoch/transformation; ручное обновление точки очищает GPS metadata. Для линий агрегаты включают worst accuracy и число ручных locations.
- Граница: Поля приёмника характеризуют процесс получения; не заменяют независимую оценку.
- Применение: Q3, Q4, Q9, Q10, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U12 — As constructed update of design plans

- Документ: [As constructed update of design plans](https://www.melbournewater.com.au/building-and-works/developer-guides-and-resources/standards-and-specifications/constructed-update); издатель: Melbourne Water.
- Дата/версия: не установлена; прочитано: Land development reference 7.8.
- Внешний факт: Исходные проектные детали нельзя удалять при аннотировании as-constructed; существенное изменение трассы требует новых полных планов.
- Граница: Локальный процесс чертежей; правила исправления assessment выводятся отдельно.
- Применение: Q6, Q9, Q13, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U13 — Surveying — preparation of drawings

- Документ: [Surveying — preparation of drawings](https://www.melbournewater.com.au/building-and-works/developer-guides-and-resources/standards-and-specifications/surveying); издатель: Melbourne Water.
- Дата/версия: 2021-08-04; прочитано: 7.20.3–7.20.4.
- Внешний факт: Для интеграции в GIS вершины нужны в характерных точках, переломах уклона/направления и центрах колодцев; требуется центролиния сооружений. Форматная точность хранения 1 мм не является точностью съёмки.
- Граница: Последняя фраза — вывод из разграничения формата хранения и требований съёмки.
- Применение: Q3, Q4, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U14 — Manage branch version conflicts

- Документ: [Manage branch version conflicts](https://pro.arcgis.com/en/pro-app/3.4/help/data/geodatabases/overview/manage-branch-version-conflicts.htm); издатель: Esri.
- Дата/версия: не установлена; прочитано: Field conflict filters; attribute rules; relationship classes.
- Внешний факт: Conflict filters исключают поля из обнаружения конфликтов; constraints и referential integrity проверяются при reconcile. Отсутствие конфликта зависит от настроенной политики сравнения.
- Граница: Продуктовая семантика, не полный тест совместимости доменных решений.
- Применение: Q2, Q5, Q7, Q9. Новизна: новый точный URL в прежнем RAW-корпусе.

### U15 — BUG-000185644

- Документ: [BUG-000185644](https://support.esri.com/en-us/bug/the-reconcile-versions-geoprocessing-tool-has-default-p-bug-000185644); издатель: Esri.
- Дата/версия: 2026-07-02 (last modified); прочитано: Description; Cause; Workaround.
- Внешний факт: Default PROCEED при reconcile мог автоматически разрешать ранее нерассмотренные конфликты и терять историю. Исправление меняет default; workaround — NOT_PROCEED.
- Граница: Конкретный опубликованный дефект; нельзя считать все версии одинаково затронутыми.
- Применение: Q2, Q7, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### U16 — Manage conflicts using conflict containers

- Документ: [Manage conflicts using conflict containers](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/manage-conflict-containers.html); издатель: Esri.
- Дата/версия: не установлена; прочитано: Introduction.
- Внешний факт: В telecom разные вставленные строки могут представлять один физический fiber/port; стандартное row-level сравнение не замечает логический конфликт группированных объектов.
- Граница: Специфично telecom; перенос на utility assessment является аналогией.
- Применение: Q2, Q4, Q7, Q9. Новизна: новый точный URL в прежнем RAW-корпусе.

### U17 — Reconcile Version

- Документ: [Reconcile Version](https://developers.arcgis.com/rest/services-reference/enterprise/reconcile-version/); издатель: Esri.
- Дата/версия: не установлена; прочитано: Description; request parameters.
- Внешний факт: Reconcile Version с withPost получает shared lock target между reconcile и post; checkOnly только проверяет необходимость reconcile без публикации.
- Граница: Документ REST operation LRS; не смешивать автоматически с поведением всех branch API.
- Применение: Q1, Q2, Q11. Новизна: новый точный URL в прежнем RAW-корпусе.

### U18 — General Tools — Metadata

- Документ: [General Tools — Metadata](https://docs.qgis.org/testing/en/docs/user_manual/introduction/general_tools.html); издатель: QGIS.
- Дата/версия: не установлена; прочитано: Metadata, lines 962–989.
- Внешний факт: Metadata хранит ограничения доступа, пространственный/временной extent, владельца, ссылки и историю. Предупреждения Validation можно игнорировать; metadata сохраняются в проекте/отдельно/источнике.
- Граница: Testing manual; наличие формы не обеспечивает обязательности metadata.
- Применение: Q4, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U19 — QGIS Dataset QA Workbench User guide

- Документ: [QGIS Dataset QA Workbench User guide](https://kartoza.github.io/qgis_dataset_qa_workbench/user-guide/); издатель: Kartoza.
- Дата/версия: не установлена; прочитано: Choose checklist; Add validation report.
- Внешний факт: Checklist выбирается по типу dataset и артефакту dataset/metadata/style. Отчёт можно добавить в metadata с timestamp и общим результатом; предыдущие отчёты остаются.
- Граница: Плагин, не общий стандарт QGIS; хранение в Abstract не равно неизменяемому аудиту.
- Применение: Q1, Q4, Q5, Q6, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U20 — Topological and Geometrical Adjustments — Giswater Toolbox

- Документ: [Topological and Geometrical Adjustments — Giswater Toolbox](https://giswater.gitbook.io/giswater-manual/7.-topological-and-geometrical-adjustments-giswater-toolbox); издатель: Giswater.
- Дата/версия: не установлена; прочитано: Chapter 7.
- Внешний факт: Для гидравлической модели недостающие высоты могут заполняться DEM/interpolation/extrapolation; исправленные уклоны можно хранить как customer data без изменения inventory.
- Граница: Модельные поправки не являются повторным полевым измерением.
- Применение: Q3, Q5, Q6, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U21 — Work environment

- Документ: [Work environment](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/work-environment.html); издатель: Giswater.
- Дата/версия: не установлена; прочитано: 6.3.2; 6.3.7.
- Внешний факт: Flow tracing требует непрерывности и направления оцифровки по потоку; audit module регистрирует изменения и даёт доступ к истории состояния сети.
- Граница: Описание возможностей продукта, без доказательства производственной эффективности.
- Применение: Q2, Q3, Q9, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U22 — Standard for As Constructed Drawing

- Документ: [Standard for As Constructed Drawing](https://www.energex.com.au/__data/assets/pdf_file/0003/1095960/Standard-for-As-Constructed-Drawing-2597742.pdf); издатель: Energex.
- Дата/версия: 2026-02-06 (release 12); прочитано: 5.1.2–5.7; PDF p.9–12.
- Внешний факт: Изменения выданного worksplan доводятся до всех workgroups; значительные требуют revision/reissue. Partial сдаётся по выполненным работам/листам, каждый лист подписан и помечен Partial/Final. Правки вносятся во все повторения сведений, включая схемы.
- Граница: Не копировать сроки оператора как универсальные; подтверждение рассылки не равно принятию содержания.
- Применение: Q1, Q4, Q6, Q10, Q11, Q13, Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U23 — ADAC As-Constructed Information

- Документ: [ADAC As-Constructed Information](https://www.ipswich.qld.gov.au/Services/Planning-and-Building/Development-Assessment/Operational-Works-and-Construction/ADAC-As-Design-As-Constructed-As-Constructed-Information); издатель: Ipswich City Council.
- Дата/версия: не установлена; прочитано: As-Constructed package; Drawings.
- Внешний факт: Пакет включает redlined утверждённые планы, чистые DWG/PDF и ADAC XML, точно согласованный с чистым планом; revision title block фиксирует as-constructed версию.
- Граница: Муниципальная схема приёмки; не универсальный формат GeoService.
- Применение: Q6, Q11, Q13, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U24 — As constructed data standards and guidelines

- Документ: [As constructed data standards and guidelines](https://www.moretonbay.qld.gov.au/Services/Building-Development/DA-Process/ADAC); издатель: City of Moreton Bay.
- Дата/версия: не установлена; прочитано: ADAC Specification.
- Внешний факт: Данные съёмки преобразуются по ADAC XML schema и затем загружаются в системы council для validation и acceptance; включает stormwater, water и sewerage.
- Граница: Форматная передача и окончательная приёмка различены; детали acceptance здесь не раскрыты.
- Применение: Q1, Q11, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U25 — Construction Surveying Guideline

- Документ: [Construction Surveying Guideline](https://www.mainroads.wa.gov.au/technical-commercial/technical-library/surveying-and-geospatial-services/engineering-surveys-guidelines/construction-surveying-guideline/); издатель: Main Roads Western Australia.
- Дата/версия: не установлена; прочитано: 4.4–4.7; 5.1.1.
- Внешний факт: Документируются назначение raw files, контролируемая выдача, метод/точность для этапа. Отчёт содержит compliance каждого sample point; receipt clearing data подтверждается по требованию, отдельно от проверки допустимой области.
- Граница: Дорожная инженерия; аналогия для передачи utility assessment.
- Применение: Q3, Q4, Q8, Q10, Q11, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### U27 — Data Lodgement Guideline

- Документ: [Data Lodgement Guideline](https://www.mainroads.wa.gov.au/technical-commercial/technical-library/surveying-and-geospatial-services/data-management-guidelines/data-lodgement-guideline/); издатель: Main Roads Western Australia.
- Дата/версия: не установлена; прочитано: Scope; 7 Design Reports; 14 Design Drawings.
- Внешний факт: Реестр reports включает тип, project, участок, Final/Draft, дату и автора. Реестр drawings включает номер и revision; передача идёт через project manager в ответственные хранилища.
- Граница: Процесс иной отрасли; не задаёт гарантию нахождения неизвестных downstream recipients.
- Применение: Q1, Q11, Q13, Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G01 — Metadata Creation

- Документ: [Metadata Creation](https://www.usgs.gov/data-management/metadata-creation); издатель: USGS.
- Дата/версия: не установлена; прочитано: Best Practices, Validating Metadata Records.
- Внешний факт: При изменении metadata обновляется дата записи; проверка структуры не исчерпывает содержательную оценку. DOI набора и DOI связанной публикации располагаются в разных элементах.
- Граница: Рекомендации USGS; не формат обязательной выписки GeoService.
- Применение: Q6, Q15. Новизна: URL уже использовался; прочитан повторно.

### G02 — Frequently Asked Questions about Positional Accuracy Elements

- Документ: [Frequently Asked Questions about Positional Accuracy Elements](https://www.fgdc.gov/csdgmgraphical/dataq/posaccfq.htm); издатель: FGDC.
- Дата/версия: не установлена; прочитано: lines 0–24.
- Внешний факт: Числовая сводка не освобождает от полного отчёта о методе и результатах. Точность описывается после преобразований; локальные вариации показываются по объектам или overlay. Одного заявления о прохождении порога недостаточно.
- Граница: Историческое пояснение CSDGM/SDTS, не замена нашему непрерывному критерию.
- Применение: Q3, Q4, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G03 — About OPUS

- Документ: [About OPUS](https://www.ngs.noaa.gov/OPUS/about.jsp); издатель: NOAA NGS.
- Дата/версия: не установлена; прочитано: OPUS Accuracy, Improving results, Solution Formats.
- Внешний факт: Формальные оценки точности могут быть оптимистичны и не обнаруживают ошибку выбора антенны/высоты. Независимое повторение с другим оборудованием/наблюдателем повышает уверенность. Отчёт фиксирует software, ephemeris, исходный файл и период.
- Граница: GNSS-точки; сантиметровые рекомендации не переносим на линейную приёмку.
- Применение: Q3, Q5, Q7, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G04 — Data Release Revisions

- Документ: [Data Release Revisions](https://www.usgs.gov/sciencebase-instructions-and-documentation/data-release-revisions); издатель: USGS ScienceBase.
- Дата/версия: не установлена; прочитано: steps 1–9, Wrong file upload.
- Внешний факт: Уровень исправления определяется влиянием на использование; сохраняют прежние data/metadata, историю, доступ к старым версиям и согласование. Ошибочная загрузка уже проверенного файла отличается от изменения самих данных.
- Граница: Процедура ScienceBase; не предполагает автоматического знания всех получателей.
- Применение: Q6, Q7, Q13, Q14. Новизна: новый точный URL в прежнем RAW-корпусе.

### G05 — Process

- Документ: [Process](https://www.usgs.gov/data-management/process); издатель: USGS.
- Дата/версия: не установлена; прочитано: Subsetting, Process Documentation, Best Practices.
- Внешний факт: Выделение подмножества — отдельная операция обработки; история должна описывать последовательность действий, требования и даты. Сохранение входов и review кода повышают воспроизводимость результата.
- Граница: Общие практики управления научными данными.
- Применение: Q4, Q7, Q10, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G06 — How do Source Citation Abbreviation and Source Used Citation Abbreviation work?

- Документ: [How do Source Citation Abbreviation and Source Used Citation Abbreviation work?](https://www.fgdc.gov/csdgmgraphical/dataq/lineage/faq.htm); издатель: FGDC.
- Дата/версия: не установлена; прочитано: complete FAQ.
- Внешний факт: Источники получают уникальные идентификаторы и связываются с шагами обработки; промежуточный результат может стать отдельным источником. При смешении источников происхождение прослеживается до элемента. Для преобразования фиксируются конкретные параметры.
- Граница: Историческое пояснение; происхождение не доказывает истинность.
- Применение: Q5, Q7, Q9, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G07 — How are USGS publication series products revised or superseded? FAQ 082

- Документ: [How are USGS publication series products revised or superseded? FAQ 082](https://www.usgs.gov/office-of-science-quality-and-integrity/fundamental-science-practices/faq/082-updating-revising-usgs-series-products); издатель: USGS.
- Дата/версия: не установлена; прочитано: Revising/Superseding.
- Внешний факт: Исправление ошибки и замена расширенным продуктом различаются. При superseding страницы старого и нового продукта взаимно ссылаются, доступ к прежнему опубликованному продукту сохраняется.
- Граница: Научные публикации, не тот же процесс, что data release.
- Применение: Q6, Q13, Q14. Новизна: новый точный URL в прежнем RAW-корпусе.

### G08 — Metadata Review

- Документ: [Metadata Review](https://www.usgs.gov/data-management/metadata-review); издатель: USGS.
- Дата/версия: 2021-06-21; прочитано: Content Metadata Review, Sample workflow.
- Внешний факт: Успех parser не гарантирует качество и пригодность metadata; содержательное review сопоставляет данные с описанием. Проверку можно распределить по компетенциям, замечания и их разрешение сохраняются; рекомендована повторная проверка исправлений.
- Граница: Дата обновления страницы 2021-06-21; конкретные инструменты необязательны.
- Применение: Q3, Q5, Q8, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G10 — Guidance on Documenting Revisions to USGS Scientific Digital Data Releases

- Документ: [Guidance on Documenting Revisions to USGS Scientific Digital Data Releases](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data); издатель: USGS OSQI.
- Дата/версия: 2023-09; прочитано: Levels 1–5, Preserving Withdrawn Versions, revision table.
- Внешний факт: Уровень пересмотра зависит от влияния на использование. Level 1 не меняет смысл; структурные изменения выделены отдельно. Существенная ошибка может потребовать withdrawal и нового release. История, прежние версии и tombstone обрабатываются по выбранному уровню; это не универсальная обязанность публиковать все старые данные.
- Граница: Редакция September 2023; уровни — USGS, а не автоматически принятая шкала GeoService.
- Применение: Q6, Q7, Q13, Q14. Новизна: URL уже использовался; прочитан повторно.

### G11 — Workflow Capture

- Документ: [Workflow Capture](https://www.usgs.gov/data-management/workflow-capture); издатель: USGS.
- Дата/версия: не установлена; прочитано: Formal Workflows, Best Practices.
- Внешний факт: Воспроизводимый workflow фиксирует входы, выходы, параметры, зависимости и каждый шаг анализа; описание метода создаётся при обработке, а не восстанавливается лишь по итоговой цифре.
- Граница: Это практика документирования, не доказательство корректности метода.
- Применение: Q5, Q7, Q8, Q9, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G12 — 502.4 Fundamental Science Practices: Review, Approval, and Release of USGS Scientific Information Products

- Документ: [502.4 Fundamental Science Practices: Review, Approval, and Release of USGS Scientific Information Products](https://www.usgs.gov/survey-manual/5024-fundamental-science-practices-review-approval-and-release-usgs-scientific); издатель: USGS.
- Дата/версия: не установлена; прочитано: sections 4,5,7G.
- Внешний факт: Проверка metadata, peer review, policy review и approval решают разные задачи. Автор письменно отвечает на существенные замечания, reconciliation хранится; существенные изменения после approval требуют оценки необходимости нового approval.
- Граница: Ведомственная политика USGS; не предписывает GeoService должности и иерархию.
- Применение: Q1, Q3, Q5, Q11, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### G13 — 502.8 Fundamental Science Practices: Review and Approval of Scientific Data for Release

- Документ: [502.8 Fundamental Science Practices: Review and Approval of Scientific Data for Release](https://www.usgs.gov/survey-manual/5028-fundamental-science-practices-review-and-approval-scientific-data-release); издатель: USGS.
- Дата/версия: 2017-01-13; прочитано: sections 4–6.
- Внешний факт: Preliminary/provisional данные до approval подлежат пересмотру и маркируются соответствующим disclaimer. Проверка data/metadata отличается от peer review научной интерпретации; approved release имеет persistent identifier и citation.
- Граница: Прочитан доступный документ с датой 2017-01-13; возможные последующие редакции не сравнивались.
- Применение: Q1, Q3, Q11, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G14 — 502.7 Fundamental Science Practices: Metadata for USGS Scientific Data

- Документ: [502.7 Fundamental Science Practices: Metadata for USGS Scientific Data](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data); издатель: USGS.
- Дата/версия: не установлена; прочитано: sections 2,4,5.
- Внешний факт: Кроме обязательных полей стандарта заполняются все поля, существенные для понимания provenance, качества и смысла. Metadata описывают пространственный/временной охват и ограничения использования; определяются обязанности data managers и reviewers.
- Граница: USGS-политика; применяем принцип достаточности, не все ведомственные поля.
- Применение: Q8, Q12, Q15. Новизна: URL уже использовался; прочитан повторно.

### G15 — AUSPOS Online GPS Processing Service

- Документ: [AUSPOS Online GPS Processing Service](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/auspos); издатель: Geoscience Australia.
- Дата/версия: не установлена; прочитано: FAQ 3.1–3.5, 5.2.
- Внешний факт: Одинаковые наблюдения в разных версиях processing дают различные координаты из-за обновлённых reference stations, velocities, calibrations и моделей. Сравнение учитывает неопределённость и reference frame; версия метода существенна даже при том же формате отчёта.
- Граница: GNSS; статистические uncertainties не равны нашему детерминированному u.
- Применение: Q5, Q7, Q9, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G16 — Geocentric Datum of Australia 2020

- Документ: [Geocentric Datum of Australia 2020](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/datums-projections/gda2020); издатель: Geoscience Australia.
- Дата/версия: 2017-12-14; прочитано: full article.
- Внешний факт: Координаты соотносятся с реализацией reference frame и эпохой; движение плит и изменения datum создают различия даже без локального редактирования геометрии.
- Граница: Страница 2017-12-14; австралийские величины не относятся к нашему SIM-LOCAL-M.
- Применение: Q9, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G17 — Quality Extension Specification

- Документ: [Quality Extension Specification](https://stac.linz.govt.nz/v0.0.15/quality/); издатель: LINZ.
- Дата/версия: не установлена; прочитано: Collection Fields.
- Внешний факт: Предложение LINZ STAC отдельно задаёт числовую accuracy, единицы и тип (nominal либо 95% confidence interval), а также scope Collection. Одна цифра accuracy без её семантики недостаточна.
- Граница: Явно Proposal, не принятый международный стандарт; не применяем collection quality к каждой линии автоматически.
- Применение: Q3, Q4, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G18 — Geodesy and Geocentric Datum of Australia

- Документ: [Geodesy and Geocentric Datum of Australia](https://www.nsw.gov.au/environment-land-and-water/surveying/geodesy-and-geocentric-datum-of-australia); издатель: NSW Government Spatial Services.
- Дата/версия: не установлена; прочитано: Positional and local uncertainty.
- Внешний факт: Positional uncertainty относительно datum отличается от local uncertainty относительно соседнего знака; обе здесь имеют 95% confidence. Малое относительное расхождение не доказывает столь же малую абсолютную ошибку.
- Граница: Геодезическая статистическая модель, не консервативный bound SIM.
- Применение: Q3, Q5, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G19 — OPUS Projects User Guide v2.0

- Документ: [OPUS Projects User Guide v2.0](https://www.ngs.noaa.gov/OPUS-Projects/user_guide/section4.3.html); издатель: NOAA NGS.
- Дата/версия: не установлена; прочитано: section 4.3;  section 6.4;  section 11.5 (один документ).
- Внешний факт: Успешная обработка/загрузка возможна при нарушении quality thresholds. Для публикации используются final precise ephemerides. Семантика uncertainty меняется по стадии; визуальная сводка не заменяет подробные файлы для сложного анализа.
- Граница: Три главы одного руководства посчитаны одним документом. Его рекомендованные thresholds прямо не являются project specifications.
- Применение: Q1, Q3, Q5, Q11, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G20 — Estimation of Vertical Uncertainties in VDatum

- Документ: [Estimation of Vertical Uncertainties in VDatum](https://vdatum.noaa.gov/docs/est_uncertainties.html); издатель: NOAA NOS.
- Дата/версия: не установлена; прочитано: Accuracy of Transformation, Source Data, Other Considerations.
- Внешний факт: Объединение неопределённостей через RSS опирается на независимость процессов; при зависимости оценка может быть больше. Ошибка исходных пользовательских данных не включается автоматически в трансформационный бюджет; пространственная применимость неоднородна.
- Граница: Вертикальная статистическая оценка; страница содержит несогласованные числовые примеры, формулы и числа не переносить в SIM.
- Применение: Q3, Q5, Q7, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### G21 — Making your data easy to find: Metadata best practice guide

- Документ: [Making your data easy to find: Metadata best practice guide](https://www.gov.uk/government/publications/making-your-geospatial-data-easy-to-find-metadata-best-practice-guide-for-data-publishers/making-your-data-easy-to-find-metadata-best-practice-guide-for-data-publishers); издатель: UK Geospatial Commission.
- Дата/версия: не установлена; прочитано: Table 1, Lineage, dates, extent.
- Внешний факт: Дата metadata, публикации и актуальности содержания различны. Conformity связывается с конкретной спецификацией/потребностью, lineage отделяется от quality results; bounding box может плохо описывать протяжённую линию.
- Граница: Discovery metadata не заменяют точный сегментный scope выписки.
- Применение: Q4, Q12, Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G22 — OGC Testbed-13: Data Quality Specification Engineering Report

- Документ: [OGC Testbed-13: Data Quality Specification Engineering Report](https://docs.ogc.org/per/17-018.html); издатель: OGC.
- Дата/версия: 2018-01-26; прочитано: 7.2.1–7.2.2.
- Внешний факт: Quality element может иметь scope, отличный от общего dataset scope; conformance, descriptive и quantitative results различны. Число сопровождается measure, domain, metric, параметрами и единицей.
- Граница: Engineering Report 2018-01-26, не OGC Standard; авиационные примеры.
- Применение: Q3, Q4, Q10, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G23 — Positional Accuracy, a Spatial Data Foundation

- Документ: [Positional Accuracy, a Spatial Data Foundation](https://www.ga.gov.au/pdf/auslig/Posaccuracy.pdf); издатель: AUSLIG; John Manning, Jim Steed.
- Дата/версия: 2001-11-19; прочитано: p1;  p9 conclusion.
- Внешний факт: Полное описание положения включает координаты, datum, epoch и точность относительно datum; пригодность межнаборного сравнения нельзя определить по совпадению координатных чисел.
- Граница: Доклад 2001-11-19/20; историческая аргументация, не текущие параметры datum.
- Применение: Q9, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G24 — Guide to reporting on administrative data quality

- Документ: [Guide to reporting on administrative data quality](https://www.stats.govt.nz/assets/Uploads/Retirement-of-archive-website-project-files/Methods/Guide-to-reporting-on-administrative-data-quality/guide-to-reporting-admin-data-quality.pdf); издатель: Statistics New Zealand.
- Дата/версия: 2016; прочитано: section 2 pp7–8.
- Внешний факт: Оценку начинают с цели, охвата, переменных и источников, значимых для конкретного использования. Ранняя оценка фиксирует известное и пробелы; прежняя metadata дополняется при появлении знаний. Изначальная цель сбора влияет на качество отдельных переменных.
- Граница: Статистические административные данные; переносим организационный принцип, не их error measures.
- Применение: Q1, Q4, Q10, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G25 — Testbed-12 Imagery Quality and Accuracy Engineering Report

- Документ: [Testbed-12 Imagery Quality and Accuracy Engineering Report](https://docs.ogc.org/per/16-050.html); издатель: OGC.
- Дата/версия: 2017-05-12; прочитано: quality units, metaquality, scope encoding.
- Внешний факт: Metaquality оценивает доверие к самому результату и репрезентативность выборки. Quality unit соединяет scope и quality elements; локальный результат не описывает автоматически весь dataset. Usability зависит от требований пользователя.
- Граница: Engineering Report 2017-05-12, не стандарт; не заменяет непрерывный полный охват SIM.
- Применение: Q3, Q4, Q5, Q10, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### G27 — USGS Science Data Exit Survey

- Документ: [USGS Science Data Exit Survey](https://www.usgs.gov/data-management/usgs-science-data-exit-survey); издатель: USGS.
- Дата/версия: не установлена; прочитано: opening sections, Introduction.
- Внешний факт: При уходе сотрудника сохраняют сведения о местонахождении данных, способе доступа, ограничениях и новом ответственном. Авторство и будущая ответственность за хранение различаются.
- Граница: Практика передачи stewardship; не разрешение заместителю подписывать выводы прежнего автора.
- Применение: Q8, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A01 — UNIDO: ISO/IEC 17025:2017 guidance

- Документ: [UNIDO: ISO/IEC 17025:2017 guidance](https://www.unido.org/sites/default/files/files/2020-06/Guide%20ISO%2017025-2017_online.pdf); издатель: UNIDO.
- Дата/версия: 2020; прочитано: PDF pp.54–55 / clauses 7.8.7, 7.8.8, 7.9, 7.10.
- Внешний факт: Выданный отчёт сохраняется: исправление, дополнение или замена выпускается отдельно со ссылкой на прежний. При обнаружении подозрительных выпущенных данных уведомление может понадобиться даже до перевыпуска. Мнения требуют документированного основания и компетентного уполномоченного автора; жалобы проверяет независимый от исходной работы участник.
- Граница: Лабораторное руководство, не обязательный стандарт GIS. Заимствуем контроль заключений, а не режим аккредитации.
- Применение: Q5, Q6, Q7, Q8, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### A02 — Data quality issues framework

- Документ: [Data quality issues framework](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework); издатель: Government Digital Service.
- Дата/версия: 2026-04-16; прочитано: What data quality rules and issues are; Determine importance; Assign priority.
- Внешний факт: Порог качества и приоритет дефекта определяются назначением данных, влиянием ошибки и фактическим отклонением. Одно и то же качество не имеет единого значения для всех сценариев использования.
- Граница: Правительственные рекомендации Великобритании; числовые таблицы приоритета не переносим в GIS автоматически.
- Применение: Q3, Q7, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### A03 — Implementing a data quality action plan

- Документ: [Implementing a data quality action plan](https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-action-plan-implementation-guide); издатель: Government Digital Service.
- Дата/версия: не установлена; прочитано: Who should be involved; Identify and log issues; steps 4–7.
- Внешний факт: План качества закрепляет владельца, журнал проблем, меры исправления, коммуникацию результатов и последующий мониторинг. В небольшой организации один человек может исполнять несколько ролей, но ответственность остаётся явной.
- Граница: Рекомендации центральному правительству; для условной организации служат образцом распределения обязанностей.
- Применение: Q7, Q8, Q13, Q14. Новизна: новый точный URL в прежнем RAW-корпусе.

### A04 — Guidance on Data Quality

- Документ: [Guidance on Data Quality](https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/information-management/guidance-data-quality.html); издатель: Government of Canada.
- Дата/версия: не установлена; прочитано: 1.1; 2 Data quality dimensions.
- Внешний факт: Пригодность для цели не требует одинакового уровня по всем измерениям качества. Важность точности, полноты, интерпретируемости и других измерений зависит от использования и стадии жизненного цикла.
- Граница: Общие рекомендации государственным органам Канады; не задают GIS-допуски.
- Применение: Q3, Q4, Q10, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### A05 — Data Quality Management Policy

- Документ: [Data Quality Management Policy](https://www.ons.gov.uk/aboutus/transparencyandgovernance/datastrategy/datapolicies/dataqualitymanagementpolicy); издатель: ONS.
- Дата/версия: не установлена; прочитано: Policy sections 1–3.
- Внешний факт: Формальная передача данных между командами сопровождается договорённостями о коммуникации, документации и показателях качества. Изменения качества и последствия исправлений сообщаются пользователям; метаданные качества выпускаются одновременно с данными.
- Граница: Внутренняя политика ONS, не регламент GeoService.
- Применение: Q11, Q13, Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A06 — Constraints of the PROV Data Model

- Документ: [Constraints of the PROV Data Model](https://www.w3.org/TR/prov-constraints/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Constraints 36–38.
- Внешний факт: Модель происхождения проверяет порядок событий: создание предшествует использованию и прекращению действия сущности. Отсутствующий идентификатор допускает неизвестность, но не даёт основания изобретать участника или зависимость.
- Граница: Ограничения графа provenance не доказывают истинность данных и не определяют юридическую силу заключений.
- Применение: Q2, Q7, Q9. Новизна: новый точный URL в прежнем RAW-корпусе.

### A07 — Linking Across Provenance Bundles

- Документ: [Linking Across Provenance Bundles](https://www.w3.org/TR/prov-links/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Mention relation.
- Внешний факт: Связь между пакетами provenance сохраняет контекст конкретного описания. Описание одного объекта разными участниками нельзя молча слить в одно без указания пакета и интерпретации.
- Граница: W3C Note для семантической связности; не процедура разрешения экспертных споров.
- Применение: Q5, Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A08 — PROV-AQ: Provenance Access and Query

- Документ: [PROV-AQ: Provenance Access and Query](https://www.w3.org/TR/prov-aq/); издатель: W3C.
- Дата/версия: не установлена; прочитано: HTTP has_provenance link.
- Внешний факт: Ресурс может сообщать адрес записи происхождения и точный идентификатор объекта в ней. Несколько записей происхождения допустимы; известная серверу запись не означает, что других нет.
- Граница: Технический способ обнаружения provenance; наличие ссылки не гарантирует полноту downstream-цепочки.
- Применение: Q14, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A09 — PROV-Dictionary: Modeling Provenance for Dictionary Data Structures

- Документ: [PROV-Dictionary: Modeling Provenance for Dictionary Data Structures](https://www.w3.org/TR/prov-dictionary/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Removal relation; example 5.
- Внешний факт: Изменения набора можно представлять явными вставками и удалениями ключей с отдельными сущностями до и после. Даже операция, не изменившая содержимое, не стирает историческую последовательность.
- Граница: Модель словарей, не готовая семантика геометрии или административного восстановления.
- Применение: Q2, Q9, Q10. Новизна: новый точный URL в прежнем RAW-корпусе.

### A10 — PROV Model Primer

- Документ: [PROV Model Primer](https://www.w3.org/TR/prov-primer/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Specialization and alternate entities.
- Внешний факт: Общий документ и отдельные версии являются разными сущностями; одинаковое содержимое в другом контексте не обязательно та же сущность. Читатель может сослаться именно на версию до последующего изменения автором.
- Граница: Учебное описание PROV, не дополнительное независимое подтверждение нормативных правил PROV.
- Применение: Q2, Q9, Q13, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A11 — The AQuA Book

- Документ: [The AQuA Book](https://www.gov.uk/guidance/the-aqua-book); издатель: Government Analysis Function.
- Дата/версия: 2025-07-30; прочитано: User and technical documentation; roles; assurance activities.
- Внешний факт: Аналитик, независимый проверяющий и утверждающий имеют различные обязанности. Документация включает цель, методы, допущения, проверки, ограничения и срок или условия валидности. Верность реализации метода не равна пригодности анализа для цели.
- Граница: Руководство британской государственной аналитики; применяем как аналогию, не обязательный GIS-процесс.
- Применение: Q1, Q3, Q5, Q8, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A12 — Revisions and Corrections Policy

- Документ: [Revisions and Corrections Policy](https://www.gov.uk/government/publications/standards-for-official-statistics-at-dcms/revisions-and-corrections-policy); издатель: DCMS.
- Дата/версия: 2026-06-11; прочитано: Scheduled revisions; Corrections.
- Внешний факт: Предварительность явно маркируется с причиной и ожиданием пересмотра. Существенная ошибка требует скорого исправления; пока результат расследуется, возможна предупреждающая отметка. Причина, масштаб и даты изменений публикуются.
- Граница: Статистическая политика; сроки для небольших ошибок не принимаются как SLA GeoService.
- Применение: Q1, Q6, Q7, Q13, Q14. Новизна: новый точный URL в прежнем RAW-корпусе.

### A13 — Verification and Validation for the AQuA Book

- Документ: [Verification and Validation for the AQuA Book](https://assets.publishing.service.gov.uk/media/5a749eeee5274a44083b8256/R0003199E.pdf); издатель: Dstl.
- Дата/версия: 2014-09-01; прочитано: PDF pp.12–14, executive summary.
- Внешний факт: Журнал валидности метода включает назначение, опыт применения, компетентных исполнителей, свидетельства проверок и ограничения. Отчёт соотносит результаты с прежними выводами и объясняет значимые различия.
- Граница: Отдельное методическое руководство Dstl, не иная версия AQuA Book; переносится логика проверки пригодности.
- Применение: Q3, Q5, Q7, Q8, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### A14 — ONS Revisions Policy and Correction of Errors Policy

- Документ: [ONS Revisions Policy and Correction of Errors Policy](https://www.ons.gov.uk/methodology/methodologytopicsandstatisticalconcepts/revisions/guidetostatisticalrevisions); издатель: ONS.
- Дата/версия: не установлена; прочитано: Sections 1, 3, 4.
- Внешний факт: Плановое улучшение данных и исправление ошибки имеют разные основания. При выборе момента пересмотра учитываются своевременность информирования и нежелательность нескольких последовательных поправок к одним данным.
- Граница: Практика статистических публикаций; не отменяет срочное предупреждение об опасном дефекте GIS.
- Применение: Q1, Q6, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### A15 — Data Quality Vocabulary

- Документ: [Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Abstract; 6.2–6.3.
- Внешний факт: Оценка качества может исходить от издателя или пользователей. Происхождение фиксируется отдельно для всего пакета метаданных и отдельного измерения качества, позволяя хранить разные оценки без потери авторства.
- Граница: Словарь не задаёт универсального определения качества и не выбирает победителя среди противоречивых оценок.
- Применение: Q3, Q5, Q10, Q15. Новизна: URL уже использовался; прочитан повторно.

### A16 — Data Catalog Vocabulary DCAT 3

- Документ: [Data Catalog Vocabulary DCAT 3](https://www.w3.org/TR/vocab-dcat-3/); издатель: W3C.
- Дата/версия: 2024-08-22; прочитано: 6.4.24–30; 11 Versioning.
- Внешний факт: Версия, предыдущая версия, текущая версия, замещение и статус — разные отношения. Статус рабочего процесса не определяется самим DCAT; описание изменений может указывать несовместимость с прошлой версией.
- Граница: Метаданные каталога, не готовая машина состояний заключения.
- Применение: Q1, Q6, Q9, Q13, Q15. Новизна: URL уже использовался; прочитан повторно.

### A17 — Data on the Web Best Practices

- Документ: [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/); издатель: W3C.
- Дата/версия: не установлена; прочитано: Best Practices 7–11.
- Внешний факт: Версиям нужны отдельные идентификаторы, а истории — объяснения отличий. Переменный адрес актуальных данных и устойчивый адрес конкретной версии обслуживают разные цели повторного использования.
- Граница: Рекомендации публикации веб-данных; неизменность экспортов и порядок уведомлений выбирает организация.
- Применение: Q9, Q13, Q14, Q15. Новизна: URL уже использовался; прочитан повторно.

### A18 — PROV-O: The PROV Ontology

- Документ: [PROV-O: The PROV Ontology](https://www.w3.org/TR/prov-o/); издатель: W3C.
- Дата/версия: не установлена; прочитано: prov:Revision and wasRevisionOf.
- Внешний факт: Пересмотр моделируется как производная новая сущность со ссылкой на прежнюю; квалифицированная связь может хранить дополнительные обстоятельства пересмотра.
- Граница: Онтология происхождения не означает, что любая новая версия отменяет все выводы старой.
- Применение: Q2, Q6, Q9, Q13. Новизна: URL уже использовался; прочитан повторно.

### A19 — PROV-DM: The PROV Data Model

- Документ: [PROV-DM: The PROV Data Model](https://www.w3.org/TR/prov-dm/); издатель: W3C.
- Дата/версия: не установлена; прочитано: 5.1.8 Invalidation.
- Внешний факт: Прекращение действия сущности фиксируется отдельным событием с участием деятельности и временем. Оно отличается от генерации новой сущности; историческое существование не стирается.
- Граница: PROV-invalidation описывает сущность в выбранной модели; нельзя автоматически отождествлять её с удалением файла или юридическим отзывом.
- Применение: Q7, Q9, Q13. Новизна: URL уже использовался; прочитан повторно.

### A20 — Metrological Traceability: Frequently Asked Questions and NIST Policy

- Документ: [Metrological Traceability: Frequently Asked Questions and NIST Policy](https://www.nist.gov/metrology/metrological-traceability); издатель: NIST.
- Дата/версия: не установлена; прочитано: 5.1.4; 5.2.1–3.
- Внешний факт: Метрологическая прослеживаемость сама по себе не гарантирует пригодность результата. Нужны описание измеряемой характеристики, метода, неопределённости и цепочки опорных измерений; прослеживаемость периодически переоценивают.
- Граница: Про измерения и калибровки; не универсальное правило provenance документов.
- Применение: Q3, Q7, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A21 — Guidance on Environmental Data Verification and Data Validation QA/G-8

- Документ: [Guidance on Environmental Data Verification and Data Validation QA/G-8](https://www.epa.gov/sites/default/files/2015-06/documents/g8-final.pdf); издатель: EPA.
- Дата/версия: 2002-11; прочитано: Sections 1.1–1.2; pp.1–6.
- Внешний факт: Проверка соблюдения метода, оценка аналитического качества и оценка пригодности для решения — связанные, но разные действия. Объём проверки зависит от цели проекта, а результаты верификации служат входом последующей валидации.
- Граница: Историческое необязывающее руководство экологических измерений; терминология других отраслей может отличаться.
- Применение: Q1, Q3, Q4, Q10, Q11, Q12. Новизна: новый точный URL в прежнем RAW-корпусе.

### A22 — Data Verification, Reporting and Validation

- Документ: [Data Verification, Reporting and Validation](https://www.epa.gov/choose-fish-and-shellfish-wisely/data-verification-reporting-and-validation); издатель: EPA.
- Дата/версия: не установлена; прочитано: Data Validation.
- Внешний факт: Проверяющий оценивает смысл флага качества для конкретного проекта. Квалификатор не обязательно делает данные непригодными. Исходную поставку можно сохранять, дополняя отдельными колонками выводов валидации и пояснениями.
- Граница: Руководство анализу рыбы и моллюсков; флаги и лабораторные критерии не переносятся буквально.
- Применение: Q3, Q4, Q10, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A23 — ILAC G27: Guidance on measurements performed as part of an inspection process

- Документ: [ILAC G27: Guidance on measurements performed as part of an inspection process](https://acreditare.md/public/files/Documente_EA_ILAC_IAF/OI/ILAC_G27_06_2019-1.pdf); издатель: ILAC; official MOLDAC mirror.
- Дата/версия: 2019-07; прочитано: Section 2; PDF p.7; cases 3.6–3.7.
- Внешний факт: Значимость измерения для итогового заключения определяет требуемую глубину обеспечения качества. Пригодность метода зависит не только от точности, но и от надёжности обнаружения существенных свойств; разные части обследования могут требовать разных проверок.
- Граница: Инспекционная аккредитация; пример методологической соразмерности, не обязательность ISO17020/17025 для GIS.
- Применение: Q3, Q4, Q7, Q10. Новизна: новый точный URL в прежнем RAW-корпусе.

### A24 — NIST TN1297 section 7 Reporting Uncertainty

- Документ: [NIST TN1297 section 7 Reporting Uncertainty](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-7-reporting-uncertainty); издатель: NIST.
- Дата/версия: не установлена; прочитано: 7.1.
- Внешний факт: Сообщение неопределённости должно указывать коэффициент охвата либо суммарную стандартную неопределённость, составляющие и способ оценки. Вероятностное толкование интервала требует основания.
- Граница: Метрологическое руководство; не универсальный допуск GIS. TN1297 как публикация уже частично использована ранее через physics.nist.gov.
- Применение: Q3, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### A25 — Data Quality Assessment: A Reviewer's Guide QA/G-9R

- Документ: [Data Quality Assessment: A Reviewer's Guide QA/G-9R](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=900B0C00.TXT); издатель: EPA.
- Дата/версия: 2006-02; прочитано: 0.1; steps 1,3,4.
- Внешний факт: Вывод привязан к проектной цели, схеме выборки и допущениям метода. Если допущения не выполнены, требуется альтернативный метод либо дополнительные данные, а отклонение документируется.
- Граница: Статистическая оценка экологических данных; не подтверждает автоматически пригодность непроверенного пространственного остатка.
- Применение: Q3, Q4, Q5, Q7, Q10, Q12. Новизна: новый точный URL в прежнем RAW-корпусе; нормализованный адрес уже встречался.

### A26 — Third Party Correspondence on RFC/RFR Submitted to EPA

- Документ: [Third Party Correspondence on RFC/RFR Submitted to EPA](https://www.epa.gov/quality/third-party-correspondence-request-correction-and-request-reconsideration-submitted-epa); издатель: EPA.
- Дата/версия: не установлена; прочитано: Introduction; Disclaimer.
- Внешний факт: Публикация замечания третьей стороны ради прозрачности не означает согласия с ним, одобрения качества или намерения опереться на него. Замечание связывается с идентификатором исходного запроса.
- Граница: Про публичные обращения EPA; аналог различения регистрации, рассмотрения и принятия.
- Применение: Q5, Q11, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### A27 — Request for Correction

- Документ: [Request for Correction](https://www.energy.gov/cio/request-correction); издатель: US Department of Energy.
- Дата/версия: не установлена; прочитано: Detailed Description; Potential Impacts; Explanation.
- Внешний факт: Запрос исправления идентифицирует точный отчёт и конкретный элемент, объясняет воздействие, основание несогласия и предлагаемое исправление. Это позволяет отделить факт обращения от обоснованности требования.
- Граница: Административная процедура DOE; срок 60 дней и бремя доказывания не заимствуются.
- Применение: Q5, Q6, Q11, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### A28 — EA FAQs — Reports, 50.1 Amendments

- Документ: [EA FAQs — Reports, 50.1 Amendments](https://european-accreditation.org/publications-and-news/ea-faqs/); издатель: European co-operation for Accreditation.
- Дата/версия: 2025-11-24; прочитано: Reports Q50.1; lines 6144–6164.
- Внешний факт: FAQ приводит различающиеся позиции: ISO/CASCO не требует выделять изменения в полном заменяющем отчёте при ссылке на оригинал; EA считает общее требование ясности изменений применимым и к полной замене. Поэтому обязательный diff нельзя объявлять единой бесспорной международной нормой.
- Граница: Аккредитационная интерпретация; история и причина замены в GeoService — собственное решение условной организации.
- Применение: Q6, Q13. Новизна: новый точный URL в прежнем RAW-корпусе.

### R01 — Subsurface Utility Engineering

- Документ: [Subsurface Utility Engineering](https://www.fhwa.dot.gov/programadmin/sueindex.cfm); издатель: FHWA.
- Дата/версия: 2022-11-01 (страница); прочитано: SUE Quality Levels; How SUE Works.
- Внешний факт: Качество сведений об инженерных коммуникациях выбирается по риску и назначению; максимальный уровень обычно нужен не в каждой точке трассы. Уровни характеризуют способы получения сведений, а не одну универсальную погрешность.
- Граница: Контекст дорожных проектов США; уровни QL не заменяют учебный критерий GeoService.
- Применение: Q3, Q4, Q12, Q15. Новизна: URL уже использовался; прочитан повторно.

### R02 — Avoiding danger from underground services, HSG47, Third edition

- Документ: [Avoiding danger from underground services, HSG47, Third edition](https://www.hse.gov.uk/pubns/priced/hsg47.pdf); издатель: HSE.
- Дата/версия: 2014; прочитано: §§36–42,135–136; pp11–12,28.
- Внешний факт: План сам по себе недостаточен для установления расположения коммуникаций. При обнаружении неточностей или изменении трассы сведения передают владельцу для исправления; исполнительный план должен отражать фактическую прокладку.
- Граница: Рекомендации UK по земляным работам; исследование не является инструкцией безопасного производства работ.
- Применение: Q3, Q12, Q13, Q15. Новизна: URL уже использовался; прочитан повторно.

### R03 — Survey Manual Chapter 12 — Subsurface Utility Engineering Designation and Location

- Документ: [Survey Manual Chapter 12 — Subsurface Utility Engineering Designation and Location](https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/technical-guidance-documents/location-and-design/migrated/surveymanual/Chapter12_acc05022023_PM.pdf); издатель: VDOT.
- Дата/версия: не установлена; имя файла содержит 2023; прочитано: §12.02; §12.04; §12.05.
- Внешний факт: Система координат и рабочие единицы обследования должны совпадать с проектной съёмкой. Передача данных через ProjectWise и уведомление адресата предшествуют оценке и включению в проект.
- Граница: Процедура VDOT, не универсальные полномочия георедактора.
- Применение: Q1, Q11, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### R05 — SUE Scope of Services, Exhibit A

- Документ: [SUE Scope of Services, Exhibit A](https://www.dot.ga.gov/PartnerSmart/utilities/Documents/SUEScopeOfServices.pdf); издатель: GDOT.
- Дата/версия: 12/05/2025 — как напечатано в документе; прочитано: §1.2 Quality Assurance Program, §1.8 Utility Report.
- Внешний факт: Программа качества описывает проверки, записи и peer review; отдельный utility report дополняет чертежи рисками, предположениями и рекомендациями по расхождениям, позволяя получателю интерпретировать данные.
- Граница: Условия контракта GDOT; профессиональная сертификация и организационные сроки не переносятся на pet-проект.
- Применение: Q1, Q5, Q8, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.

### R06 — National Underground Asset Register (NUAR)

- Документ: [National Underground Asset Register (NUAR)](https://www.gov.uk/guidance/national-underground-asset-register-nuar); издатель: GDS / DSIT.
- Дата/версия: обновлено 2026-04-27; прочитано: About NUAR, абзац об использовании как primary means.
- Внешний факт: NUAR объединяет доступ к сведениям владельцев; решение о том, как использовать их в процессе безопасных земляных работ, остаётся за выполняющими эти работы. Доставка единой карты не равна разрешению конкретного использования.
- Граница: Описание сервиса UK; статистику выгод и охват не используем как измеренный эффект GeoService.
- Применение: Q11, Q12, Q15. Новизна: новый точный URL в прежнем RAW-корпусе.
