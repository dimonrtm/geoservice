---
title: Utility GIS Editor — пригодность экземпляра данных и доказательства результата
type: research
status: active
created: 2026-11-07
updated: 2026-11-07
source: RAW_inputs/documents/UtilityGisEditorRole.md
tags: [domain-research, utility-gis, dataset-qualification, simulated-organization]
---

# Utility GIS Editor: глубокий анализ UseCase и новых знаний

## Область и происхождение

Это отдельное интернет-исследование по поручению пользователя после discovery. Рассмотрен исходный UseCase из [[RAW_inputs/documents/UtilityGisEditorRole]], текущая Wiki/DDD_Wiki и 15 вопросов о допуске конкретного набора и доказательстве сохранённого результата. [Ответы и решения условной организации](2026-11-07-utility-gis-editor-dataset-qualification-answers.md) — второй результат того же исследования. Оба документа опираются на общий корпус **80 внешних документов**, а не на два независимых корпуса по 80.

Обозначения: **факт источника** — содержание доступной публикации; **решение организации** — выбранное агентом через персону `02_expert_oldman_ufa` правило GeoService; **гипотеза** — пока не проверенное предположение. Персона не является реальным интервьюируемым. Синтетические координаты не выдаются за полевую съёмку. Фактическая БД, конкретный volume и пользовательский runtime в этом исследовании не проверялись.

Поиск охватил utility editing, field/offline sync, subsurface utility survey, as-built asset handover, идентичность записей, CRS/операции, геометрические предикаты, качество и происхождение. Использованы документы владельцев стандартов, регуляторов, операторов сетей и разработчиков продуктов. Читались релевантные разделы HTML/PDF; не заявляется полное чтение каждого многостраничного руководства. Список S01–S80 ниже содержит вклад и ограничения каждого документа. Поисковые сниппеты, ошибки доступа, повторные открытия и языковые копии в число 80 не включены.

Точное сравнение URL с предыдущими файлами `RAW_inputs/research_results/*.md` дало 51 ранее не встречавшуюся ссылку и 29 повторных. Это не оценка числа новых произведений: перенаправление, новая версия документа или новый URL могут вести к знакомому материалу. Содержательно новые для этого разбора опоры — открытые элементы NUAR 2025 года (S09), IMKL/KLIC (S64/S70), SLA Utility Survey (S71), NGS OPUS Projects §4.3 (S77). Общая библиография содержит зависимые документы одного поставщика; 80 документов не означают 80 независимых подтверждений.

## 1. Что исходный UseCase подтверждает, а что требует ограничения

| Тезис исходного файла | Результат проверки | Последствие для GeoService |
| --- | --- | --- |
| Редактор работает с авторитетной моделью сети | Поддерживается сценариями Esri, Giswater и документацией операторов, S01–S06/S25–S26/S53–S56 | Намерение правки, идентичность, связи и передача результата существенны |
| Два стека доминируют на рынке | Корпус показывает существование и возможности стеков, но не рыночные доли | Не использовать как установленный факт или аргумент выбора архитектуры |
| После изменения нужны контроль и reconcile/post | Поддерживается для конкретного versioned workflow Esri, S59–S61 | Не считать весь vendor workflow обязательным для ближайшего среза |
| Поле и офис обмениваются изменениями | Поддерживается QFieldCloud/Mergin, S22–S24/S32–S34/S65–S67 | Нужны идентичность копии, состояние синхронизации и разбор конфликтов |
| Правка геометрии даёт готовую сетевую модель | Не следует из источников; topology/операционные состояния/расчёты отдельны | Не заявлять topology checked или гидравлическую пригодность после Save |
| Сведения карты пригодны для эксплуатации и раскопок | Без дополнительных условий не подтверждается, S20/S68–S71 | Техническая демонстрация не является разрешением на реальные работы |

Исходные opaque-ссылки вида `turn…` не воспроизводимы как самостоятельная библиография и не перенесены в доказательную базу. Исходник сохранён без исправлений. Слова «часто», «доминируют», «почти всегда» требуют отдельного исследования распространённости; число руководств не заменяет такую статистику. FU-2026-06-01-002 поэтому не закрывается.

Сквозной UseCase логично разделить на получение задания/основания, установление объекта и версии, подготовку допустимой правки, сохранение, выяснение исхода и актуального состояния, оценку качества, согласование/передачу. Это аналитическая декомпозиция, не предложение реализовать все этапы сейчас. Ближайший срез сохраняет одну существующую линию, одну внутреннюю вершину, неизменяемые endpoints/associations и baseline.

## 2. Идентичность: реальный актив, запись, система и экземпляр

**Факт.** MUDDI различает идентификатор реального объекта, его записи и системы; DCAT отдельно описывает набор и формы его распространения. USGS различает идентификаторы metadata и dataset. [S10](https://docs.ogc.org/is/23-024/23-024.html) [S49](https://www.w3.org/TR/vocab-dcat-3/) [S29](https://www.usgs.gov/science-data-management/persistent-identifiers-pids-metadata-faq)

**Новый вывод.** Название `synthetic_utility_feeder_01`, asset code `L-003`, локальный feature ID и геометрия отвечают на разные вопросы. Повторное создание базы может сохранить название и изменить локальные ID; импорт может создать ещё одну запись того же актива; одинаковая форма может принадлежать соседним или синтетическим объектам. Нельзя выбирать одну из этих осей идентичности молча.

**Решение организации.** Для допуска упражнения фиксировать логический набор/редакцию и конкретный экземпляр окружения, затем локальную запись и её связь с обозначением актива. Внутри экземпляра ключ должен быть однозначен; между экземплярами требуется явное сопоставление с provenance. Хеш координат может подтверждать снимок, но не заменяет идентичность объекта. Новая таблица идентификаторов и новые aggregate этим не вводятся.

**Контрпример.** Два volume имеют L-003 с одинаковым кодом, но один создан до изменения seed. Имя совпало, данные для упражнения — нет. Правильный результат: разные экземпляры, отдельная сверка. Не «починить L-003 до ожидаемого вида» в ходе проверки.

## 3. Координатная политика: происхождение важнее похожих чисел

**Факт.** `ST_SetSRID` меняет обозначение, `ST_Transform` преобразует координаты; PROJ учитывает параметры и доступные операции. GeoJSON задаёт порядок longitude/latitude, который следует сопоставлять с соглашениями CRS и API. [S36](https://postgis.net/docs/ST_SetSRID.html) [S37](https://postgis.net/docs/ST_Transform.html) [S45](https://proj.org/en/stable/faq.html) [S46](https://proj.org/en/stable/usage/transformation.html) [S51](https://www.rfc-editor.org/rfc/rfc7946)

**Новый вывод.** Паспорт задаёт выбранные условия, настройка приложения переносит часть условий в программу, persisted policy определяет правила конкретной EditVersion, наблюдаемые координаты показывают фактическое представление. Это цепочка разных свидетельств. Обратный вывод «настройка по умолчанию существует, значит набор получен на этой сетке» некорректен.

**Решение организации.** В карточке сравнения четыре графы: ожидаемое по паспорту; источник/основание; фактическое значение версии/данных; результат сверки. Неизвестность остаётся видимой. Смена настроек не переписывает правила старой версии. При расхождении останавливается заявленное упражнение; вопрос исправления исходных данных проходит существующий разбор.

Для синтетических данных можно выбрать сетку как условие генерации и показать соответствие данным. Для импортированного набора та же сетка без сведений о происхождении — лишь предположение. Минимальный наблюдаемый шаг разностей координат тоже не доказывает исходное разрешение: выборка могла не использовать более мелкие деления, а последующий экспорт — округлить значения.

## 4. CRS недостаточно для воспроизводимости преобразования

**Факт.** PROJ выбирает операции с учётом территории, доступных сеток и точности; OS и Geoscience Australia публикуют разные модели для разных задач/областей. Геодезические системы могут учитывать эпоху. [S11](https://proj.org/en/stable/operations/operations_computation.html) [S47](https://proj.org/en/stable/apps/projinfo.html) [S57](https://www.ordnancesurvey.co.uk/geodesy-positioning/coordinate-transformations) [S72](https://www.linz.govt.nz/sites/default/files/25000-LINZS25000%2520Standard%2520for%2520New%2520Zealand%2520Geodetic%2520Datum%25202000%2520_4.pdf) [S73](https://www.ordnancesurvey.co.uk/documents/resources/guide-coordinate-systems-great-britain.pdf) [S78](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/australian-geospatial-reference-system/agrstoolsandmodels) [S79](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/datums-projections/gda2020)

**Новый вывод.** Даже правильные source/target CRS не определяют единственный результат: нужны реально применённая операция, версия ресурсов, параметры и условия. Контрольная точка должна соответствовать назначению и территории операции. Наличие утилиты `projinfo` показывает доступные варианты, а не историю конкретного файла.

**Решение организации.** Для преобразованных evidence фиксировать исходную/целевую CRS, оси, единицы, метод/параметры, необходимые ресурсы, область и версию обработки. Эпоха и vertical datum нужны, когда они влияют на заявленное утверждение; не требовать их механически для XY-синтетики без такого преобразования. «Преобразование не выполнялось» допустимо только при прослеживаемом происхождении координат. «В коде нет pipeline» не доказывает отсутствия преобразования до импорта.

Применение: оценка в метрах требует обоснованного метода. Разница широт/долгот, умноженная на произвольный коэффициент, не становится подтверждённой позиционной оценкой. Сетка градусов не заменяет метрический критерий SIM-UGIS-POS-001.

## 5. Неизвестное значение и неприменимое свойство — разные результаты

**Факт.** Практики метаданных, требований к поставке и словари качества связывают утверждение с его предметом и основанием. [S28](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data) [S50](https://www.w3.org/TR/vocab-dqv/) [S53](https://assets.watercare.co.nz/media/ai_asset_information_and_data_standard_november_2020_b0f0de2baa.pdf) [S55](https://assets.watercare.co.nz/media/eir_watercare_e057cb8a01.pdf)

**Решение организации.** Использовать в ручной карточке различимые формулировки: «значение установлено, источник…», «неизвестно», «не предусмотрено текущим контрактом», «не применимо к данной цели, потому что…». Это не новый API enum. Отсутствие persisted `xyTolerance` означает отсутствие такого поля в текущем контракте, а не значение ноль и не отсутствие всех допусков вообще.

Сведения о преобразовании, необходимые для позиционного вывода, могут оставаться неизвестными и делать этот вывод недоказанным. При этом техническая проверка Save синтетической линии может быть выполнима. Квалификация зависит от цели, а не от универсального флага «набор хороший».

## 6. Геометрическое равенство не доказывает допустимость одной вершины

**Факт.** `ST_Equals` сравнивает множества точек и допускает различную структуру вершин; `ST_OrderingEquals` учитывает порядок. Операции grid/precision могут затронуть множество точек. [S35](https://docs.qgis.org/3.40/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html) [S39](https://postgis.net/docs/ST_ReducePrecision.html) [S40](https://postgis.net/docs/ST_SnapToGrid.html) [S41](https://postgis.net/docs/ST_Equals.html) [S42](https://postgis.net/docs/ST_OrderingEquals.html)

**Новый вывод.** Двухточечная и трёхточечная коллинеарные линии могут быть топологически равны, но только у второй есть внутренняя shape vertex. Поэтому равенство геометрии и пригодность fixture — независимые проверки.

**Решение организации.** Сравнивать тип/размерность, число и порядок вершин, endpoints, разрешённый индекс изменения и неизменность прочих элементов по принятому контракту. Нельзя добавлять вершину старой L-003 ради совпадения с новым сценарием. Общая нормализация всех координат может создать дополнительные изменения и нарушить ограничение first-save.

Экранное округление — ещё одна форма представления. Числа, выглядящие одинаковыми на панели, могут различаться в сохранённом снимке. Проверка должна опираться на координаты достаточной точности и их связь с версией; screenshot служит иллюстрацией, не единственным доказательством. [S38](https://postgis.net/docs/ST_AsGeoJSON.html)

## 7. Допуск зависит от задания, а не только от линии

**Факт.** Предикат покрытия допускает совпадение с границей; геометрическая валидность проверяет другие свойства. [S43](https://postgis.net/docs/ST_CoveredBy.html) [S44](https://postgis.net/docs/ST_IsValid.html)

**Решение организации.** Перепроверять WorkOrder/AOI и доступную ветку упражнения при смене наряда, его области или состояния. Полное покрытие линии AOI не равно строгому внутреннему положению перемещаемой вершины. Видимость объекта на карте не означает eligibility.

Здесь важна причинность: изменение AOI делает старое свидетельство допуска неприменимым к новой задаче, даже если XY не изменились. Это развитие существующего `change_basis_lifecycle`, а не новый lifecycle EditVersion. Исторический результат сохраняется с прежним scope; новая задача требует нового обоснования.

## 8. Синхронизация и сохранение не равны единому снимку

**Факт.** QFieldCloud и Mergin документируют передачу изменений, версии и конфликты; Esri отдельно выполняет reconcile/post. [S22](https://docs.qfield.org/get-started/tutorials/get-started-qfc/) [S23](https://docs.qfield.org/reference/qfieldcloud/system/) [S24](https://docs.qfield.org/reference/qfieldcloud/workflow/) [S32](https://docs.qfield.org/reference/qfieldcloud/jobs/) [S33](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/) [S34](https://docs.qfield.org/get-started/tutorials/tips-tricks-qfc/) [S59](https://pro.arcgis.com/en/pro-app/3.3/help/data/geodatabases/overview/manage-branch-version-conflicts.htm) [S60](https://pro.arcgis.com/en/pro-app/3.5/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.htm) [S65](https://merginmaps.com/docs/manage/synchronisation/) [S66](https://merginmaps.com/docs/manage/missing-data/) [S67](https://merginmaps.com/blog/mergin-maps-best-practises-from-setup-to-fieldwork)

**Новый вывод.** Receipt подтверждает исход конкретного действия; current — состояние на момент чтения. Отображённая карта и ChangeSet, прочитанные в разное время, могут не составлять одного доказательства. Временные метки сами по себе не заменяют причинную/версионную связь. Модель PROV полезна для описания этой связи, но не предоставляет транзакционность. [S48](https://www.w3.org/TR/prov-dm/) [S74](https://www.w3.org/TR/prov-constraints/)

**Решение организации.** В отчёте отдельно фиксировать операцию, её исход, версии прочитанных представлений и baseline. При расхождении обновлять чтение доступными средствами и указывать, что удалось согласовать. Не называть независимые GET атомарным снимком. Если контракт не позволяет подтвердить согласованность, результат честно ограничивается.

Повтор старого CommandId может доказать исторический успех, но не отменяет более новую правку. Новый current не делает старый receipt ложным. Автоматическое «последний победил» из другого продукта не становится нашим правилом разрешения бизнес-конфликтов.

## 9. Успешная запись, топология, позиционная и эксплуатационная пригодность

**Факт.** В utility workflows сетевой контроль выделен отдельно; EPANET требует расчётных параметров и калибровочных наблюдений. [S01](https://doc.esri.com/en/arcgis-pro/latest/help/editing/edit-a-utility-network.html) [S02](https://learn.arcgis.com/en/projects/edit-and-validate-subnetworks/) [S03](https://learn.arcgis.com/en/projects/manage-utility-data-using-arcgis-utility-network/) [S04](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-network-topology.html) [S05](https://pro.arcgis.com/en/pro-app/3.3/help/data/utility-network/dirty-areas-in-a-utility-network.htm) [S06](https://learn.arcgis.com/en/projects/get-started-with-arcgis-utility-network-for-wastewater/) [S25](https://giswater.gitbook.io/giswater-manual/7.-topological-and-geometrical-adjustments-giswater-toolbox) [S26](https://giswater.gitbook.io/giswater-manual/3.-basic-work-rules) [S61](https://pro.arcgis.com/en/pro-app/3.4/help/data/utility-network/faq.htm) [S62](https://www.epa.gov/water-research/epanet) [S63](https://19january2021snapshot.epa.gov/sites/static/files/2020-05/documents/epanet_userss_manual_2.2.0.pdf)

**Решение организации.** Выводы формулировать раздельно: допустимая техническая запись; согласованный readback; пригодность основания; позиционная оценка; topology; эксплуатационная пригодность; выпуск/принятие. Не объединять всё в «проверено».

SIM-UGIS-POS-001 остаётся прежним: для полного заявленного охвата требуется выполнение выбранного критерия `Q=max(e(s)+u(s))`, `T=0.50 m`, `u(s)<=0.10 m` и его остальных условий. Новые источники не меняют эти числа. Они не доказывают точность L-003. Длина сдвига мышью — величина изменения записи, а не ошибка относительно независимого эталона. SIM-EVID-001 не становится evidence для L-003 от совпадения учебного контекста.

## 10. Полевое происхождение и поставка данных дают разные доказательства

**Факт.** SLA описывает съёмку коммуникаций, в том числе до засыпки; HSE рассматривает планы вместе с обнаружением; Kadaster различает отсутствие объекта, изменения сети и расхождения положения. [S68](https://www.hse.gov.uk/electricity/information/excavations.htm) [S69](https://www.hse.gov.uk/pubns/priced/hsg47.pdf) [S70](https://www.kadaster.nl/-/invulinstructie-klic-schadeformulier) [S71](https://www.sla.gov.sg/qql/slot/u143/Newsroom/Circulars/Survey%20Services/Other%20Information/Standard%20and%20Specifications%20for%20Utility%20Survey%20in%20Singapore%20Version%201.0%20-%20Aug%202017.pdf)

**Новый вывод.** Пропущенное наблюдение физически скрытого объекта нельзя восстановить красивой геометрией. Последующая правка может улучшить запись по допустимому основанию, но не превращает её в непосредственную съёмку. Статус «as-built» должен читаться вместе с методом и источником.

**Факт.** ADAC, Watercare и Urban Utilities описывают информационную поставку и принятие; NUAR/IMKL согласуют схемы обмена. [S07](https://gdsgeospatial.blog.gov.uk/2024/08/13/an-introduction-to-the-nuar-data-model/) [S09](https://gdsgeospatial.blog.gov.uk/2025/11/13/open-sourcing-elements-of-nuar/) [S12](https://www.contractsfinder.service.gov.uk/Notice/Attachment/b1a84db2-857d-427f-908d-a20a3fff82f9) [S16](https://www.unitywater.com/-/media/unitywater/pdf-accreditation-certification-documents/adac-xml-data-capture-guidelines-version-2.pdf) [S17](https://www.unitywater.com/-/media/unitywater/pdf-infrastructure-standards/pr11473---private-works-pcd-manual.pdf?hash=4BB5355C0C94427DC068DA031E7F28B2&sc_lang=en) [S18](https://www.watercare.co.nz/builders-and-developers/tools-fees-and-resources/engineering-standards-framework/asset-recording) [S19](https://www.watercare.co.nz/builders-and-developers/compliance/certificate-of-acceptance) [S21](https://www.urbanutilities.com.au/sfsites/c/cms/delivery/media/MCNYOLYHR4LZC6PJ33664RPYLYJE) [S54](https://assets.watercare.co.nz/media/ESF_500_STD_502_6f05f86369.pdf) [S56](https://assets.watercare.co.nz/media/as_built_3d_model_specification_2cef742361.pdf) [S64](https://www.geonovum.nl/geo-standaarden/informatiemodel-kabels-en-leidingen-imkl)

**Решение организации.** Отделять соответствие структуре поставки, принятие документа и доказательство положения. Чужие численные допуски и категории ущерба не переносить в GeoService. FHWA показывает практическую пользу уточнения utility information, но не доказывает окупаемость нашего прототипа. [S13](https://www.fhwa.dot.gov/construction/dabs/library_hif24094.pdf) [S14](https://www.fhwa.dot.gov/utilities/pdf/hif22002.pdf) [S15](https://www.gov.uk/government/consultations/the-national-underground-asset-register-nuar/the-national-underground-asset-register-nuar-consultation) [S20](https://www.watercare.co.nz/builders-and-developers/tools-fees-and-resources/gis-maps)

## 11. Число знаков, GNSS indicator и независимость evidence

**Факт.** QField применяет GNSS-параметры при сборе; NGS предупреждает о пределах формальных оценок и разных определениях показателей. AUSPOS связывает сравнение результатов с версией обработки и неопределённостью. [S08](https://docs.qfield.org/how-to/navigation-and-positioning/gnss/) [S76](https://www.ngs.noaa.gov/OPUS/about.jsp) [S77](https://nweb.ngs.noaa.gov/OPUS-Projects/user_guide/section4.3.html) [S80](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/auspos)

**Новый вывод.** Малое reported accuracy, много десятичных знаков и повторная обработка файла — три разных свойства. Копии и решения из одного наблюдения не дают столько же независимых подтверждений. Не следует выбирать минимальную из доступных оценок uncertainty без понимания метрики.

**Решение организации.** При позиционной оценке сохранять вид метрики, уровень/смысл uncertainty, метод получения и зависимость свидетельств. Если они несовместимы с критерием, заключение остаётся непроверенным. Для текущей fixture никаких реальных GNSS-данных не создано и не запрошено.

## 12. Что действительно новое относительно существующей wiki

| Уже закреплено до этого исследования | Новое уточнение | Доменный эффект |
| --- | --- | --- |
| Нужен паспорт набора | Разделение логического набора, экземпляра, записи и актива | Сопоставление между окружениями становится явным |
| Сетка не равна точности | Четыре уровня основания: паспорт, конфигурация, persisted policy, наблюдаемые данные | Default перестаёт выглядеть доказательством происхождения |
| Неизвестность надо обозначать | Unknown, отсутствие свойства в контракте и обоснованное n/a различаются | Нет подстановки нуля или вымышленного «без трансформации» |
| Нужен пригодный метрический метод | Операция/ресурсы/область/эпоха условно входят в provenance | Две одинаковые CRS-метки не гарантируют воспроизводимость |
| Правка ограничена одной вершиной | Topological equality не подтверждает структуру fixture | Двухточечную линию нельзя допустить по одному ST_Equals |
| Receipt/current различаются | Совместимость отдельных чтений должна быть доказана или ограничена | Нет вымышленного атомарного снимка |
| Качество и основание оцениваются по цели | Формальный критерий допуска именно экземпляра упражнения | Технический допуск не закрывает позиционный вопрос |

USGS lifecycle, W3C best practices и OGC quality reports подкрепляют внимание к версии, цели и происхождению, но не предписывают нашу реализацию. S30/S31 — Engineering Reports, не нормативные стандарты, а S31 относится к экспериментальному исследованию качества, не непосредственно к коммунальной сети. [S27](https://www.usgs.gov/data-management/data-lifecycle) [S30](https://docs.ogc.org/per/17-025r2.html) [S31](https://docs.ogc.org/per/26-005r1.html) [S52](https://www.w3.org/TR/dwbp/)

## 13. Сопоставление с кодовой реальностью

Локальные источники: [[Code_wiki/архитектура/edit_geometry_fixture_metadata]], [[Code_wiki/архитектура/edit_version_api_readback]], [[Code_wiki/архитектура/frontend_save_recovery]], seed/policy/deps/read-service и frontend editor, указанные этими нодами. Это отдельная категория свидетельств, не часть 80 внешних документов.

По исходникам L-003 имеет baseline `(65.520,44.820) → (65.525,44.8205) → (65.530,44.820)`; учебный candidate меняет индекс 1 на `(65.525,44.8215)`. Seed create-once не переписывает старый dataset. Из этого следует кандидат для проверки, а не подтверждение содержимого любого volume.

Исходники задают XY/SRID4326, диапазоны координат и immutable GeometryPolicy версии: `xy_resolution`, `rounding_mode`, `version`. Default `0.0000001` поступает из settings при создании версии; reopen не обновляет snapshot. Отдельных persisted xyTolerance и transformation pipeline контракт не задаёт. Карта не показывает полный policy snapshot; один screenshot не закрывает сверку.

Прежнее доменное требование выводить сетку из metadata и реализованный способ передачи значения через settings требуют явного согласования происхождения, а не молчаливого принятия default. Это остаток FU-2026-10-11-001. Предложенная цепочка доказательств не утверждает, что нужные metadata уже реализованы.

## 14. Результат исследования и проверяемые ограничения

Приняты правила ручной квалификации за условную организацию; они конкретизируют существующую политику. При ingest нужны два атомарных понятия — идентичность экземпляра/записи и происхождение координатной операции — и спецификация допуска экземпляра, связанная с подготовкой правки. Новые domain events, aggregate, API и hard guards Save не обоснованы.

Два фактических вопроса metadata/fixture остаются открыты: интернет не читает локальную БД. Закрыть их можно отдельной сверкой конкретного экземпляра, persisted policy, AOI, структуры и before/current/candidate. Это техническая проверка, а не требование реальной организации или полевой кампании.

Гипотезы: текущий volume соответствует новому seed; UI показывает состояние того же token, что отчёт; любой экспорт сохранил структуру. Ни одна из них здесь не принята за факт. Для упражнения допускается ручная доказательная карточка; необходимость программной автоматизации определяется отдельной задачей.

## Реестр 80 внешних документов

Ниже каждый S-ID обозначает один документ. Все упоминания S-ID в ответах относятся к этому реестру. Версии руководств явно указаны там, где они зафиксированы URL; динамические страницы описывают состояние на дату обращения. Исторические региональные нормы используются как примеры, а не как действующие обязательства нашего проекта.

### S01 — Edit a utility network | ArcGIS Pro documentation

[Открытый документ](https://doc.esri.com/en/arcgis-pro/latest/help/editing/edit-a-utility-network.html). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Esri, руководство: условия редактирования utility network, роли геометрии и ассоциаций. Подтверждает сетевой смысл исходного UseCase; не доказывает распространённость продукта.

### S02 — Edit and validate subnetworks | Documentation

[Открытый документ](https://learn.arcgis.com/en/projects/edit-and-validate-subnetworks/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri, учебный сценарий: последовательность изменения и проверки подсетей. Разделяет исправление данных и готовность результата; tutorial не производственная статистика.

### S03 — Manage utility data using ArcGIS Utility Network | Documentation

[Открытый документ](https://learn.arcgis.com/en/projects/manage-utility-data-using-arcgis-utility-network/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri, учебный сценарий: работа с объектами и связями utility network. Помогает отделить изменение представления от управления активом; не контракт GeoService.

### S04 — Network topology | ArcGIS Pro documentation

[Открытый документ](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-network-topology.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri, руководство: network topology как отдельное представление связности. Успешная запись геометрии не означает обновлённый сетевой анализ.

### S05 — Dirty areas—ArcGIS Pro | Documentation

[Открытый документ](https://pro.arcgis.com/en/pro-app/3.3/help/data/utility-network/dirty-areas-in-a-utility-network.htm). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri, руководство 3.3: dirty areas обозначают участки, требующие validation. Исторически версионированный документ; не новый статус GeoService.

### S06 — Get started with ArcGIS Utility Network for wastewater | Documentation

[Открытый документ](https://learn.arcgis.com/en/projects/get-started-with-arcgis-utility-network-for-wastewater/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri, учебный wastewater-проект: отраслевой состав объектов и подсетей. Поддерживает вариативность роли редактора, но не универсальность водной модели.

### S07 — An introduction to the NUAR Data Model – Geospatial Insights

[Открытый документ](https://gdsgeospatial.blog.gov.uk/2024/08/13/an-introduction-to-the-nuar-data-model/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Geospatial Commission, описание NUAR: согласование разнородных схем поставщиков. Новый полезный контекст соответствия локальных данных общей модели.

### S08 — All about GPS, GNSS and NTRIP - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/how-to/navigation-and-positioning/gnss/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

QField, руководство GNSS/NTRIP: фильтры точности и сбор координат. Порог при записи точки не доказывает точность всей инженерной линии.

### S09 — Open-sourcing elements of NUAR – Geospatial Insights

[Открытый документ](https://gdsgeospatial.blog.gov.uk/2025/11/13/open-sourcing-elements-of-nuar/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

GDS, публикация 2025-11-13: открытие элементов NUAR и повторное использование подходов интеграции. Это технический опыт платформы, не открытый доступ ко всем сетевым данным.

### S10 — OGC Model for Underground Data Definition and Integration (MUDDI) Part 1: Conceptual Model

[Открытый документ](https://docs.ogc.org/is/23-024/23-024.html). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

OGC, стандарт MUDDI Part 1: различение objectID, recordID и systemID. Основание многослойной идентичности; конкретные ключи GeoService выбирает проект.

### S11 — Computation of coordinate operations between two CRS — PROJ 9.9.0 documentation

[Открытый документ](https://proj.org/en/stable/operations/operations_computation.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PROJ, документация выбора операций: область применения, точность и доступность ресурсов влияют на выбор преобразования. Пара CRS не определяет всю вычислительную цепочку.

### S12 — Appendix M – Data Specification Outline

[Открытый документ](https://www.contractsfinder.service.gov.uk/Notice/Attachment/b1a84db2-857d-427f-908d-a20a3fff82f9). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

NUAR, историческое приложение M к закупке: требования к поставке и согласованию модели. Используется как история требований, не актуальная редакция стандарта MUDDI.

### S13 — TechBrief: Lessons Learned for the Development of Digital As Built of Aboveground Assets from Colorado Department of Transportation’s Subsurface Utility Program

[Открытый документ](https://www.fhwa.dot.gov/construction/dabs/library_hif24094.pdf). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

FHWA, Colorado TechBrief: связь subsurface utility information и digital as-built. Контекст накопления исходных сведений; не перенос местных процедур автоматически.

### S14 — Tech Brief: Subsurface Utility Engineering Saves Time and Costs in Delaware

[Открытый документ](https://www.fhwa.dot.gov/utilities/pdf/hif22002.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

FHWA, Delaware TechBrief: применение subsurface utility engineering на проекте. Показывает ценность уточнения неизвестных условий; экономические результаты одного проекта не обобщаются.

### S15 — The National Underground Asset Register (NUAR) Consultation - GOV.UK

[Открытый документ](https://www.gov.uk/government/consultations/the-national-underground-asset-register-nuar/the-national-underground-asset-register-nuar-consultation). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

UK government, консультационный документ NUAR: проблема неоднородности и доступа к сведениям сетей. Материал обсуждения, не действующая норма для GeoService.

### S16 — Unitywater: ADAC XML Data Capture Guidelines, v2.1

[Открытый документ](https://www.unitywater.com/-/media/unitywater/pdf-accreditation-certification-documents/adac-xml-data-capture-guidelines-version-2.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Unitywater, ADAC v2.1: структурированный формат передачи asset data и правила захвата. Соответствие файлу поставки отделяется от происхождения координат.

### S17 — Pr11473 - Private Works PCD Manual

[Открытый документ](https://www.unitywater.com/-/media/unitywater/pdf-infrastructure-standards/pr11473---private-works-pcd-manual.pdf?hash=4BB5355C0C94427DC068DA031E7F28B2&sc_lang=en). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Unitywater, Pr11473: порядок оформления private works и документации. Обосновывает отдельный этап сдачи; не задаёт роль reviewer в нашем приложении.

### S18 — Asset recording

[Открытый документ](https://www.watercare.co.nz/builders-and-developers/tools-fees-and-resources/engineering-standards-framework/asset-recording). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Watercare, Asset recording: комплект требований для записи активов. Нужен как связка технического представления, документов и приёмки.

### S19 — Certificate of Acceptance

[Открытый документ](https://www.watercare.co.nz/builders-and-developers/compliance/certificate-of-acceptance). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Watercare, Certificate of Acceptance: административное принятие выполненных работ. Не тождественно сохранению feature или прохождению геометрической проверки.

### S20 — GIS maps

[Открытый документ](https://www.watercare.co.nz/builders-and-developers/tools-fees-and-resources/gis-maps). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Watercare, GIS maps: доступные сведения о сетях и ограничения их использования. Карта полезна для ориентирования, но не самостоятельное натурное подтверждение.

### S21 — 11 Procedure Guidance Notes – Major Works

[Открытый документ](https://www.urbanutilities.com.au/sfsites/c/cms/delivery/media/MCNYOLYHR4LZC6PJ33664RPYLYJE). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Urban Utilities, Procedure Guidance Notes – Major Works: требования к передаче данных о работах. Региональная практика, не универсальный нормативный процесс.

### S22 — Get started - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/get-started/tutorials/get-started-qfc/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

QFieldCloud, учебный запуск: подготовка проекта, передача и возврат правок. Различает готовность проекта к полю и результат синхронизации.

### S23 — System documentation - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/reference/qfieldcloud/system/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

QFieldCloud, system documentation: хранение проектов и обработка изменений. Сервисная копия не является независимым источником съёмки.

### S24 — Workflow - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/reference/qfieldcloud/workflow/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

QFieldCloud, workflow: операции push/sync и движение данных. Получение новой копии не доказывает намерение автора и отсутствие конфликта.

### S25 — 7. Topological and Geometrical Adjustments - Giswater Toolbox | Giswater Manual

[Открытый документ](https://giswater.gitbook.io/giswater-manual/7.-topological-and-geometrical-adjustments-giswater-toolbox). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Giswater, toolbox: геометрические и топологические проверки. Полезно как пример отдельного контроля; автоматические исправления не разрешены нашим first-save.

### S26 — 3. Basic work rules | Giswater Manual

[Открытый документ](https://giswater.gitbook.io/giswater-manual/3.-basic-work-rules). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Giswater, basic work rules: правила объектов и состояний сети. Эксплуатационное состояние нельзя вывести только из совпадения XY.

### S27 — Data Lifecycle | U.S. Geological Survey

[Открытый документ](https://www.usgs.gov/data-management/data-lifecycle). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

USGS, Data Lifecycle: описание, оценка и сохранение данных сопровождают жизненный цикл. Поддерживает повторную проверку применимости после изменений.

### S28 — 502.7 - Fundamental Science Practices: Metadata for USGS Scientific Data | U.S. Geological Survey

[Открытый документ](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

USGS, policy 502.7: требования к метаданным научных данных. Организационная политика USGS, не обязательная норма коммунального GIS.

### S29 — Persistent Identifiers (PIDs) for Metadata FAQ | U.S. Geological Survey

[Открытый документ](https://www.usgs.gov/science-data-management/persistent-identifiers-pids-metadata-faq). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

USGS, PID metadata FAQ: идентификатор metadata и идентификатор dataset имеют разные задачи. Заголовок паспорта не является ключом экземпляра.

### S30 — OGC Testbed-13: Quality Assessment Service ER

[Открытый документ](https://docs.ogc.org/per/17-025r2.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

OGC, Testbed-13 Quality Assessment Service ER: модель проверки качества и выражения результата. Engineering Report, не стандарт обязательных проверок.

### S31 — OGC Testbed-21: Data Quality for Integrity, Provenance and Trust Report

[Открытый документ](https://docs.ogc.org/per/26-005r1.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

OGC, Testbed-21 Data Quality for Integrity, Provenance and Trust, 2026: целостность, происхождение и доверие в экспериментальном контексте. Не стандарт utility data и не свидетельство готового evaluator.

### S32 — Jobs - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/reference/qfieldcloud/jobs/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

QFieldCloud, Jobs: конфликты применения дельт и стратегии разрешения. Last-wins не переносится как бизнес-правило GeoService.

### S33 — Advanced setup - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

QFieldCloud, Advanced setup: способы организации работы с источниками проекта. Настроенное соединение не подтверждает соответствие содержимого паспорту.

### S34 — Tips and Tricks QFieldCloud projects - QField Ecosystem Documentation

[Открытый документ](https://docs.qfield.org/get-started/tutorials/tips-tricks-qfc/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

QFieldCloud, Tips and Tricks: практические ограничения проекта и ключей при синхронизации. Пример вычисления fid не считается доказательством глобальной уникальности.

### S35 — 12.3. Editing — QGIS Documentation documentation

[Открытый документ](https://docs.qgis.org/3.40/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

QGIS 3.40, Editing: precision grid и topological editing могут затрагивать больше одной вершины/объекта. Версионированное руководство, не разрешение нормализовать baseline.

### S36 — ST_SetSRID

[Открытый документ](https://postgis.net/docs/ST_SetSRID.html). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

PostGIS, ST_SetSRID: установка обозначения CRS без преобразования координат. Используется для запрета подменять происхождение сменой метки.

### S37 — ST_Transform

[Открытый документ](https://postgis.net/docs/ST_Transform.html). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

PostGIS, ST_Transform: преобразование координат между системами. Нужна отдельно от установки SRID; результат зависит от заданной операции/ресурсов.

### S38 — ST_AsGeoJSON

[Открытый документ](https://postgis.net/docs/ST_AsGeoJSON.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_AsGeoJSON: представление и ограничение числа знаков; уменьшение точности вывода способно повредить геометрию. Экранный текст не канонический снимок.

### S39 — ST_ReducePrecision

[Открытый документ](https://postgis.net/docs/ST_ReducePrecision.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_ReducePrecision: округление на сетку с изменением представления/удалением малых элементов. Нельзя использовать как скрытую починку учебного baseline.

### S40 — ST_SnapToGrid

[Открытый документ](https://postgis.net/docs/ST_SnapToGrid.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_SnapToGrid: привязка всех точек к сетке с возможным схлопыванием. Валидность/простота и структура требуют отдельной проверки.

### S41 — ST_Equals

[Открытый документ](https://postgis.net/docs/ST_Equals.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_Equals: топологическое равенство допускает различие числа и порядка вершин. Недостаточно для условия одной внутренней вершины.

### S42 — ST_OrderingEquals

[Открытый документ](https://postgis.net/docs/ST_OrderingEquals.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_OrderingEquals: сравнение порядка и координат. Контраст с топологическим равенством; метод сопоставления в GeoService задаётся его контрактом.

### S43 — ST_CoveredBy

[Открытый документ](https://postgis.net/docs/ST_CoveredBy.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_CoveredBy: покрытие включает границу. Полезно различать покрытие всей линии и строгое внутреннее положение редактируемой вершины.

### S44 — ST_IsValid

[Открытый документ](https://postgis.net/docs/ST_IsValid.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PostGIS, ST_IsValid: геометрическая валидность в 2D. Не проверяет точность местоположения, пригодность активов и гидравлику.

### S45 — FAQ — PROJ 9.9.0 documentation

[Открытый документ](https://proj.org/en/stable/faq.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PROJ, FAQ: порядок осей и соглашения интерфейсов. EPSG-метка и последовательность чисел должны проверяться вместе.

### S46 — Geodetic transformation — PROJ 9.9.0 documentation

[Открытый документ](https://proj.org/en/stable/usage/transformation.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

PROJ, Geodetic transformation: цепочки преобразований и их параметры. Основание фиксировать метод, а не только входную/выходную CRS.

### S47 — projinfo — PROJ 9.9.0 documentation

[Открытый документ](https://proj.org/en/stable/apps/projinfo.html). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

PROJ, projinfo: сведения о кандидатах операций, сетках и области применения. Инструмент исследования возможной операции не доказывает фактически исполненную.

### S48 — PROV-DM: The PROV Data Model

[Открытый документ](https://www.w3.org/TR/prov-dm/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

W3C, PROV-DM: сущности, деятельности, агенты и derivation. Даёт словарь прослеживаемости, не требует внедрять RDF в приложение.

### S49 — Data Catalog Vocabulary (DCAT) - Version 3

[Открытый документ](https://www.w3.org/TR/vocab-dcat-3/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

W3C, DCAT 3: dataset, distribution и версии различаются. Помогает не отождествлять выгрузку с логическим набором.

### S50 — Data on the Web Best Practices: Data Quality Vocabulary

[Открытый документ](https://www.w3.org/TR/vocab-dqv/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

W3C, DQV: измерение качества связано с метрикой и объектом оценки. Не задаёт единого универсального численного порога.

### S51 — RFC 7946: The GeoJSON Format | RFC Editor

[Открытый документ](https://www.rfc-editor.org/rfc/rfc7946). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

IETF, RFC 7946: GeoJSON задаёт WGS84 и долготу/широту в градусах. Стандарт формата, не свидетельство исходной съёмки.

### S52 — Data on the Web Best Practices

[Открытый документ](https://www.w3.org/TR/dwbp/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

W3C, Data on the Web Best Practices: идентификаторы, версии и происхождение. Изменение содержания требует различимой редакции для воспроизводимости.

### S53 — Watercare: Asset Information and Data Standard, ноябрь 2020

[Открытый документ](https://assets.watercare.co.nz/media/ai_asset_information_and_data_standard_november_2020_b0f0de2baa.pdf). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Watercare, Asset Information and Data Standard: качество и передача asset information, проверка источников. Прочитаны релевантные разделы, не весь 340-страничный документ.

### S54 — Watercare: Standard for Producing CAD and Geospatial Drawings, ESF-500-STD-502

[Открытый документ](https://assets.watercare.co.nz/media/ESF_500_STD_502_6f05f86369.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Watercare, ESF-500-STD-502: требования к CAD/геопространственным чертежам и системам координат. Локальные datum-правила не переносятся в наш SRID4326.

### S55 — Watercare: Exchange Information Requirements

[Открытый документ](https://assets.watercare.co.nz/media/eir_watercare_e057cb8a01.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Watercare, Exchange Information Requirements: требования к структуре информационной поставки. Информация и геометрия входят в более широкий комплект передачи.

### S56 — Watercare: As-built 3D Model Specification

[Открытый документ](https://assets.watercare.co.nz/media/as_built_3d_model_specification_2cef742361.pdf). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Watercare, As-built 3D Model Specification: методы, статус и точность представления активов. Объектные требования не заменяются одним общим допуском.

### S57 — Coordinate transformations | Geodesy and positioning | OS

[Открытый документ](https://www.ordnancesurvey.co.uk/geodesy-positioning/coordinate-transformations). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Ordnance Survey, Coordinate transformations: модели перехода между системами. Доступность модели важна для воспроизводимости результата.

### S58 — OS Net & GNSS questions & answers | OS Net | OS

[Открытый документ](https://www.ordnancesurvey.co.uk/geodesy-positioning/os-net/faq). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Ordnance Survey, OS Net FAQ: GNSS, контроль и совместимость координатных оснований. Совпадение названий систем не гарантирует совместимость старых локальных материалов.

### S59 — Manage branch version conflicts—ArcGIS Pro | Documentation

[Открытый документ](https://pro.arcgis.com/en/pro-app/3.3/help/data/geodatabases/overview/manage-branch-version-conflicts.htm). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri 3.3, branch conflicts: обнаружение/рассмотрение конфликтов версий. Это отдельное решение после записи, не основание скрытого last-wins.

### S60 — Reconcile and post edits to a branch version—ArcGIS Pro | Documentation

[Открытый документ](https://pro.arcgis.com/en/pro-app/3.5/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.htm). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri 3.5, reconcile/post: согласование версии и публикация различаются. Post не следует автоматически из технического Save.

### S61 — Frequently asked questions—ArcGIS Pro | Documentation

[Открытый документ](https://pro.arcgis.com/en/pro-app/3.4/help/data/utility-network/faq.htm). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Esri 3.4, Utility Network FAQ: свойства и ограничения сетевой модели. Поддерживает отделение geometry storage от сетевых возможностей.

### S62 — EPANET | US EPA

[Открытый документ](https://www.epa.gov/water-research/epanet). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

US EPA, EPANET: расчёт гидравлики и качества воды. Сам факт наличия линии GIS не задаёт расчётную модель.

### S63 — EPANET USERS MANUAL, Release 2.2

[Открытый документ](https://19january2021snapshot.epa.gov/sites/static/files/2020-05/documents/epanet_userss_manual_2.2.0.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

US EPA, EPANET 2.2 manual, архивная копия: calibration data и сравнение расчёта с наблюдениями. Прочитаны релевантные разделы; не норматив приёмки GIS.

### S64 — Informatiemodel Kabels en Leidingen (IMKL) | Geonovum

[Открытый документ](https://www.geonovum.nl/geo-standaarden/informatiemodel-kabels-en-leidingen-imkl). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Geonovum, IMKL: отдельные спецификация данных, визуализация и модель сообщений для кабелей/труб. Региональная практика; законодательство Нидерландов не переносится.

### S65 — Synchronisation | Mergin Maps

[Открытый документ](https://merginmaps.com/docs/manage/synchronisation/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Mergin Maps, Synchronisation: версии проекта и объединение изменений. Версия пакета и состояние feature должны быть прослеживаемы.

### S66 — How to Recover Missing Data | Mergin Maps

[Открытый документ](https://merginmaps.com/docs/manage/missing-data/). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Mergin Maps, Recover Missing Data: восстановление локальных/серверных изменений. Восстановить данные не значит подтвердить их предметную правильность.

### S67 — merginmaps.com

[Открытый документ](https://merginmaps.com/blog/mergin-maps-best-practises-from-setup-to-fieldwork). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Mergin Maps, Best practices, 2026-09-16: подготовка и дисциплина полевой работы. Практическое руководство поставщика, не независимая оценка качества.

### S68 — Excavation and underground services - HSE

[Открытый документ](https://www.hse.gov.uk/electricity/information/excavations.htm). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

HSE, Excavation and underground services: сочетание планирования, обнаружения и безопасной работы. Карта сама по себе не подтверждает положение для раскопок.

### S69 — Avoiding danger from underground services HSG47

[Открытый документ](https://www.hse.gov.uk/pubns/priced/hsg47.pdf). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

HSE, HSG47: роли планов и обнаружения коммуникаций. Официальный URL при чтении перенаправлен на зеркало powerandcables; автор документа HSE, зеркало не второе свидетельство.

### S70 — Invulinstructie KLIC schadeformulier - Kadaster.nl zakelijk

[Открытый документ](https://www.kadaster.nl/-/invulinstructie-klic-schadeformulier). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Kadaster, KLIC damage form: отдельно описываются отсутствующая линия, изменение сети и расхождение положения/глубины. Категория ущерба не универсальный допуск GIS.

### S71 — Standard and Specifications

[Открытый документ](https://www.sla.gov.sg/qql/slot/u143/Newsroom/Circulars/Survey%20Services/Other%20Information/Standard%20and%20Specifications%20for%20Utility%20Survey%20in%20Singapore%20Version%201.0%20-%20Aug%202017.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Singapore Land Authority, Utility Survey v1.0, 2017: требования к съёмке коммуникаций, включая сбор до засыпки. Историческое региональное руководство, не доказательство наблюдения L-003.

### S72 — Microsoft Word - LINZS25000 - NZGD2000 Standard.doc

[Открытый документ](https://www.linz.govt.nz/sites/default/files/25000-LINZS25000%2520Standard%2520for%2520New%2520Zealand%2520Geodetic%2520Datum%25202000%2520_4.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

LINZ, LINZS25000, 2007: NZGD2000, datum и преобразования. Исторический стандарт для иллюстрации координатного основания; не заявлена его актуальность как нормы проекта.

### S73 — guide-coordinate-systems-great-britain

[Открытый документ](https://www.ordnancesurvey.co.uk/documents/resources/guide-coordinate-systems-great-britain.pdf). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Ordnance Survey, Guide to coordinate systems: datum, проекция и преобразование различаются. Назначение экранной проекции не меняет качество первичных наблюдений.

### S74 — Constraints of the PROV Data Model

[Открытый документ](https://www.w3.org/TR/prov-constraints/). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

W3C, PROV Constraints: причинные ограничения generation/use/invalidation. Помогает не описывать несовместимые снимки как одно доказательство.

### S75 — OGC API - Features - Part 2: Coordinate Reference Systems by Reference corrigendum

[Открытый документ](https://docs.ogc.org/is/18-058r1/18-058r1.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

OGC API Features Part 2: CRS ответа указывается отдельно через Content-Crs. Пример явного контракта представления; наш API не объявляется реализующим этот стандарт.

### S76 — NGS OPUS: обработка и точность GNSS

[Открытый документ](https://www.ngs.noaa.gov/OPUS/about.jsp). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

NOAA NGS, OPUS About/Accuracy: ошибки установки и окружения не устраняются малой формальной оценкой. Контроль независимым наблюдением усиливает основание, но не измеряет нашу линию.

### S77 — NGS OPUS Projects: Data & Solution Quality Thresholds

[Открытый документ](https://nweb.ngs.noaa.gov/OPUS-Projects/user_guide/section4.3.html). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

NOAA NGS, OPUS Projects §4.3: метрики качества имеют разные определения; рекомендованные пороги не являются спецификацией проекта. Новый источник против автоматического переноса чужих чисел.

### S78 — Geoscience Australia: AGRS tools, models and resources

[Открытый документ](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/australian-geospatial-reference-system/agrstoolsandmodels). Дата обращения: 2026-11-07. URL не найден точным сравнением в прежних RAW-исследованиях.

Geoscience Australia, AGRS tools, 2026-10-19: разные преобразования, модели высот и области применения. Выбор операции зависит от задачи и территории.

### S79 — Geoscience Australia: GDA2020

[Открытый документ](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/datums-projections/gda2020). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Geoscience Australia, GDA2020: реализация datum и эпоха привязки существенны. Австралийский пример не означает необходимость динамической модели для синтетической fixture.

### S80 — Geoscience Australia: AUSPOS

[Открытый документ](https://www.ga.gov.au/scientific-topics/positioning-navigation/positioning-australia/geodesy/auspos). Дата обращения: 2026-11-07. URL уже встречался в прежних RAW-исследованиях.

Geoscience Australia, AUSPOS, 2026-10-27: версия обработки и неопределённость важны при сравнении решений. Повторная обработка не считается новым независимым наблюдением.
