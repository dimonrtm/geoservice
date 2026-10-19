---
title: Utility GIS Editor — ответы на 15 вопросов об основании и результате правки
type: research
status: active
created: 2026-10-19
updated: 2026-10-19
source: RAW_inputs/documents/UtilityGisEditorRole.md; RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-research.md
tags: [research, discovery, utility-gis, simulated-organization]
confidence: high
related: [Wiki/policies/edit_change_justification_policy, Wiki/policies/intentional_line_editing_policy]
---

# Ответы на вопросы discovery: основание, изменение и передача

## Контекст решений

Ответы относятся к 15 вопросам последнего `/discover` о подготовке и проверке правки линии. Агент `02_expert_oldman_ufa` принимает приведённые правила за условную организацию. Реального интервью и реальной эксплуатирующей организации нет. Внешние факты служат основанием рассуждения, но не предписывают конкретные правила GeoService. Все примеры ниже синтетические, все сценарии — аналитические, не результаты runtime-тестов.

Использован общий с `2026-10-19-utility-gis-editor-change-basis-research.md` корпус **77 различных прочитанных веб-документов**. Полный реестр включён в этот файл; это тот же корпус, а не ещё 77 независимых подтверждений. Вопросы сгруппированы вокруг нового знания N01–N10 из аналитического файла. Ссылки S указывают на конкретные документы, из которых выведены различия; сама организационная норма явно помечена как решение.

Во всех ответах сохраняются текущие ограничения: одна существующая линия и одна внутренняя вершина, неизменяемый baseline, действующие guards, отсутствие автоматического positional verification, downstream review/post. Поля ручной карточки не становятся обязательными параметрами Save. Принятие модели не означает реализацию функций.

## 1. В задании написано «уточнить положение линии», но ожидаемое исправление не задано. Какого минимума достаточно?

**Основание:** пригодность определяется назначением и данными о происхождении [S04](https://www.w3.org/TR/vocab-dqv/)–[S08](https://www.fhwa.dot.gov/construction/dabs/library_hif24094.pdf), [S19](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework)–[S20](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework-guidance); предмет и наблюдаемое свойство различаются [S38](https://www.w3.org/TR/vocab-ssn/), [S75](https://docs.ogc.org/is/23-024/23-024.html).

**Решение:** до осмысленной правки установить пять вещей: какой объект и участок; какую ошибку или неопределённость устраняем; на основании какой конкретной редакции материала; какие свойства разрешено менять; по какому наблюдаемому результату оценим выполнение. Точная целевая координата не всегда должна быть записана заранее, но должен существовать воспроизводимый способ её получить и проверить. Формулировка «сделать ровнее» без предметного основания недостаточна.

Например: «для указанного участка L-003 уточнить XY внутренней вершины по обозначенному фрагменту схемы; endpoints и идентичность актива сохраняются; сопоставить итог с этим свидетельством и отдельно указать непроверенную точность». Если источник не позволяет выбрать положение, агент исследует пробел либо моделирует учебное основание с явной меткой. Нельзя выдавать придуманную координату за полевую. До уточнения допустим анализ, но нет основания объявлять изменение выполнением задания. Это организационная проверка намерения, не дополнительный серверный запрет technical Save.

## 2. После первого Save задание уточнили. Когда это уточнение, а когда новая задача?

**Основание:** revision классифицируется по воздействию [S03](https://www.w3.org/TR/vocab-dcat-3/), [S54](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data); зависимости и повторное открытие работы отделены от её содержания [S10](https://doc.arcgis.com/en/workflow-manager/latest/help/dependencies.htm)–[S11](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-holds.htm), [S14](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-jobs.htm).

**Решение:** уточнение остаётся в той же работе, если сохраняются целевой объект/участок, тип намерения, ожидаемый результат и допустимая операция. Новая редакция текста связывается с прежней, а сохранённый результат проверяется на соответствие ей. Уточнение может потребовать переоценки и без новой задачи: например, раскрыта ранее неясная погрешность источника.

Смена объекта, расширение на другую ветвь, замена актива вместо исправления данных или новый самостоятельный результат требуют отдельной задачи/согласованного изменения объёма. «Новая задача» здесь — решение о границе работы, не обещание существующего API. Прежнюю правку нельзя молча присвоить новому намерению. Записываем, что было сохранено при старом задании, что теперь остаётся пригодным и что требует исправления. Не отменяем прежний Save только потому, что текст изменился; не меняем baseline задним числом.

## 3. Выяснилось, что отредактирована соседняя линия. В каком порядке исправлять ошибку?

**Основание:** выбранное представление, реальная идентичность объекта и связи сети различаются [S47](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/version-changes-branch.html), [S51](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/nonspatial-objects.html), [S63](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/containment.html)–[S68](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/set-edge-connectivity-for-line-features.html); Save и Discard имеют разные области действия [S60](https://doc.esri.com/en/arcgis-pro/latest/help/editing/save-or-discard-edits.html).

**Решение:** остановить новые записи и сначала установить исход ошибочного действия. Если оно не сохранено — отбросить локальную попытку. Если сохранено — прочитать current, определить затронутую линию и объяснить ошибку выбора. Затем выбрать разрешённую компенсацию: возврат к baseline только при его актуальной пригодности и действующих условиях; иначе отдельный разбор, а не прямой ремонт БД.

После подтверждения исправления ошибочной записи заново установить нужный объект и допустимый контекст работы. Ограничение «одна линия в версии» не обходится правкой второй линии поверх первой. Если устранение ошибки временно невозможно, это не мешает исследовать правильный объект, но запрещает выдавать пакет за завершённое исправление. Неизвестный outcome сначала разрешается существующим recovery. Получатель видит обе причины: исправление ошибочной записи и выполнение исходной задачи. История первого Save остаётся; геометрический откат не стирает ошибку выбора.

## 4. Часть работы выполнима, остальная нет. Как доказать самостоятельность частичного результата?

**Основание:** workflow dependencies выделяют зависимые этапы [S10](https://doc.arcgis.com/en/workflow-manager/latest/help/dependencies.htm)–[S11](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-holds.htm); разные участки обследования имеют разную доказательную основу [S05](https://www.fhwa.dot.gov/programadmin/sueindex.cfm)–[S08](https://www.fhwa.dot.gov/construction/dabs/library_hif24094.pdf); verification отделена от correction [S86](https://pro.arcgis.com/en/pro-app/latest/help/data/validating-data/results-and-life-cycle-phases.htm).

**Решение:** частичный результат принимается как самостоятельный только при собственной понятной цели, точной области, достаточном основании и отсутствии незавершённой зависимости, без которой он искажает смысл сети. Проверка: если получатель увидит только эту часть и её ограничения, сможет ли он корректно использовать её для заявленной цели?

Исправление одного подтверждённого изгиба может быть полезно как локальное уточнение карты. Половина переноса реконструированного участка, создающая ложную связь со старой ветвью, самостоятельным результатом не является. Записываем принятую часть, непроверенную/отклонённую часть, зависимость, ограничение использования и следующий шаг. Процент выполнения и число Save не являются доказательством полезности. Технически сохранённое промежуточное состояние может остаться рабочим draft, но не объявляется выполненным заданием или готовым review package. При неделимом намерении готовность всей задачи остаётся неподтверждённой.

## 5. Линия уже соответствует заданию. Что доказывает результат без перемещения?

**Основание:** качество оценивается относительно назначения [S04](https://www.w3.org/TR/vocab-dqv/), [S19](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework); сравнение истории и периодическая оценка не требуют обязательного изменения [S18](https://www.usgs.gov/data-management/data-quality-assessment-and-review-recommended-practices); differences показывает конкретную область сравнения [S47](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/version-changes-branch.html).

**Решение:** зафиксировать проверенный объект, актуальное сохранённое состояние, критерий, редакцию основания, область сравнения, метод и вывод «изменение не требуется». Сохраняем явные ограничения: подтверждено соответствие учебному заданию, а не реальная точность, если её evidence отсутствует.

Не нужно двигать вершину туда-обратно для демонстрации активности. No-op ответ сервера подтверждает отсутствие изменения от конкретного запроса, но сам не доказывает соответствия заданию. Если current уже отличается от baseline из-за прежних Save, «сейчас менять не требуется» не означает «версия не изменена». Для бизнес-задачи проверка может дать полезный результат без правки; для учебной цели «показать сохранение ненулевого изменения» такая ветка её не выполняет — нужен другой допустимый учебный пример. Эти два критерия фиксируются раздельно.

## 6. В новой редакции источника изменились подпись или пояснение, но не координаты. Когда достаточно обновить ссылку?

**Основание:** USGS различает поправки, не меняющие понимания данных, и изменения с воздействием на использование [S54](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data); DCAT разделяет версии описания и данных [S03](https://www.w3.org/TR/vocab-dcat-3/); metadata несут смысл и ограничения [S16](https://www.usgs.gov/data-management/metadata-creation), [S82](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data).

**Решение:** сравнить не только XY, но и референт подписи, единицы, CRS, время наблюдения, метод, область, статус актива и ограничения. Достаточно актуализировать ссылку, если доказано, что затронутые утверждения семантически эквивалентны; сохранить прежнюю ссылку в истории и краткое объяснение эквивалентности.

«улицa» → «улица» — обычно редакторская поправка. «проектная» → «исполнительная», «кабель A» → «кабель B», новая дата обследования или уточнение о неизвестной точности — изменение основания, даже при одинаковой геометрии. Тогда переоцениваем зависимые выводы, не обязательно перемещаем линию. Если невозможно установить характер изменения, не предполагаем его несущественным. Текущее заключение отмечаем как требующее проверки в затронутой области; весь набор автоматически непригодным не объявляем.

## 7. Источник отозван после Save, но другой материал поддерживает те же координаты. Можно ли оставить результат?

**Основание:** invalidation и derivation различаются [S01](https://www.w3.org/TR/prov-o/)–[S02](https://www.w3.org/TR/prov-dm/); отзыв данных требует внимания к последствиям [S54](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data); quality evidence должно иметь область [S17](https://www.usgs.gov/data-management/documenting-data-quality-considerations), [S75](https://docs.ogc.org/is/23-024/23-024.html).

**Решение:** да, после нового обоснования. Сначала установить причину и охват отзыва. Затем проверить, что альтернативный материал относится к тому же объекту, времени и свойству, не является копией отозванного ошибочного наблюдения и достаточен по действующему критерию. Совпадение XY само по себе недостаточно.

Если проверка пройдена, сохранить геометрию, выпустить новую запись основания/оценки с фактической датой и связью с прежним решением. Не утверждать, что новое основание было известно при старом Save. Пересмотреть downstream заключения по их зависимостям; прежнее approval не переносится автоматически. Если основание пока недостаточно, запись остаётся историческим фактом и, при допустимом процессе, рабочим draft с ограничением использования. Возврат к baseline выбирается отдельно: baseline тоже мог зависеть от того же плохого источника. Отзыв документа не является командой Revert.

## 8. Два согласующихся источника оказались копиями одного наблюдения. Как меняется достаточность?

**Основание:** PROV описывает происхождение и копирование [S01](https://www.w3.org/TR/prov-o/)–[S02](https://www.w3.org/TR/prov-dm/), DWBP различает производителя и издателя [S37](https://www.w3.org/TR/dwbp/); фото допускает производные аннотации [S23](https://docs.qfield.org/how-to/project-setup/pictures/).

**Решение:** учесть их как одну цепь происхождения, сохранив оба представления, если они помогают чтению. Согласие копий подтверждает согласованность передачи, но не даёт независимого подтверждения полевого положения. Пересмотреть прежний вывод, если он опирался на независимость двух свидетельств.

Одно качественное, пригодное наблюдение может быть достаточным: правила «всегда нужны два источника» не вводим. И наоборот, десять копий слабого замера не устраняют неопределённость. Если общий первоисточник неизвестен, независимость не подтверждена; агент исследует метаданные и цепочку передачи. Независимость указывать по измерению: самостоятельный осмотр может подтвердить наличие актива, но использовать ту же координатную основу и не быть независимым подтверждением XY. Число документов не превращаем в процент уверенности.

## 9. Принята только часть полевого материала. Как обозначить границу?

**Основание:** visit может содержать несколько событий/параметров [S30](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/add-visit.html), качество обследования зависит от участка [S05](https://www.fhwa.dot.gov/programadmin/sueindex.cfm), а качество данных имеет несколько измерений [S19](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework)–[S20](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework-guidance).

**Решение:** использовать явную таблицу утверждений, например: `источник/редакция/страница или feature id → объект/участок → свойство → решение → причина → связанное сохранение/оценка`. Решения: принято для объявленной цели; отклонено с причиной; ещё не проверено. Это значения ручной карточки, не новые backend enum.

Синтетический пример: положение внутренней вершины принято для локальной правки; глубина из той же схемы не проверена; состояние «в эксплуатации» отклонено как неподтверждённое; соседняя ветвь вне охвата. Не ставим общую отметку «файл принят». Оригинальный материал не обрезаем и не переписываем, чтобы не потерять контекст и противоречия. Получатель должен видеть не только зелёную часть, но и отсутствие вывода по остальному. При новой редакции сопоставляем фрагменты повторно, поскольку номер страницы или порядок объектов мог измениться.

## 10. Дата наблюдения неизвестна, известна только дата поступления. Что пересмотреть?

**Основание:** phenomenonTime и resultTime различны [S38](https://www.w3.org/TR/vocab-ssn/), NPMS разделяет дату условий и подачи [S39](https://www.npms.phmsa.dot.gov/PipelineData.aspx), metadata описывают temporal extent [S82](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data).

**Решение:** не подставлять поступление вместо наблюдения. Пересмотреть утверждения «это последнее положение», «после реконструкции», «существовало на дату работ», «источник новее противоречащего» и пригодность для текущего operational state. Также проверить, не было ли качество признано достаточным из-за предполагаемой свежести.

Неизвестное время не делает материал бесполезным для всех целей: он может помогать идентификации или историческому сопоставлению. При ограниченном интервале можно записать именно интервал и его основание, не выдумывая точный день. Дату поступления сохраняем для аудита передачи. Агент исследует доступные признаки; если дата не установлена, формулирует более узкий вывод или явно задаёт синтетическую дату только для учебного набора. Пробел не перекладывается на несуществующего сотрудника. Результат, требующий доказательства актуальности, остаётся неподтверждённым.

## 11. Несколько Save одной вершины выполнены по одному основанию. Когда достаточно одного пояснения?

**Основание:** история происхождения и история изменений связаны, но не тождественны [S01](https://www.w3.org/TR/prov-o/)–[S03](https://www.w3.org/TR/vocab-dcat-3/); журнал задания отличается от tracking объекта [S53](https://doc.arcgis.com/en/workflow-manager/latest/help/view-job-history.htm), [S57](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/introduction-to-editor-tracking.html).

**Решение:** одно пояснение может покрывать последовательность, если неизменны объект, участок, цель, способ интерпретации, редакция основания и критерий. В карточке указать, какие сохранения оно охватывает и какое состояние является итоговым. Сохранённые промежуточные координаты остаются видимыми как промежуточные; общий текст не объявляет их все приемлемыми результатами.

Новое пояснение нужно при новом источнике или его существенной редакции, выборе другой трактовки, отклонении от задания, компенсации ошибки либо смене цели. Небольшая величина сдвига не освобождает от объяснения изменившегося смысла. Поздно добавленное пояснение получает фактическое время, а не время первого Save. Идемпотентный retry той же команды не считается новым предметным намерением. Если receipt и current относятся к разным состояниям, пояснение должно точно назвать, к чему относится вывод, а не ссылаться только на «последнюю правку».

## 12. Ошибка в пояснении: где опечатка, а где изменение причины?

**Основание:** уровень revision зависит от влияния на понимание/использование, а не длины исправленного текста [S54](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data); metadata участвуют в смысле данных [S16](https://www.usgs.gov/data-management/metadata-creation), [S82](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data).

**Решение:** опечаткой считается изменение, не меняющее объект, утверждение, источник, время, метод, критерий и причину выбора. Исправляем с отметкой кто/когда/что исправил. Если замена одной цифры меняет ID объекта, она существенна; если «не подтверждено» превращается в «подтверждено», это новое заключение.

При существенном изменении сохраняем прежний текст как историческое основание, записываем новую редакцию и оцениваем затронутые результаты. Геометрию менять не обязательно; но нельзя сохранить прежний статус готовности только потому, что координаты совпадают. Поздняя корректировка не должна создавать впечатление, что прежняя запись была сделана по уже исправленной причине. Если исходная причина вообще не была зафиксирована, честно отмечаем ретроспективную реконструкцию, её основания и ограничения. Техническая история Save не заменяет эту проверку.

## 13. Координаты те же, но объяснение меняется с исправления данных на физическое изменение актива. Продолжаем ту же работу?

**Основание:** lifecycle операции Replace/End и planned/operative различаются [S28](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/replace-feature.html), [S31](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/new-psector.html)–[S34](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-fusion.html); физическая сеть включает больше геометрии [S61](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-terminal-management.html)–[S70](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-error-features.html); Watercare разделяет приёмку актива и документы [S41](https://www.watercare.co.nz/builders-and-developers/compliance/certificate-of-acceptance).

**Решение:** автоматически продолжать нельзя. Это существенная смена намерения: нужно установить, какой актив существовал и когда, произошла ли замена/перенос, сохраняется ли идентичность, что подтверждает выполненные физические работы. Одинаковые координаты не отвечают на эти вопросы.

Прежнюю работу фиксируем как исправление представления с её реальным основанием. Физическое изменение оформляется отдельной задачей или явным новым объёмом, если процесс это поддерживает. В текущем geometry-only срезе такое изменение не кодируется перестановкой вершины или заменой пояснения. Нельзя задним числом превратить информационную правку в подтверждение строительства. Пока lifecycle evidence нет, допустим отдельный разбор гипотезы о физическом изменении; реальность работ и эксплуатационная пригодность не утверждаются. Права на геометрическое редактирование не дают полномочий на ввод актива.

## 14. Последний Save ошибочен, более ранние полезны. Когда восстановить предыдущее сохранённое положение, а когда baseline?

**Основание:** просмотр исторических данных и изменение operational data различаются [S29](https://docs.giswater.org/master/ca/docs/giswater/for-users/additional-toolbars/audit.html); Common Ancestor имеет конкретную семантику [S47](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/version-changes-branch.html); Discard не отменяет произвольный прежний Save [S60](https://doc.esri.com/en/arcgis-pro/latest/help/editing/save-or-discard-edits.html).

**Решение:** выбирать состояние по действующему намерению и evidence. Если прежняя сохранённая форма достоверно известна, остаётся обоснованной, а ошибочен только последний шаг, допустима новая корректирующая запись этой формы с актуальным token и новым CommandId. Она проходит все существующие проверки. Нельзя replay старой команды использовать как способ навязать старую форму текущему состоянию.

Revert к baseline выбирается, если нужно снять весь сохранённый change set и сам baseline допустим. Он не предпочтительнее только потому, что старше. Если ни прежняя форма, ни baseline не имеют пригодного основания, сначала разбор. При коррекции сохраняются before/after и причина; предыдущие события не удаляются. UI произвольного выбора исторического состояния этим решением не считается реализованным; текущая кнопка сохранённого возврата также ещё не доказывает полный рабочий сценарий. После записи отдельно читаем current и baseline diff; полезные прежние изменения не должны исчезнуть незаметно.

## 15. Передаём сохранённую правку с незавершённым разбором основания. Что означает принятие работы?

**Основание:** reassignment, hold, closure и история имеют отдельную семантику [S10](https://doc.arcgis.com/en/workflow-manager/latest/help/dependencies.htm)–[S11](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-holds.htm), [S53](https://doc.arcgis.com/en/workflow-manager/latest/help/view-job-history.htm), [S77](https://doc.arcgis.com/en/workflow-manager/latest/help/work-on-jobs.htm)–[S78](https://doc.arcgis.com/en/workflow-manager/latest/administer/users-groups-roles-and-privileges.htm); correction не равна verification [S86](https://pro.arcgis.com/en/pro-app/latest/help/data/validating-data/results-and-life-cycle-phases.htm).

**Решение:** получатель явно подтверждает «принял обязанность продолжить разбор», называя задачу, объект/версию и следующий шаг. Это не «геометрия верна», не positional VERIFIED, не approval и не закрытие quality case. До реализации подтверждение хранится в ручной карточке.

Передача содержит доказанный или неизвестный исход последнего действия, отдельно прочитанное current, baseline diff, точные редакции оснований, принятое/непроверенное/отклонённое, причину разбора, ограничения использования, оставшиеся действия и принятую обязанность. Если получатель только получил ссылку, передача ответственности ещё не доказана. Новая запись требует действующих прав и контекста, разрешённого намерения и условий existing recovery; передача не обходит guards. В условной организации агент оформляет это как моделируемое действие персоны, не выдумывает реальное письмо или реального сотрудника. При невозможности принять результат сохраняется открытый разбор с понятным следующим шагом.

## Минимальная ручная карточка

| Поле | Смысл |
| --- | --- |
| WorkOrder / EditVersion / feature / участок | Однозначный предмет работы |
| Намерение и редакция задания | Что считаем выполнением |
| Сохранения и актуальное чтение | Известный исход отдельно от нынешнего состояния |
| Источник, редакция, точный фрагмент | К чему относится основание |
| Корневое наблюдение и производные | Зависимость копий и преобразований |
| Время наблюдения / результата / поступления | Разные даты; неизвестность не скрывается |
| Утверждение, свойство, область | Что именно принимается, а что нет |
| Решение и ограничения | Применимо / недостаточно / требуется переоценка с причиной |
| Изменение основания | Что изменилось и какие выводы затронуты |
| Автор и фактическое время | Не приписывать поздний текст прошлому Save |
| Передача и следующий шаг | Принятая обязанность отдельно от правильности результата |

Это семантическая форма, не проект миграции БД и не новый обязательный request payload. Если реквизит неизвестен, пишется «не установлено» с последствием для вывода.

## Аналитическая проверка согласованности ответов

| Сценарий | Ожидаемый исход правила |
| --- | --- |
| Три PDF происходят от одного замера | Одна цепь наблюдения; число копий не повышает независимость |
| Исправлена подпись, сменившая идентичность линии | Существенная revision; переоценка даже при неизменном XY |
| Отозван источник, независимый новый достаточен | Новое обоснование текущей формы без фиктивного геометрического Save |
| Отозван источник, baseline зависит от него же | Нет автоматического безопасного Revert |
| Задание выполнено ранее, current отличается от baseline | Результат «новая правка не нужна», прежний diff не скрывается |
| Последний шаг ошибочен, предыдущий обоснован | Новая коррекция после актуального чтения, не retry старого намерения |
| Передан разбор, получатель подтвердил обязанность | Разбор продолжается; quality approval не возникает |
| Неизвестно время наблюдения, известна загрузка | Ограничение выводов об актуальности; время не подменяется |

Матрица не является журналом пройденных тестов. Числовые допуски, инварианты версии, retention и границы review/post не изменены. Реализация и сверка metadata/fixture остаются отдельной работой.

## Реестр 77 источников

Дата обращения: 2026-10-19. Большие документы читались по релевантным разделам. Доступность, границы и метод подсчёта раскрыты в парном исследовании. Ни один источник не считается реальным evidence положения L-003.

| ID | Документ | Прочитанное содержание и роль в анализе | Относительно реестра 2026-10-18 |
| --- | --- | --- | --- |
| S01 | [PROV-O](https://www.w3.org/TR/prov-o/) | PROV-O: revision, quotation, primary source и invalidation различаются; ссылка на копию не доказывает независимое наблюдение. | Новый URL |
| S02 | [PROV-DM](https://www.w3.org/TR/prov-dm/) | PROV-DM: derivation описывает получение сущности из другой; основание решения можно проследить через преобразования. | Повторно проверен |
| S03 | [DCAT 3 — versioning](https://www.w3.org/TR/vocab-dcat-3/) | DCAT 3, versioning: редакции dataset, distribution и metadata различаются; политика выпуска версий задаётся поставщиком. | Новый URL |
| S04 | [Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/) | DQV: качество описывается для оценки пригодности к употреблению; единая универсальная оценка не предписана. | Новый URL |
| S05 | [Subsurface Utility Engineering - Subsurface Utility Engineering - Utility Program - Design - Federal Highway Administration](https://www.fhwa.dot.gov/programadmin/sueindex.cfm) | FHWA SUE: QL D/C/B/A отражают способ получения сведений; требуемая детализация зависит от риска и участка. | Новый URL |
| S06 | [Applying Subsurface Utility Engineering to Highway and Road Projects - Subsurface Utility Engineering - Utility Program - Design - Federal Highway Administration](https://www.fhwa.dot.gov/programadmin/sueshow.cfm) | FHWA, применение SUE: исходниками служат разные виды планов и записей; оцифровка сама может внести ошибку. | Новый URL |
| S07 | [SUE Then and Now - Subsurface Utility Engineering - Utility Program - Design - Federal Highway Administration](https://www.fhwa.dot.gov/programadmin/history.cfm) | FHWA, история SUE: обследование, surveying и управление данными образуют инженерный процесс; designating и locating различаются. | Новый URL |
| S08 | [TechBrief: Lessons Learned for the Development of Digital As Built of Aboveground Assets from Colorado Department of Transportation’s Subsurface Utility Program](https://www.fhwa.dot.gov/construction/dabs/library_hif24094.pdf) | FHWA HIF-24-094, стр. 5–6: CDOT объединяет survey, SUE, CAD и GIS; фазы проекта требуют разных данных. Это конкретный кейс. | Повторно проверен |
| S09 | [It gets MUDDI – a quest for better subsurface data (The MUDDI for everyone guide)](https://docs.ogc.org/guides/24-045.pdf) | OGC 24-045, раздел 4: подземные данные скрыты и разнородны; MUDDI связывает категории объектов. Руководство, не сам стандарт. | Новый URL |
| S10 | [Dependencies—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/dependencies.htm) | Workflow Manager Dependencies: этапы могут зависеть от других заданий; завершение обследования может освобождать редактирование. | Новый URL |
| S11 | [Show and manage holds—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-holds.htm) | Workflow Manager Holds: отсутствие данных допускает приостановку; снятие hold — отдельное действие с правами. | Новый URL |
| S14 | [Manage jobs—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-jobs.htm) | Workflow Manager Manage jobs: закрытие и повторное открытие — действия workflow; техническая возможность закрыть не доказывает качество. | Новый URL |
| S16 | [Metadata Creation — U.S. Geological Survey](https://www.usgs.gov/data-management/metadata-creation) | USGS Metadata Creation: описание отвечает who/what/when/where/how/why; metadata нужно поддерживать при изменениях. | Новый URL |
| S17 | [Documenting Data Quality: Considerations — U.S. Geological Survey](https://www.usgs.gov/data-management/documenting-data-quality-considerations) | USGS Documenting Data Quality: фиксируются методы, flags, проверки и неопределённость, особенно для производных данных. | Повторно проверен |
| S18 | [Data Quality Assessment and Review: Recommended Practices — U.S. Geological Survey](https://www.usgs.gov/data-management/data-quality-assessment-and-review-recommended-practices) | USGS Assessment and Review: проверки выполняются в важных точках процесса, сравниваются история и полевые заметки. | Повторно проверен |
| S19 | [The Government Data Quality Framework - GOV.UK](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework) | UK Government Data Quality Framework: completeness, validity, accuracy и timeliness — разные измерения. | Новый URL |
| S20 | [The Government Data Quality Framework: guidance - GOV.UK](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework-guidance) | UK Framework guidance: качество и критичность данных оцениваются по использованию; ограничения сообщаются потребителю. | Новый URL |
| S21 | [Jobs - QField Ecosystem Documentation](https://docs.qfield.org/reference/qfieldcloud/jobs/) | QFieldCloud Jobs: успех Process Project означает обработку, а не правильность конфигурации; применение delta может дать конфликт. | Повторно проверен |
| S22 | [Digitize and edit - QField Ecosystem Documentation](https://docs.qfield.org/how-to/data-collection/digitize/) | QField Digitize and edit: режим просмотра отделён от оцифровки; формы и закреплённые значения влияют на ввод. | Повторно проверен |
| S23 | [Attachment widget - QField Ecosystem Documentation](https://docs.qfield.org/how-to/project-setup/pictures/) | QField Attachment widget: фото можно аннотировать и связывать отношением 1:N; производный снимок сохраняет зависимость от оригинала. | Повторно проверен |
| S24 | [All about GPS, GNSS and NTRIP - QField Ecosystem Documentation](https://docs.qfield.org/how-to/navigation-and-positioning/gnss/) | QField GNSS: доступны quality metadata и ограничения digitizing по качеству; измерение и ручное изменение следует различать. | Повторно проверен |
| S25 | [Advanced setup - QField Ecosystem Documentation](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/) | QField Advanced setup: мобильные deltas и перепаковка проекта различаются; schema changes опасны при неотправленных правках. | Повторно проверен |
| S26 | [Permissions and Roles - QField Ecosystem Documentation](https://docs.qfield.org/get-started/tutorials/permissions/) | QField Permissions: роли дают возможности изменения данных; право редактировать не является подтверждением достоверности. | Повторно проверен |
| S28 | [13. Replace feature — Giswater Documentation  documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/replace-feature.html) | Giswater Replace feature: замена связана с прежним объектом, датой и workcat; это иной смысл, чем сдвиг вершины. | Повторно проверен |
| S29 | [Audit Module — Giswater Documentation  documentació](https://docs.giswater.org/master/ca/docs/giswater/for-users/additional-toolbars/audit.html) | Giswater Audit Module: snapshot и журнал выбранных таблиц обеспечивают реконструкцию; временный исторический слой не меняет рабочую сеть. | Новый URL |
| S30 | [8. Add Visit — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/add-visit.html) | Giswater Add Visit: посещение связывается с объектами, параметрами, событиями и документами; визит не тождественен правке. | Повторно проверен |
| S31 | [30. New planning sector — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/new-psector.html) | Giswater New psector: включённый плановый контекст меняет состояние создаваемых объектов; planned отделяется от operative. | Повторно проверен |
| S32 | [16. End Feature — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/end-feature.html) | Giswater End Feature: прекращение эксплуатации связано с объектом и construction file; нельзя выражать его одной геометрией. | Повторно проверен |
| S33 | [11. Divide Arc — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-divide.html) | Giswater Divide Arc: разделение создаёт две дуги при допустимом узле; это изменение структуры и идентичности. | Повторно проверен |
| S34 | [12. Fuse Arc — Giswater Documentation  documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-fusion.html) | Giswater Fuse Arc: объединяются дуги одного каталога, отдельно выбирается судьба узла; не простая редакция координат. | Повторно проверен |
| S35 | [5. Data model for Giswater — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/data-model-giswater.html) | Giswater Data model: arcs/nodes/connecs/links и virtual arcs имеют разные роли; движение связанного узла может затронуть линии. | Повторно проверен |
| S36 | [26. Result manager — Giswater Documentation documentation](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/result-manager.html) | Giswater Result manager: входные данные расчёта, архивный и corporate result различаются; описание результата не равно его пересчёту. | Повторно проверен |
| S37 | [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/) | W3C DWBP, §8.4: издатель может отличаться от производителя; происхождение и история изменений нужны потребителю. | Новый URL |
| S38 | [Semantic Sensor Network Ontology](https://www.w3.org/TR/vocab-ssn/) | SSN/SOSA §4.3.2.4 и §4.7.2.5: phenomenonTime — время применимости результата, resultTime — завершение наблюдения. | Новый URL |
| S39 | [Pipeline Data](https://www.npms.phmsa.dot.gov/PipelineData.aspx) | PHMSA NPMS Pipeline Data: охват исключает distribution/gathering gas; дата состояния отличается от ежегодной подачи, карта имеет ограничения. | Новый URL |
| S40 | [Asset recording](https://www.watercare.co.nz/builders-and-developers/tools-fees-and-resources/engineering-standards-framework/asset-recording) | Watercare Asset recording: сведения об активах нужны для maintenance, renewals и обмена; опубликованы разные виды требований. | Новый URL |
| S41 | [Certificate of Acceptance](https://www.watercare.co.nz/builders-and-developers/compliance/certificate-of-acceptance) | Watercare CoA: приёмка актива, подключение и финальный комплект документов — отдельные этапы. Страница содержит старое уведомление 2024 года. | Новый URL |
| S42 | [Add and configure Add Attachment—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/add-attachment.htm) | Workflow Manager Add Attachment: linked и embedded материалы различаются; после pause вложения остаются, но это не проверка их содержания. | Новый URL |
| S43 | [NUAR project update - November 2023 - GOV.UK](https://www.gov.uk/government/publications/national-underground-asset-register-project-update-november-2023/nuar-project-update-november-2023) | NUAR update November 2023: предусмотрен feedback о реальных условиях; общая карта дополняет обследование, а не заменяет его. | Повторно проверен |
| S45 | [Reconcile and post edits to a branch version — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.html) | Esri reconcile/post: получение изменений Default и публикация в Default — разные операции; Save сам по себе их не выполняет. | Повторно проверен |
| S46 | [Manage branch version conflicts — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/manage-branch-version-conflicts.html) | Esri conflicts: представление выбирается при разрешении конфликта; повторный reconcile/post может очистить историю разрешения. | Повторно проверен |
| S47 | [View branch version changes — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/version-changes-branch.html) | Esri Differences: показываются Current, Target и Common Ancestor; сравнение зависит от момента создания/последнего reconcile. | Повторно проверен |
| S48 | [Attribute rule fundamentals — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/an-overview-of-attribute-rules.html) | Esri attribute rules: immediate constraints и deferred validation решают разные задачи; факт записи не означает прохождения всех проверок. | Повторно проверен |
| S49 | [Dirty areas — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/dirty-areas-in-a-utility-network.html) | Esri dirty areas: отображают изменения, ещё не отражённые topology; скрытие слоя не устраняет несогласованность. | Повторно проверен |
| S50 | [Validate a network topology — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/validate-a-network-topology.html) | Esri validate topology: проверяется заданная область; после reconcile могут возникнуть новые dirty areas, post возможен и с ними. | Повторно проверен |
| S51 | [Junction and edge objects — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/nonspatial-objects.html) | Esri nonspatial objects: сетевые объекты могут не иметь собственной геометрии; синтезированная форма не становится съёмкой. | Повторно проверен |
| S52 | [Configure a trace — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/configure-a-trace.html) | Esri trace configuration: тип трассы, барьеры, параметры и subnetwork definition влияют на результат. | Повторно проверен |
| S53 | [View job history—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/view-job-history.htm) | Workflow Manager History: журнал включает hold, reassignment, attachment и reopen; история задания отличается от геометрической истории. | Новый URL |
| S54 | [Guidance on Documenting Revisions to USGS Scientific Digital Data Releases — U.S. Geological Survey](https://www.usgs.gov/office-of-science-quality-and-integrity/guidance-documenting-revisions-usgs-scientific-digital-data) | USGS revisions, Levels 1–5: различаются редакторская поправка, изменение данных/структуры и отзыв; важен эффект на использование. | Новый URL |
| S57 | [Introduction to editor tracking — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/introduction-to-editor-tracking.html) | Esri editor tracking: записывает создание и последнее изменение; существовавшие до включения записи могут иметь NULL, не все schema changes отслеживаются. | Новый URL |
| S60 | [Save or discard edits — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/editing/save-or-discard-edits.html) | Esri Save/Discard: Discard откатывает несохранённое после последнего Save; не произвольную уже сохранённую историю. | Повторно проверен |
| S61 | [Terminal management — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-terminal-management.html) | Esri terminals: порты и внутренние пути влияют на traversability; переключение пути меняет поток без обязательной правки линии. | Повторно проверен |
| S62 | [Connectivity and traversability — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/connectivity-and-traversability.html) | Esri connectivity/traversability: геометрическая/ассоциативная связность отличается от проходимости при заданных атрибутах. | Повторно проверен |
| S63 | [Containment associations — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/containment.html) | Esri containment: контейнер и содержимое могут иметь разные геометрии; вложение не означает прохождение ресурса через контейнер. | Повторно проверен |
| S64 | [Structural attachment associations — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/structural-attachments.html) | Esri structural attachments: опорная конструкция и проводящий ресурс объект связаны, но выполняют разные функции. | Повторно проверен |
| S65 | [Connectivity associations — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/connectivity.html) | Esri connectivity associations: связь возможна между несовпадающими пространственно объектами; совпадение пикселей недостаточно. | Повторно проверен |
| S66 | [Connectivity and associations — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-connectivity-and-associations.html) | Esri connectivity and associations: геометрия и явные отношения — разные механизмы; правила применяются на разных этапах. | Повторно проверен |
| S67 | [Feature restrictions — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/feature-restrictions.html) | Esri feature restrictions: ограничения классов и настраиваемые network rules различаются; не всякое желаемое соединение допустимо. | Повторно проверен |
| S68 | [Set edge connectivity for features — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/set-edge-connectivity-for-line-features.html) | Esri edge connectivity: End vertex и Any vertex зависят от политики типа; внутренняя вершина не всегда пассивная точка. | Повторно проверен |
| S69 | [Network rules — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/network-rules.html) | Esri network rules: правила ограничивают допустимые отношения; удаление поддерживающего правила может сделать прежние отношения ошибочными. | Повторно проверен |
| S70 | [Errors — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-error-features.html) | Esri errors: нарушение может относиться к geometry, attributes, rules или subnetwork; не каждую ошибку исправляет сдвиг. | Повторно проверен |
| S71 | [Trace utility networks — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-tracing-utility-networks.html) | Esri tracing: старт, остановки, барьеры и вид результата определяют охват; результат трассы не равен всему объекту исследования. | Повторно проверен |
| S72 | [Update a subnetwork — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/update-a-subnetwork.html) | Esri update subnetwork: это отдельная операция с сохранёнными правками и актуальной topology, не синоним Save. | Новый URL |
| S73 | [Underground cables - HSE](https://www.hse.gov.uk/ELECTRICITY/underground.htm) | HSE Underground cables, Using cable plans: планы дают ориентир; сведения о кабелях требуют отдельного установления на местности. | Новый URL |
| S74 | [Avoiding danger from underground services HSG47](https://www.hse.gov.uk/pubns/priced/hsg47.pdf) | HSG47, раздел Use and limitation of plans: схема и обследование имеют ограничения; цифровой учёт не разрешает физические работы. | Повторно проверен |
| S75 | [OGC Model for Underground Data Definition and Integration (MUDDI) Part 1: Conceptual Model](https://docs.ogc.org/is/23-024/23-024.html) | MUDDI §8.1–8.3: core/extension и traceability связывают объекты с observations/evidence; объём модели зависит от use case. | Новый URL |
| S76 | [Spatial Data on the Web Best Practices](https://www.w3.org/TR/sdw-bp/) | Spatial Data on Web BP: идентификатор Spatial Thing, геометрия, CRS и точность представления требуют явного описания; документ — Group Draft Note. | Новый URL |
| S77 | [Work on jobs—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/help/work-on-jobs.htm) | Workflow Manager Work on jobs: pause, cancel, complete, hold и зависимости имеют разные последствия. | Новый URL |
| S78 | [Users, groups, roles, and privileges—ArcGIS Workflow Manager — Documentation](https://doc.arcgis.com/en/workflow-manager/latest/administer/users-groups-roles-and-privileges.htm) | Workflow Manager Roles: права на reassignment, closure, attachments и holds разделены; полномочие имеет конкретную область. | Новый URL |
| S79 | [Utility network reference for editing — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/editing/utility-network-reference-for-editing.html) | Esri editing reference: network-aware инструменты могут добавлять вершины/изменять связи по правилам; перенос UX без модели опасен. | Повторно проверен |
| S80 | [Edit a utility network — ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/editing/edit-a-utility-network.html) | Esri Edit utility network: изменение geometry, associations и network attributes требует согласования topology и последующей публикации. | Повторно проверен |
| S81 | [Data Best Practice Guidance](https://www.ofgem.gov.uk/sites/default/files/2025-11/Data_Best_Practice_Guidance_CLEAN%26ACC.pdf) | Ofgem DBP, принцип 7: качество зависит от нужд пользователей, проблемы учитываются с решением; V3.2 доступная редакция без изменения содержания. | Новый URL |
| S82 | [502.7 - Fundamental Science Practices: Metadata for USGS Scientific Data — U.S. Geological Survey](https://www.usgs.gov/survey-manual/5027-fundamental-science-practices-metadata-usgs-scientific-data) | USGS SM502.7 §4: metadata описывают происхождение, качество, смысл и ограничения; общая запись БД не всегда заменяет описание особого набора. | Новый URL |
| S83 | [502.8 - Fundamental Science Practices: Review, Approval, and Release of USGS Scientific Data — U.S. Geological Survey](https://www.usgs.gov/survey-manual/5028-fundamental-science-practices-review-approval-and-release-usgs-scientific-data) | USGS SM502.8 §4: preliminary, approved и dynamic data различаются; публикация предварительных сведений не тождественна approval. | Новый URL |
| S84 | [502.6 - Fundamental Science Practices: Scientific Data Management Lifecycle — U.S. Geological Survey](https://www.usgs.gov/survey-manual/5026-fundamental-science-practices-scientific-data-management-lifecycle) | USGS SM502.6 §3: управление данными продолжается весь lifecycle; способы получения и преобразования документируются. | Новый URL |
| S85 | [Configure the mobile app—ArcGIS Field Maps — Documentation](https://doc.arcgis.com/en/field-maps/android/use-maps/configure-field-maps.htm) | Field Maps configuration: accuracy/confidence, averaging, offset и snapping — отдельные настройки, влияющие на происхождение координаты. | Новый URL |
| S86 | [Error results and their life cycle — ArcGIS Pro documentation](https://pro.arcgis.com/en/pro-app/latest/help/data/validating-data/results-and-life-cycle-phases.htm) | Data Reviewer error lifecycle: correction и verification раздельны; неприемлемое исправление возвращается на review. | Новый URL |

Сверка реестров: 35 URL отсутствуют в реестре 2026-10-18, 42 повторно проверены. Сопоставлены URL с нормализацией старых адресов ArcGIS Pro; новизна URL не гарантирует независимость содержания. Содержательная новизна установлена отдельно в N01–N10.
