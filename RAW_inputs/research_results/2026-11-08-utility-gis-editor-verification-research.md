---
title: Utility GIS Editor — исследование методов проверки и охвата данных
type: research
status: active
created: 2026-11-08
updated: 2026-11-08
source: RAW_inputs/documents/UtilityGisEditorRole.md
tags: [domain-knowledge, research, simulated-organization, evidence]
---

# Utility GIS Editor: проверяемое изменение сведений о сети

## Задача и способ исследования

Исследуется UseCase из [[RAW_inputs/documents/UtilityGisEditorRole]], в контексте 15 вопросов последнего discovery о допуске экземпляра данных. Ответы вынесены в [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-answers]]. Это два результата **одного анализа на общем корпусе 78 внешних документов**, а не два независимых исследования. Все 78 документов открыты; прочитаны релевантные разделы, не заявляется сплошное чтение многосотстраничных руководств. Дата обращения — 08.11.2026.

Поиск охватил документацию редакторов и полевого обмена, сетевые модели, стандарты владельцев водных сетей, метаданные, геодезические преобразования и проверку результатов. Поисковые выдачи, недоступные страницы, языковые/версионные копии и повторные открытия не включены в число 78. В частности, исключены неоткрывшиеся Esri trace/terminals, отдельная страница Giswater Delete Feature, arXiv HTML, Contracts Finder attachment и два слишком больших PDF Philadelphia. R65 — прочитанное сообщение самого владельца в каталоге, а не эти PDF.

Точное сравнение URL с прежними файлами RAW_inputs/research_results до создания настоящих артефактов выявило **42 ранее не встречавшихся URL**. Это верхняя оценка новизны адресов: переезд Esri на doc.esri.com, /latest/ у QGIS и альтернативные адреса EPA могут обозначать уже известный документ. Устойчиво новые предметные опоры — Ohio DNR (R61), глава GIS integration Miami-Dade (R62), сообщение Philadelphia о not-constructed systems (R65), Fort Myers (R73–R74), разделение проверок Giswater (R78). Watercare и Water Corporation уже были известны: здесь их нельзя выдавать за впервые обнаруженные организации.

78 документов не означают 78 независимых подтверждений: Esri/VertiGIS принадлежат одной технологической экосистеме; разделы PostGIS, PROJ, GDAL описывают связанные механизмы; PROV-O развивает PROV-DM; MUDDI guide поясняет стандарт; руководства USGS взаимосвязаны. Отчёты участников и поставщика R63–R64 дают примеры, не статистическую проверку. Англоязычные водные сети представлены сильнее электрических, газовых, telecom и практики РФ/СНГ. Рыночную распространённость выборка не измеряет.

Обозначения ниже: **факт** — содержание внешнего документа в его области; **решение** — правило условной организации через 02_expert_oldman_ufa; **гипотеза** — возможное развитие, не принятое требование. Ни интервью, ни производственные измерения не проводились.

## 1. Что исходное описание роли объясняет хорошо и где переобобщает

Центральная ценность редактора — поддержание объяснимого представления инженерной сети. Он устанавливает, какой объект и какое состояние описываются, по какому основанию допустима правка, какие отношения должны сохраниться и кому пригоден результат. Это шире движения геометрии, но не означает, что один редактор лично выполняет все обследования, расчёты и утверждения.

**Факт.** Esri отделяет connectivity, containment и structural attachment; Giswater выделяет edit, O&M, hydraulic simulation и audit. Исходное описание правильно связывает роль с сетевой семантикой, однако обязанности и инструменты надо описывать по сценарию, а не универсальным списком навыков. [R53](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/connectivity.htm), [R54](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/associations.htm), [R75](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/work-environment.html)

**Ограничение.** Формулировки исходника о «двух основных архитектурах», «почти всегда» используемом стеке и обязательной последовательности всех работ не подтверждены репрезентативной выборкой. Невоспроизводимые ссылки вида turn… не используются как доказательства. Изученные руководства подтверждают существование механизмов, не их долю рынка. FU-2026-06-01-002 остаётся открытым; исходный RAW не переписывается.

**Решение.** Для ближайшего среза GeoService роль формулируется так: редактор в контексте WorkOrder/EditVersion осознанно изменяет разрешённую часть существующей линии, устанавливает исход сохранения и актуальное состояние, документирует основание и пределы доказательства. Приёмка съёмки, review/post, расчёт режима сети и физические работы — смежные процессы, не побочные эффекты Save.

## 2. Декомпозиция UseCase по результатам

| Этап | Предметный результат | Что его не доказывает | Источники |
|---|---|---|---|
| Выбрать сведения | Установлены экземпляр, запись, редакция и цель | Совпадение имени проекта или L-003 | R07, R13, R40, R45, R58 |
| Проверить основание | Известны метод, время, свойства и охват свидетельства | Файл называется as-built или красиво отображается | R59–R62, R73–R74 |
| Подготовить изменение | Есть допустимый candidate с сохранёнными отношениями | Доступность инструмента drag или snapping | R50, R53–R54, R76 |
| Сохранить | Установлен исход конкретной операции | Завершение отправки на клиенте | R06, R12, R14–R15 |
| Проверить модель | Проверены названные свойства на указанной области | Один зелёный статус без перечня проверок | R01–R03, R09, R55, R78 |
| Передать/принять | Результат пригоден для названного использования | Доставка, post или формальный выпуск по отдельности | R10, R56, R62, R67 |
| Использовать в эксплуатации | Применимы данные и расчётные предпосылки | Корректный XY или ненулевой Save | R19–R21, R75 |

Это аналитическая карта, не проект новых команд или состояний приложения. Полевое обследование, импорт, редактирование, публикация и эксплуатационная проверка не образуют одну транзакцию. Отказ позднего этапа не позволяет автоматически отменить уже совершённый ранний этап.

## 3. Новые уточнения предметного знания

### 3.1. Метод проверки относится к утверждению, а не ко всему объекту

**Факт.** Watercare различает неподтверждённую as-built модель, визуальную проверку и несколько инструментальных методов. В metadata объекта отдельно описываются статус, источник проверки и техника обследования. Ohio DNR требует сведения о способе получения и характеристиках точности; это локальные условия поставки. [R59](https://assets.watercare.co.nz/media/as_built_3d_model_specification_2cef742361.pdf), [R61](https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/engineering/designguidelines/doegisasbuilt)

**Вывод.** Слово verified без проверяемого свойства неоднозначно: подтвердили наличие объекта, XY, высоту, материал, связность или соответствие проекту? Метод способен поддерживать одни утверждения и не поддерживать другие. Внешний вид линии не удостоверяет глубину заложения.

**Решение.** В существующей ручной карточке указываются свойство, метод, источник/редакция, время, охват и вывод. Статус позиционной оценки остаётся отдельным. Это уточняет уже известное field_observation_acceptance; отдельный дублирующий aggregate или enum не нужен.

### 3.2. Охват — не одна рамка на карте

**Факт.** S551 требует survey extent, тип обследования, период capture, datum и accuracy class. Esri позволяет проверять topology в заданной extent. Giswater разделяет проверки графа, EPA, O&M и конфигурации. [R60](https://pw-cdn.watercorporation.com.au/-/media/watercorp/documents/about-us/suppliers-and-contractors/resources/design-standards/spatial-data-standards/s551-spatial-data-standard.pdf?hash=89BDD9F67400853882120EC1306E3239&rev=52ed8b38196e44cb970cada69fd4d06e), [R55](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/validate-a-network-topology.htm), [R78](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/check-project.html)

**Вывод.** Для утверждения важны пространственный участок, перечень объектов, проверенные свойства, момент/редакция данных и выполненные правила. Совпадение AOI с рамкой survey не доказывает обследование всех подземных объектов; viewport не означает проверку полного набора.

**Решение.** Охват фиксируется как «объекты/участки × свойства × состояние × метод». Если проверены endpoints, заключение не распространяется автоматически на весь изгиб. Если проверена одна fixture, вывод не называется проверкой dataset целиком. Новизна относительно 07.11 — операционализация уже принятого частичного scope в явную матрицу проверки.

### 3.3. Отрицательный результат и отсутствие наблюдения требуют разных записей

**Факт.** Philadelphia сообщает о требовании учитывать not-constructed systems до as-built approval. Это положительно установленный статус незавершённого строительства, а не просто пустой слой. USGS рекомендует определять missing-data и quality-indicator codes. [R65](https://water.phila.gov/gsi/planning-design/resources/), [R66](https://www.usgs.gov/data-management/data-dictionaries)

**Вывод.** «Не найдено в прочитанной выдаче», «проверка не выполнялась», «проверено и не соответствует», «известно, что не построено» имеют разную доказательную силу. Ограничения доступа, фильтр, устаревшая копия или ошибка sync могут объяснять отсутствие записи.

**Решение.** Для ручной сверки различаем соответствие, установленное несоответствие, непроверенность и обоснованную неприменимость. Это язык заключения, не новый серверный статус. Отсутствие L-003 в текущей выдаче сначала требует проверки контекста чтения; не означает уничтожения актива.

### 3.4. Преобразование поставки может менять предметный смысл

**Факт.** GDAL поддерживает фильтрацию, преобразование CRS и полей при конвертации. GeoJSON имеет параметры точности записи. QField предупреждает об изменяемости fid при синхронизации. USGS прямо отмечает риск потерь при конвертации форматов. [R35](https://gdal.org/en/stable/programs/ogr2ogr.html), [R37](https://gdal.org/en/stable/drivers/vector/geojson.html), [R13](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/), [R72](https://www.usgs.gov/data-management/file-formats)

**Вывод.** Успешный экспорт/импорт не доказывает сохранение identity, полноты объектов, размерности, атрибутов и точности представления. Назначить CRS и преобразовать координаты — различные операции. Визуально одинаковые данные могут иметь другую структуру вершин.

**Решение.** Для квалификации после переноса проверяются релевантные соответствия записей и свойства результата. Ссылка на исходный паспорт не заменяет сверку конечного экземпляра. Не предлагается внедрять новый ETL в ближайший срез.

### 3.5. Доставка, применение и приёмка разделены даже в готовых продуктах

**Факт.** QFieldCloud использует job применения изменений; Mergin описывает слияние и conflict copies; VertiGIS закрывает job через несколько действий с branch versions. [R06](https://merginmaps.com/docs/manage/synchronisation/), [R08](https://merginmaps.com/docs/manage/missing-data/), [R10](https://docs.vertigis.com/networks/latest/en/editor/vne_jm_close-jobs.html), [R12](https://docs.qfield.org/reference/qfieldcloud/workflow/), [R14](https://docs.qfield.org/reference/qfieldcloud/self_hosted/django_interface/)

**Вывод.** Сообщение одного этапа не подтверждает все downstream-результаты. При нескольких сервисах нужны результаты по каждому значимому участнику; общая надпись completed не заменяет проверку фактического содержания. Нельзя переносить детали vendor workflow как гарантии GeoService.

**Решение.** Сохраняется разделение receipt/current/baseline. Дополнительное уточнение карточки — какое именно действие завершено и в каком представлении проверен результат. Это развитие уже принятого assessment_delivery_and_acceptance, не новая независимая сущность.

### 3.6. Изменение формы, связности и жизненного состояния — разные намерения

**Факт.** Giswater Divide Arc создаёт две дуги при участии подходящего узла, End Feature меняет состояние объекта с привязкой к документу работ. Miami-Dade требует выделять разные сегменты при изменении характеристик трубы. [R76](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-divide.html), [R77](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/end-feature.html), [R62](https://www.miamidade.gov/resources/water/documents/wasd-cad-manual.pdf)

**Вывод.** Вставка вершины ради демонстрации не нейтральна к структуре данных, а разбиение линии или замена актива не сводятся к перемещению shape point. Даже при неизменном внешнем виде может меняться предметная идентичность.

**Решение.** Текущий Save не используется для подготовки удобного набора, смены узлов, разделения активов или оформления вывода из эксплуатации. Такие задачи получают отдельное основание и явный scope.

### 3.7. Сетевая и расчётная пригодность проверяются независимо

**Факт.** Dirty areas отражают состояние topology после редактирования; диаграмма может отставать от данных или topology. EPA рассматривает калибровку гидравлических/качественных параметров относительно измерений и назначения расчёта. [R01](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/dirty-areas-in-a-utility-network.htm), [R02](https://www.esri.com/arcgis-blog/products/arcgis-pro/data-management/how-do-utility-or-trace-network-changes-impact-network-diagrams), [R19](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P10113EM.TXT), [R20](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=2000D2C2.TXT), [R21](https://www.epa.gov/water-research/epanet)

**Вывод.** Связность — необходимое условие некоторых задач, но не полное доказательство эксплуатации. Корректная геометрия сама не подтверждает давление, режим задвижек или возможность изоляции участка.

**Решение.** Сохраняется POSITIONAL_ACCURACY_UNVERIFIED при отсутствии пригодного эталона. Техническое упражнение не называется эксплуатационной приёмкой; новый hard guard Save не вводится.

## 4. Сопоставление с существующей моделью и code reality

Уже приняты identity экземпляра/записи, происхождение координатной операции, независимость evidence, lifecycle основания и частичное заключение. Их повторное обнаружение не объявляется новым знанием. Настоящий вклад — более конкретное содержание карточки: проверяемое свойство и метод, матрица охвата, явные состояния знания, проверка результата переноса и разделение стадий обмена.

Опорные ноды: [[Wiki/concepts/field_observation_acceptance]], [[Wiki/concepts/assessment_statement_lifecycle]], [[Wiki/concepts/assessment_delivery_and_acceptance]], [[Wiki/concepts/dataset_instance_and_record_identity]], [[Wiki/concepts/coordinate_operation_provenance]], [[Wiki/specifications/demo_dataset_instance_qualified]].

Code reality сопоставлена с [[Code_wiki/архитектура/edit_geometry_fixture_metadata]] и ближайшими исходниками: seed L-003 содержит три вершины; ensure существующего набора не означает его обновление; persisted GeometryPolicy отличается от текущих settings; UI ограничен трёхвершинной линией. Это знание о репозитории, не наблюдение рабочего volume. Фактическая БД не опрашивалась.

Значение xy_resolution по умолчанию, SRID модели и координаты fixture нельзя копировать в графу «наблюдено» без чтения конкретного экземпляра. Синтетический candidate в интеграционных тестах не является измеренной истинной линией. Аналитические сценарии в ответах не запускались как тесты.

## 5. Последствия для модели и открытые ограничения

При ingest достаточно уточнить существующие concepts, policy, specification и use case. Нет основания создавать bounded context «верификация», общий флаг verified dataset, новый aggregate, таблицу, команду или event. Формат карточки пока документальный. Автоматизация её заполнения — гипотеза для отдельной задачи, не принятое требование.

Два фактических вопроса metadata/fixture и FU-2026-10-11-001 остаются открытыми: исследование даёт критерии проверки, не её результат. FU-2026-10-13-004 не закрывается. Прежние positional criteria, immutable baseline и текущие guards сохраняются. Противоречий с принятыми правилами не найдено; vendor/market claims исходника остаются в прежнем follow-up.

Недостоверно переносить внешние численные допуски: они зависят от класса объекта, метода, территории и назначения поставки. S551 прочитан в доступной редакции 2024, Fort Myers — как историческая практика; их текущая обязательность не заявляется. В R61 нельзя механически копировать сочетание названия datum и кода CRS без отдельной проверки. Нет оснований выбирать по этим документам новые нормы для GeoService.

## 6. Реестр прочитанных источников

Каждая строка — отдельный документ с вкладом и границей использования. Версии, разделы и даты указаны там, где существенны; /latest/ отражает страницу, доступную на дату обращения. Полные руководства не воспроизводятся. R59–R60 повторно использованы осознанно; новые адреса перечислены выше по содержательному вкладу.

| ID | Документ | Прочитанный предмет и ограничение |
|---|---|---|
| R01 | [Esri: Dirty areas](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/dirty-areas-in-a-utility-network.htm) | Изменения данных и состояние сетевой топологии; dirty area не является областью измерительной ошибки. |
| R02 | [Esri: Changes and network diagrams](https://www.esri.com/arcgis-blog/products/arcgis-pro/data-management/how-do-utility-or-trace-network-changes-impact-network-diagrams) | Согласованность диаграммы с editing space и topology space; актуальность одного представления не гарантирует другого. |
| R03 | [ArcGIS Maps SDK: Validate utility network topology](https://developers.arcgis.com/net/v200/winui/sample-code/validate-utility-network-topology/) | Пример проверки перед trace; наличие операции в SDK не подтверждает её выполнение в GeoService. |
| R04 | [VertiGIS: Glossary](https://docs.vertigis.com/networks/latest/en/editor/vne_glossary.html) | Job и long transaction; терминологическая опора для границ задания. |
| R05 | [VertiGIS: Resolve conflicts](https://docs.vertigis.com/networks/latest/en/editor/vne_jm_resolve-conflicts.html) | Сравнение конфликтующих свойств branch/default; выбор результата требует осмысления. |
| R06 | [Mergin Maps: Synchronisation](https://merginmaps.com/docs/manage/synchronisation/) | Слияние изменений, схемы и конфликты; sync не является проверкой предметной истины. |
| R07 | [Mergin Maps: Project history](https://merginmaps.com/docs/manage/project-history/) | Редакции проекта и просмотр изменений; история отделяется от текущего состояния. |
| R08 | [Mergin Maps: Missing data](https://merginmaps.com/docs/manage/missing-data/) | Диагностика conflict copies и изменений схемы; отсутствие на карте не доказывает физического отсутствия. |
| R09 | [VertiGIS: Working within a job](https://docs.vertigis.com/networks/latest/en/editor/vne_jm_working-within-the-job.html) | Сохранение, проверка Extent/All и завершение задания различаются. |
| R10 | [VertiGIS: Close jobs](https://docs.vertigis.com/networks/latest/en/editor/vne_jm_close-jobs.html) | Reconcile, post и удаление branch выполняются по этапам; итог задания нельзя читать как единую транзакцию всех сервисов. |
| R11 | [Giswater: Data model](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/data-model-giswater.html) | Узлы, дуги и состояния планируемого/действующего/устаревшего объекта; геометрия не исчерпывает семантику. |
| R12 | [QFieldCloud: Workflow](https://docs.qfield.org/reference/qfieldcloud/workflow/) | Push delta и её применение через job различаются; перед чтением результата требуется установить завершение обработки. |
| R13 | [QFieldCloud: Advanced setup](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/) | Изменяемый fid, UUID для отношений, ограничения offline-копии; перенос не гарантирует идентичность локального ключа. |
| R14 | [QFieldCloud: Django administration](https://docs.qfield.org/reference/qfieldcloud/self_hosted/django_interface/) | Просмотр delta JSON и отдельная проверка скачанных слоёв/вложений. |
| R15 | [Mergin Maps: Automatic sync](https://merginmaps.com/docs/field/autosync/) | Режим автоматизации и доступность соединения влияют на обмен; это не новая предметная приёмка. |
| R16 | [OGC MUDDI Part 1, 23-024](https://docs.ogc.org/is/23-024/23-024.html) | Модель подземных объектов и отношений; общий язык интеграции, не сертификат точности экземпляра. |
| R17 | [OGC: MUDDI for everyone, 24-045](https://docs.ogc.org/guides/24-045.pdf) | Объяснение межсистемной интеграции подземных данных; зависим от того же стандарта, не независимое подтверждение. |
| R18 | [USGS: Manage Quality](https://www.usgs.gov/data-management/manage-quality) | Пригодность для цели, предотвращение ошибок и контроль результата различаются. |
| R19 | [EPA: EPANET 2.2 User Manual](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P10113EM.TXT) | Раздел Calibration Report: расчёт сопоставляется с измерениями конкретного параметра. |
| R20 | [EPA: Water Distribution System Analysis, Reference Guide](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=2000D2C2.TXT) | Глава 4: пригодность к одной задаче калибровки не обеспечивает пригодность к другой; историческая методика. |
| R21 | [EPA: EPANET overview](https://www.epa.gov/water-research/epanet) | Гидравлика и качество воды — самостоятельные расчётные задачи; модель сети требует входных параметров. |
| R22 | [PostGIS: ST_SetSRID](https://postgis.net/docs/ST_SetSRID.html) | Назначение обозначения CRS не преобразует координаты. |
| R23 | [PostGIS: ST_Transform](https://postgis.net/docs/ST_Transform.html) | Преобразование координат зависит от операции и ресурсов; не равнозначно назначению SRID. |
| R24 | [PostGIS: ST_Equals](https://postgis.net/docs/ST_Equals.html) | Топологическое равенство допускает разные последовательности вершин; недостаточно для fixture. |
| R25 | [PostGIS: ST_OrderingEquals](https://postgis.net/docs/ST_OrderingEquals.html) | Порядок координат имеет отдельное значение; выбрать сравнение по цели. |
| R26 | [PostGIS: ST_IsValid](https://postgis.net/docs/ST_IsValid.html) | Проверяется валидность в 2D; это не натурная или эксплуатационная оценка. |
| R27 | [PostGIS: ST_IsSimple](https://postgis.net/docs/ST_IsSimple.html) | Простота линии — отдельный структурный предикат. |
| R28 | [PostGIS: ST_CoveredBy](https://postgis.net/docs/ST_CoveredBy.html) | Граница входит в отношение покрытия; применимость зависит от корректных входных геометрий. |
| R29 | [PostGIS: ST_ReducePrecision](https://postgis.net/docs/ST_ReducePrecision.html) | Снижение точности может удалить элементы геометрии; не использовать как скрытую подготовку baseline. |
| R30 | [PROJ: FAQ](https://proj.org/en/stable/faq.html) | Порядок осей CRS и привычный GIS XY различаются; необходимо установить соглашение конкретного интерфейса. |
| R31 | [PROJ: Coordinate operations computation](https://proj.org/en/stable/operations/operations_computation.html) | Выбор операции зависит от области и доступных ресурсов, а не только пары кодов CRS. |
| R32 | [PROJ: projinfo](https://proj.org/en/stable/apps/projinfo.html) | Фильтры области, grids, ballpark и accuracy; список кандидатов не доказывает историю импорта. |
| R33 | [PROJ: Transformation pipelines](https://proj.org/en/stable/usage/transformation.html) | Составные операции и эпохи; воспроизводимость требует знания цепочки. |
| R34 | [PROJ: Network capabilities](https://proj.org/en/stable/usage/network.html) | Загрузка и кэширование grids; окружение является зависимостью преобразования. |
| R35 | [GDAL: ogr2ogr](https://gdal.org/en/stable/programs/ogr2ogr.html) | Конвертация допускает фильтрацию, смену полей, размерности и CRS; проверяется содержательный результат. |
| R36 | [GDAL: GeoPackage driver](https://gdal.org/en/stable/drivers/vector/gpkg.html) | Таблицы и metadata контейнера; форматная корректность не доказывает происхождение объектов. |
| R37 | [GDAL: GeoJSON driver](https://gdal.org/en/stable/drivers/vector/geojson.html) | Настройка точности сериализации; число знаков не является паспортом измерительной точности. |
| R38 | [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) | Entity/activity/agent для описания происхождения; provenance не гарантирует истинность. |
| R39 | [W3C PROV-O](https://www.w3.org/TR/prov-o/) | Представление связей происхождения в онтологии; технически связан с PROV-DM, не независимая практика. |
| R40 | [W3C DCAT 3](https://www.w3.org/TR/vocab-dcat-3/) | Dataset и distribution разделены; другая выдача набора может иметь другое представление. |
| R41 | [W3C Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/) | Описание измерений качества и пригодности для задач; Group Note, не обязательная норма GeoService. |
| R42 | [W3C Dataset Usage Vocabulary](https://www.w3.org/TR/vocab-duv/) | Обратная связь и опыт использования; жалоба пользователя — свидетельство, требующее проверки. |
| R43 | [W3C Data on the Web Best Practices](https://www.w3.org/TR/dwbp/) | Метаданные, provenance и история редакций делают данные повторно используемыми. |
| R44 | [RFC 7946 GeoJSON](https://www.rfc-editor.org/rfc/rfc7946) | Порядок longitude/latitude и градусы в формате; формат не хранит полную историю измерений. |
| R45 | [OGC GeoPackage 1.4](https://www.geopackage.org/spec140/index.html) | Первичный ключ feature table и ссылки metadata; локальный integer key не равен глобальной идентичности актива. |
| R46 | [Geospatial Commission: NUAR data model](https://gdsgeospatial.blog.gov.uk/2024/08/13/an-introduction-to-the-nuar-data-model/) | Гармонизация неоднородных данных владельцев; единое представление не устраняет качество исходников. |
| R47 | [UK government: NUAR MVP](https://www.gov.uk/government/publications/nuar-minimum-viable-product-mvp/nuar-minimum-viable-product-mvp) | Историческое описание ограничений покрытия и использования MVP; не заявление о нынешнем полном охвате. |
| R48 | [Find a Tender: NUAR Data Ingestion and Transformation, 036942-2025](https://www.find-tender.service.gov.uk/Notice/036942-2025/PDF) | Требования к поставке, mapping и проверке; закупочный документ не свидетельствует об исполненной системе. |
| R49 | [QGIS: Working with projections, 3.44](https://docs.qgis.org/latest/en/docs/user_manual/working_with_projections/working_with_projections.html) | CRS слоя и проекта; отображение на лету не удостоверяет исходную привязку. |
| R50 | [QGIS: Editing, 3.44](https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html) | Topological editing может менять общие вершины соседних объектов; неподходящая аналогия для локальной правки GeoService. |
| R51 | [QGIS: Check geometry, 3.44](https://docs.qgis.org/latest/en/docs/user_manual/processing_algs/qgis/checkgeometry.html) | Проверки геометрии имеют собственные параметры; численная tolerance алгоритма не равна positional acceptance. |
| R52 | [QGIS: Vector geometry, 3.44](https://docs.qgis.org/latest/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html) | Операции меняют координаты/размерности и значения M; результат обработки требует новой проверки представления. |
| R53 | [Esri: Connectivity](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/connectivity.htm) | Геометрическое совпадение и ассоциации описывают разные способы связности; shape point не обязательно узел. |
| R54 | [Esri: Associations](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/associations.htm) | Connectivity, containment и structural attachment — разные отношения. |
| R55 | [Esri: Validate network topology](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/validate-a-network-topology.htm) | Проверка указанной extent и dirty areas; частичный запуск нельзя объявлять проверкой всей сети. |
| R56 | [Esri: Reconcile and post branch edits](https://pro.arcgis.com/en/pro-app/latest/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.htm) | Reconcile/post — отдельные операции; новое изменение между ними влияет на результат. |
| R57 | [Esri: Network rules](https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/network-rules.htm) | Правила ограничивают допустимые сетевые отношения; изменение правил меняет контекст проверки. |
| R58 | [Watercare: Asset Information and Data Standard, 2020](https://assets.watercare.co.nz/media/ai_asset_information_and_data_standard_november_2020_b0f0de2baa.pdf) | Поля equipment number и связь систем/полевой идентификации; локальный стандарт владельца. |
| R59 | [Watercare: As-Built 3D Model Specification, 2024](https://assets.watercare.co.nz/media/as_built_3d_model_specification_2cef742361.pdf) | Разделы 2–3: verified/unverified, источник проверки и техника обследования; визуальная проверка и инструментальное обследование различаются. |
| R60 | [Water Corporation: S551 Spatial Data Standard, редакция 17.11.2024](https://pw-cdn.watercorporation.com.au/-/media/watercorp/documents/about-us/suppliers-and-contractors/resources/design-standards/spatial-data-standards/s551-spatial-data-standard.pdf?hash=89BDD9F67400853882120EC1306E3239&rev=52ed8b38196e44cb970cada69fd4d06e) | Разделы 9–12: преобразования, survey extent, метод, горизонтальная/вертикальная основа и период capture; не утверждение об актуальности редакции в 2026. |
| R61 | [Ohio DNR: GIS As-Built Utility Record Guidelines, May 2026](https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/engineering/designguidelines/doegisasbuilt) | Метаданные метода и точности, геометрия и схема сдачи; локальные числа/CRS не переносить в GeoService. |
| R62 | [Miami-Dade WASD: CAD and GIS Standards, January 2026](https://www.miamidade.gov/resources/water/documents/wasd-cad-manual.pdf) | Глава 7: as-built сведения должны описывать установленное состояние; требования к сегментам и атрибутам, а не лишь внешнему виду. |
| R63 | [AWA Water e-Journal: Waikato R2R](https://info.awa.asn.au/water-e-journal/ewaikato-r2r-achieving-resilience-outcomes-through-collaboration) | Отчёт участников о федерации моделей и передаче asset information; пример организации работ, не независимая оценка эффективности. |
| R64 | [Recon: Watercare Asset Management](https://www.recon.nz/case-studies/watercare-asset-management) | Кейс поставщика обследования legacy assets; качественный пример проверки, не статистика рынка. |
| R65 | [Philadelphia Water: GSI Resource Directory, новости 2026](https://water.phila.gov/gsi/planning-design/resources/) | Прямое сообщение владельца о внесении not-constructed systems; отсутствие записи отличается от явно установленного состояния. |
| R66 | [USGS: Data Dictionaries](https://www.usgs.gov/data-management/data-dictionaries) | Определения полей, missing-data codes и правила; неизвестность нельзя превращать в ноль. |
| R67 | [USGS: Data Release](https://www.usgs.gov/data-management/data-release) | Данные, metadata и review составляют разные части выпуска; публикация не равна сохранению файла. |
| R68 | [USGS: Data Quality Assessment and Review](https://www.usgs.gov/data-management/data-quality-assessment-and-review-recommended-practices) | Проверки по этапам, сравнение с историей и фиксация anomalies; результат зависит от плана проверки. |
| R69 | [USGS: Data Management Plans](https://www.usgs.gov/data-management/data-management-plans) | Цель, стандарты и жизненный цикл определяют обращение с данными; не требование реальной организации для эксперимента. |
| R70 | [USGS: Metadata Creation](https://www.usgs.gov/data-management/metadata-creation) | Метаданные сопровождают данные, их редакция фиксируется; структурная валидация и содержательная проверка различаются. |
| R71 | [USGS: Data Standards](https://www.usgs.gov/data-management/data-standards) | Стандартизировать нужно значение и формат; формальная совместимость недостаточна. |
| R72 | [USGS: File Formats](https://www.usgs.gov/data-management/file-formats) | При конвертации возможны потери; визуальное оформление не должно быть единственным носителем metadata. |
| R73 | [Fort Myers: Request for Record/GIS Drawings, January 2025](https://www.fortmyers.gov/DocumentCenter/View/25497/AsBuilt-GIS-Data-Request-Form-Jan-2025) | Выдаваемые карты информационные и требуют полевой проверки; доступ к записи не удостоверяет положение. |
| R74 | [Fort Myers: Record Drawings / As-Built Requirements](https://www.fortmyers.gov/DocumentCenter/View/13386/Record-Drawings--As-Built-Requirements-PDF) | Разделы D–H: редакции, границы, точки связи, обследование и электронная поставка; исторический локальный документ. |
| R75 | [Giswater: Work environment](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/work-environment.html) | Разделены edit, O&M, EPA и audit; различать сохранённые данные, расчёт и историю. |
| R76 | [Giswater: Divide Arc](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-divide.html) | Разбиение разрешённым узлом создаёт две дуги; не эквивалент движения shape point. |
| R77 | [Giswater: End Feature](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/end-feature.html) | Перевод в obsolete связан с документом работ; не эквивалент удаления геометрии. |
| R78 | [Giswater: Check Project](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/check-project.html) | Отдельные проверки versions/project/graph/EPA/O&M; общий ярлык проверки скрывает разные свойства. |
