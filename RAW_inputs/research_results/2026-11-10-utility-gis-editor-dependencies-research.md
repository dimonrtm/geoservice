---
title: Utility GIS Editor — исследование зависимых работ и новых знаний
type: research
status: active
created: 2026-11-10
updated: 2026-11-10
source: RAW_inputs/documents/UtilityGisEditorRole.md
tags: [utility-gis, work-dependency, research, simulated-organization]
confidence: high
---

# Анализ UseCase и прироста доменной модели

## Предмет, метод и ограничения

Дата чтения — 10.11.2026. Исходная роль — [[RAW_inputs/documents/UtilityGisEditorRole]]. Конкретная исследовательская задача — три открытых вопроса DISC-2026-11-10-01/02/03 после discovery: обязательность результата предшественника, изменение зависимости и взаимное ожидание. Анализ охватывает также соседние процессы: полевой осмотр, as-built, конфигурацию сети, топологию, версии, передачу данных и эксплуатационное применение. Узкий first-save не принят за границу исследования.

Прочитаны относящиеся к задаче разделы **75 разных внешних документов**; не заявляется чтение всех страниц длинных руководств. Реестр ниже содержит прямой URL, извлечённый факт и предел переноса каждого источника. Страницы выдачи, ошибки доступа, языковые/версионные дубли и повторные открытия не посчитаны. Например, недоступная IBM Maximo страница predecessor и ошибочные адреса Giswater исключены. Этот анализ и [[RAW_inputs/research_results/2026-11-10-utility-gis-editor-dependencies-answers]] используют один общий корпус 75 документов, а не два независимых исследования по 75.

После нормализации URL **25 новых адресов**, 50 встречались в прежних RAW research_results. Сравнение выполнено со всеми существовавшими до этих двух файлов исследованиями: убраны fragment и завершающий slash; Esri doc.esri/arcgis-pro сопоставлен pro.arcgis/pro-app, версии help и QGIS приведены к latest, .html/.htm уравнены. Это проверка новизны адреса, не гарантия новой идеи или независимого наблюдения. Новые адреса отмечены в реестре.

Корпус: Esri — 39 документов; QField/OPENGIS — 9; Giswater — 13; QGIS — 5; W3C — 3; FHWA — 4; Lands Department Hong Kong — 1; University of Arkansas — 1. документы одного издателя не являются независимыми свидетельствами. Выборка преимущественно документационная, не статистическая: она доказывает механизмы и встречающиеся требования, но не распространённость роли, частоту отказов или выгоду GeoService.

Внешние факты имеют S-ID; собственные выводы обозначены как интерпретации; нормативные правила выбраны expert_repson за условную организацию в отдельном файле ответов. Ни один источник не доказывает фактическую пригодность L-003, работу evaluator или post в приложении. Текущие руководства latest/master зависят от версии продукта. Доступность partial-post в Esri не означает её наличие или разрешение в GeoService.

## 1. Что представляет собой UseCase

Цель редактора — передать пригодное для определённого использования изменение сетевой модели или обоснованное заключение, а не просто получить успешный Save. Точка входа может быть нарядом, обнаруженным расхождением, полевым обследованием, результатом строительства или необходимостью исправить опубликованное состояние. Успешный выход имеет четыре компонента: определённый объект и область; доказанный смысл изменения; проверки относительно установленного состояния; понятный получателю результат и ограничения.

| Этап | Внешнее основание | Предметный результат и риск |
| --- | --- | --- |
| Определить работу | S01–16, S62–64 | Наряд, родительская связь и обязательная предпосылка различаются. Порядок работ нельзя вывести только из общего проекта |
| Собрать исходные сведения | S17–27, S49, S67, S70, S75 | Полевой визит, передача, применение и принятие данных происходят отдельно; съёмка после засыпки может утратить нужное наблюдение |
| Подготовить представление | S19–20, S30–32, S38, S65–74 | Планируемый, действующий и выведенный объект различаются; графическая правка не всегда изменение физического актива |
| Изменить и проверить | S28–29, S37, S39–41, S50–54, S56–59 | Geometry/topology/configuration/derived subnetworks имеют разные проверки и охват; чистота одного результата не доказывает качество всех данных |
| Согласовать и опубликовать | S33–36, S42–45, S55 | Reconcile, конфликты, post и установление исхода самостоятельны; техническая операция не заменяет организационную приёмку |
| Передать зависимой работе | S01–02, S15, S26, S46–48, S60–64 | Потребителю нужен конкретный применимый результат. Успешный статус производителя недостаточен |
| Исправить или перепланировать | S08–10, S34, S59, S63–64 | Отмена задания не отменяет данные; замена обязательства требует сохранения истории и новой ответственности |

Это интерпретация совместно прочитанных источников. Исходное утверждение о «доминировании двух стеков» не подтверждено: наличие подробных руководств не измеряет рынок. FU-2026-06-01-002 остаётся открытым. Не восстановимые внутренние cite-маркеры исходного RAW не использованы как внешние источники.

## 2. Почему связи работ недостаточно

Workflow Manager различает последовательные, параллельные и staggered зависимости; управляемая dependency привязана к удерживаемому шагу и шагу предшественника (S01–02). Иерархия parent/child существует отдельно (S04, S09). Это сильное основание различать три отношения: происхождение задания, информирование и обязательное ожидание результата.

Интерпретация для модели: «Б зависит от А» недоопределено. Неясно, ждёт ли Б осмотра, заключения о пригодности, принятого набора координат или опубликованной правки. Нужны ожидаемый deliverable, область, редакция и точка потребления. Например, осмотр клапана способен дать пригодный отчёт без post (S67); публикация соседней геометрии может быть обязательна только перед финальной проверкой Б. Запрещать всю подготовку Б из-за любой связи — чрезмерное правило; разрешать всю работу по closed А — недостаточное.

Общее XY-пересечение не даёт точного графа зависимостей: connectivity и structural associations связывают разные виды объектов (S30–32, S38), а topological editing способен затронуть общие вершины (S50). Проверка зависимости должна учитывать смысл и область результата, а не только пересечение AOI.

## 3. Принятый результат и его текущая применимость

В QFieldCloud delta job ID ещё не означает применение; даже успех подготовки проекта не гарантирует правильную конфигурацию (S17, S26). Offline-копия может не выполнять PostGIS triggers, shared dataset может не синхронизироваться обычным путём (S23, S25). Поэтому цепочка «отправлен → применён → доступен → принят для цели» содержит разные утверждения.

PROV разделяет результат, действие и участника; DQV оставляет оценку пригодности относительно цели потребителю (S46–48). Наш вывод: сохранять исторический факт приёмки отдельно от текущего разрешения использовать результат. Изменение default, отозванное evidence или обновлённые правила могут потребовать переоценки (S34, S39). Это не повод переписать прежнюю приёмку.

Подтверждение не обязательно положительное заключение о геометрии. Если А поручено обследовать участок и сообщить установленное состояние, полный отчёт об обнаруженном дефекте может выполнить обязанность А; Б затем выбирает разрешённую коррекцию. Но если обязательство сформулировано «предоставить пригодные координаты», тот же отчёт обязанности не выполняет. Содержание условия важнее слова completed.

## 4. Замена и частичное исполнение

FHWA R15B рекомендует явный учёт конфликтов и альтернатив; кейс Kentucky связывает альтернативы со сроками/затратами и сохраняет историю документов (S62–63). Международный обзор показывает процедуру согласованной эскалации (S64). Это свидетельства полезности явной координации, не источник конкретных полномочий GeoService.

Интерпретация: отмена производителя не устраняет потребность получателя. Замена evidence и изменение обязательства различны. Первое отвечает «достаточен ли другой источник для той же цели»; второе — «кто согласовал иную цель, область, срок или результат». Нельзя снимать обязательную dependency только потому, что администратору доступна кнопка release.

Частичный результат допустим как новый явно ограниченный предмет приёмки, если он самостоятельно полезен и остальные обязанности имеют владельца. API partial-post (S55) переносит связанные строки и имеет технические условия; он не доказывает предметную делимость задачи. Примеры as-built требуют набора материалов, а не просто одного файла (S70, S75); нормативы чужого владельца не перенесены в наши сроки или точности.

## 5. Взаимное ожидание и промежуточное состояние

Цикл на уровне карточек не всегда deadlock: А может дать обследование до своей публикации, Б использовать обследование и затем вернуть результат А. Нужно сравнивать ожидаемые deliverables и удерживаемые этапы. Петля возврата QA также не равна блокировке двух публикаций (S16).

Настоящий тупик возникает, когда каждый следующий допустимый результат требует ещё не существующего результата другого, а независимого допустимого шага нет. Последовательность «опубликовать А, затем Б» не решает задачу, если промежуточная сеть недопустима. Технические свойства отдельных версий и post (S36, S42, S57) не дают гарантии общей атомарности.

Для условной организации выбран консервативный маршрут: удержание затронутых этапов, разбор смысла результата, перепланирование к самостоятельным допустимым результатам; если это невозможно — отдельное решение о разрешённом scope и процессе. Сейчас нет принятого механизма совместного атомарного post нескольких WorkOrder. Это организационный выбор, а не универсальный отраслевой запрет.

## 6. Прирост относительно существующей модели

| Знание | Что уже было | Реальный прирост | Последствие |
| --- | --- | --- | --- |
| Обязательная зависимость результата | evidence_dependency связывает доказательства; related WorkOrder не наследует статусы | Обязательство производителя перед конкретным этапом потребителя | Новый concept work_result_dependency |
| Приёмка зависимости | assessment_delivery_and_acceptance различает доставку/приёмку | Приёмка исполняет только согласованный предмет обязательства; текущая применимость проверяется отдельно | Условие dependent_work_step_allowed |
| Пересмотр зависимости | change_basis_revision_policy допускает достаточную замену evidence | Изменение самого обязательства требует принятия владельцем результата Б | dependent_work_coordination_policy |
| Взаимное ожидание | Неделимость и границы baseline уже известны | Проверка цикла на уровне milestones и отсутствие разрешённого совместного post | Исключение координации и новый use case |
| Передача части результата | Принятие остатка уже урегулировано | Указание, какой именно этап Б освобождается и что продолжает удерживаться | Уточнение новой policy, не отдельный lifecycle |
| Поле/офис, сеть/представление | Уже присутствуют field_observation_acceptance и network_representation_and_operational_state | Дополнительные контрпримеры, не новые универсальные правила | Источники и сценарии, без дублирующих нод |
| Идентичность после divide/fuse/replace | Уже различены запись, представление и физический актив | Новые примеры зависимости результата от состава объектов | Кандидат будущего смыслового фильтра, не принятое расширение Save |

Содержательных отмен прежних решений не найдено. Новые source URLs сами по себе не считаются приростом. Различия в описании продуктовых прав QField и версионные условия Esri требуют проверки при выборе конкретной интеграции; из них не выводятся auth roles нашего приложения. Числа точности и сроки чужих as-built руководств не заменяют SIM-UGIS-POS-001 и SIM-UGIS-RET-001.

## 7. Риски переноса и открытая проверка

Гипотеза: явная карточка dependencies уменьшит преждевременную передачу результатов. Она не проверена экспериментом, KPI не заявлены. Сначала применим ручной протокол; автоматизация требует отдельной задачи. Доменная определённость не равна runtime validation.

При реализации нужно отдельно проверить точку проверки зависимости относительно допуска post, гонку изменения обязательства и допуска, неизвестный исход уже запущенной операции, связь с актуальностью пакета и передачу остатка. Это техническая часть существующего FU-2026-10-13-004, а не повторные доменные вопросы. Если изменение пришло после допуска исполнения, сначала устанавливается outcome; зависимость не объявляется волшебным откатом.

## 8. Реестр прочитанных источников

S-ID используются также в файле ответов. Факт — краткий пересказ прочитанного раздела, применение — аналитическая граница. Новизна сравнивается с прежними RAW, а не со всем интернетом.

| ID | Документ и прямая ссылка | Извлечённый факт | Применение / ограничение | Новизна URL |
| --- | --- | --- | --- | --- |
| S01 | [Dependencies](https://doc.arcgis.com/en/workflow-manager/latest/help/dependencies.htm) | Sequential, parallel и staggered зависимости удерживают разные этапы работы; child job может собрать недостающие полевые данные. | Виды обязательств и граница ожидания; не готовая policy GeoService. | ранее встречался |
| S02 | [Manage dependencies](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-dependencies.htm) | Зависимость указывает блокируемый шаг и job/step-предшественник; снятие требует привилегии. | Точный адрес обязательства и отделение снятия от выполнения. | ранее встречался |
| S03 | [Show and manage holds](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-holds.htm) | Hold может возникнуть из-за отсутствия данных, ресурсов или срока и приостанавливает выполнение шагов. | Отличать административное ожидание от доказательства качества. | ранее встречался |
| S04 | [Create Job](https://doc.arcgis.com/en/workflow-manager/latest/help/create-job.htm) | Создание child job и dependency настраивается отдельно; созданные зависимости удерживают следующий шаг. | Иерархия работ не равна условию допуска. | ранее встречался |
| S05 | [Manage jobs](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-jobs.htm) | Manage показывает задания по местоположению и группирует по родителю; перекрывающиеся области показываются отдельно. | Географическое соседство не задаёт автоматически производственный порядок. | ранее встречался |
| S06 | [Users groups roles privileges](https://doc.arcgis.com/en/workflow-manager/latest/administer/users-groups-roles-and-privileges.htm) | Права изменения holds, родителя, статуса и назначения перечислены отдельно. | Раздельная ответственность; не копировать роли Esri в auth. | ранее встречался |
| S07 | [Auto-resume jobs](https://doc.arcgis.com/en/workflow-manager/latest/administer/auto-resume-jobs.htm) | Автопродолжение зависит от настройки шага, авторизации и сохранения назначенного пользователя. | Снятие ожидания не является безусловной командой продолжения. | новый URL |
| S08 | [Work on jobs](https://doc.arcgis.com/en/workflow-manager/latest/help/work-on-jobs.htm) | Pause, cancel, complete и hold — разные действия; dependency удерживает шаг до другого результата. | Не смешивать отмену работы, остановку и успешное завершение. | ранее встречался |
| S09 | [Parent-child relationships](https://doc.arcgis.com/en/workflow-manager/latest/help/parent-child-relationships.htm) | Иерархия может применяться совместно с dependency, но dependency добавляется отдельно. | Связь происхождения/декомпозиции не обязана блокировать. | ранее встречался |
| S10 | [Reroute workflow](https://doc.arcgis.com/en/workflow-manager/latest/help/reroute-workflow.htm) | Переназначение текущего шага требует прав; другой работающий шаг препятствует операции. | Перепланирование должно учитывать уже исполняющийся эффект. | ранее встречался |
| S11 | [Manage job properties](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-job-properties.htm) | Редактирование properties требует назначения/владения и прав; closed job ограничен. | Право менять карточку не доказывает право принять результат. | новый URL |
| S12 | [Manage job attachments](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-job-attachments.htm) | Вложение может быть файлом, URL либо ссылкой на документ; виден автор последнего изменения. | Наличие вложения не доказывает неизменность или принятие evidence. | ранее встречался |
| S13 | [Manage job notes](https://doc.arcgis.com/en/workflow-manager/latest/help/manage-job-notes.htm) | Notes предназначены для неформальной информации и допускают редактирование. | Обязательство нельзя выводить из одной неформальной заметки. | новый URL |
| S14 | [Job templates](https://doc.arcgis.com/en/workflow-manager/latest/help/create-and-manage-job-templates.htm) | Изменённый template используется новыми jobs; существующие сохраняют прежние свойства. | Пересмотр шаблона не снимает обязательств ранее созданной работы. | новый URL |
| S15 | [Create Field Maps Task](https://doc.arcgis.com/en/workflow-manager/latest/help/create-field-maps-task.htm) | Webhook dependency выпускается по заданному условию статуса field task; task имеет геометрию и идентификатор. | Полевой статус — сигнал для проверки, а не позиционная приёмка. | новый URL |
| S16 | [Workflow diagrams](https://doc.arcgis.com/en/workflow-manager/latest/help/workflow-diagrams.htm) | Looping для возврата QA, branching с одним путём и parallel с несколькими активными шагами различаются. | Цикл повторной проверки не равен взаимному ожиданию публикаций. | новый URL |
| S17 | [QFieldCloud Jobs](https://docs.qfield.org/reference/qfieldcloud/jobs/) | Успех process_projectfile означает чтение проекта, не корректность настройки; delta_apply отдельно применяет изменения, конфликты требуют policy. | Технический success не является приёмкой результата. | ранее встречался |
| S18 | [QFieldCloud Get started](https://docs.qfield.org/get-started/tutorials/get-started-qfc/) | Cloud/local состояния различаются; загрузка локального GeoPackage заменяет облачный файл. | Проверять путь получения результата, не только кнопку sync. | ранее встречался |
| S19 | [Giswater Data model](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/data-model-giswater.html) | Объекты имеют operative, obsolete и planned состояния; planned связан с psector; топология узел–дуга ограничивает изменения. | Рабочий сценарий и действующая сеть — разные основания проверки. | ранее встречался |
| S20 | [New planning sector](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/new-psector.html) | Выбор текущего psector переводит новые оцифрованные объекты в planned; возврат к operative выполняется отдельно. | Не выводить эксплуатационное состояние из факта сохранения. | ранее встречался |
| S21 | [QFieldCloud FAQ](https://qfield.cloud/faq.html) | Прямая работа с PostGIS и offline editing имеют разные условия доступности. | Доступный путь передачи нужно устанавливать для конкретного проекта, не по названию стека. | новый URL |
| S22 | [QFieldCloud repository](https://github.com/opengisch/qfieldcloud) | Проект заявляет change tracking, team management и online/offline synchronization. | Первичный источник существования инструментальной цепочки, не доказательство рыночной доли. | новый URL |
| S23 | [QField Basic concepts](https://docs.qfield.org/get-started/tutorials/concepts/) | Shared datasets видны в проекте, но не участвуют в обычной синхронизации; template отделён от regular. | Видимость данных не означает их обновление в рабочей копии. | новый URL |
| S24 | [QField Permissions](https://docs.qfield.org/get-started/tutorials/permissions/) | Reporter может добавлять, но не менять существующие объекты; права проекта отделены от организации. | Полномочия получателя нельзя наследовать от факта участия. | ранее встречался |
| S25 | [QField Advanced setup](https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/) | Offline копия GeoPackage не выполняет серверные PostGIS triggers; конфликты разрешаются last wins или вручную. | Проверка полевой копии не равна проверке центрального состояния. | ранее встречался |
| S26 | [QField Workflow](https://docs.qfield.org/reference/qfieldcloud/workflow/) | После отправки deltas возвращается job ID; менеджер ждёт применения перед загрузкой результата. | Передано, применено и доступно потребителю — разные факты. | ранее встречался |
| S27 | [QField Digitize and edit](https://docs.qfield.org/how-to/data-collection/digitize/) | Просмотр и digitize разделены; доступны vertex/split/reshape и атрибутные формы. | Роль шире движения вершины; поддержка инструмента не расширяет GeoService slice. | ранее встречался |
| S28 | [Dirty areas](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/dirty-areas-in-a-utility-network.html) | Правка карты создаёт dirty area; скрытие слоя не убирает непроверенное состояние. | Проверка результата должна ссылаться на состояние топологии. | ранее встречался |
| S29 | [Validate topology](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/validate-a-network-topology.html) | Validate обрабатывает dirty features в выбранном extent; current extent и entire extent различаются. | Область подтверждённого результата обязательна. | ранее встречался |
| S30 | [Associations](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/associations.html) | Connectivity, containment и structural attachment различны; association требует поддерживающего правила. | Зависимость работ нельзя определять только пересечением XY. | ранее встречался |
| S31 | [Connectivity associations](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/connectivity.html) | Связность может существовать между несовпадающими пространственно и непространственными объектами. | Соседство на карте не исчерпывает зависимость сети. | ранее встречался |
| S32 | [Containment](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/containment.html) | Контейнер управляет представлением содержимого; ресурс через контейнер не течёт. | Совместное размещение не означает одну функциональную связь. | ранее встречался |
| S33 | [Edit a utility network](https://doc.esri.com/en/arcgis-pro/latest/help/editing/edit-a-utility-network.html) | Named version изолирует правки перед reconcile/post; edits создают несогласованность с topology. | Разделять рабочий и опубликованный результат. | ранее встречался |
| S34 | [Reconcile and post branch](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.html) | Изменения default после reconcile могут вызвать конфликт при post; требуется reconcile заново. | Порядок завершения задач не резервирует актуальность. | ранее встречался |
| S35 | [Manage branch versions](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/manage-branch-versions.html) | Права версии зависят от пользователя, владельца и access; modified/validated/reconciled различны. | Не заменять приёмку правом редактирования или датой изменения. | ранее встречался |
| S36 | [Branch version scenarios](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/branch-version-scenarios.html) | Длительные work orders могут иметь отдельные версии; branch hierarchy имеет один уровень под default. | Иерархия заданий не совпадает с деревом версий. | ранее встречался |
| S37 | [Network topology](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-network-topology.html) | Validate не выполняется автоматически после каждой правки; неполный extent не гарантирует валидность всего feature. | Milestone должен содержать охват и оставшиеся проверки. | ранее встречался |
| S38 | [Structural attachments](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/structural-attachments.html) | Опора связана с оборудованием, но не проводит ресурс; связь полезна для поиска конструкций. | Разные виды сетевых зависимостей требуют разной области анализа. | ранее встречался |
| S39 | [Network rules](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/network-rules.html) | Правила определяют допустимые связи; новые правила в named version отражаются после reconcile. | Принятое основание включает применимую конфигурацию. | ранее встречался |
| S40 | [Feature restrictions](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/feature-restrictions.html) | Неизменяемые системные ограничения классов предшествуют настраиваемым network rules. | Организационное снятие hold не отменяет инварианты данных. | ранее встречался |
| S41 | [Errors](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-error-features.html) | Неоднозначная связность создаёт ошибку; исправление может касаться geometry, attributes либо rules. | Не выбирать порядок публикации случайно при неопределённой связи. | ранее встречался |
| S42 | [Post REST](https://developers.arcgis.com/rest/services-reference/enterprise/post/) | Post требует reconcile той же session; async возвращает ссылку на состояние, а не итог. | Подтверждённый outcome отделён от запуска. | ранее встречался |
| S43 | [Reconcile REST](https://developers.arcgis.com/rest/services-reference/enterprise/reconcile/) | Reconcile проверяет конфликты и автоматически фиксирует edits; stopEditing(false) их не отменяет. | Нельзя считать отмену workflow откатом данных. | ранее встречался |
| S44 | [Differences REST](https://developers.arcgis.com/rest/services-reference/enterprise/differences/) | Diff различает inserts/updates/deletes и может быть ограничен моментом и слоями. | Свидетельство результата должно иметь точную область сравнения. | ранее встречался |
| S45 | [Trace REST](https://developers.arcgis.com/rest/services-reference/enterprise/trace-utility-network-server/) | Trace читает topology; при dirty areas точность представления текущей сети не гарантируется. | Не выдавать полученный trace за проверенный current. | новый URL |
| S46 | [PROV-DM](https://www.w3.org/TR/prov-dm/) | Модель различает entities, activities, derivation и ответственных agents. | Основание прослеживаемости ожидаемого результата; не workflow policy. | ранее встречался |
| S47 | [PROV-O](https://www.w3.org/TR/prov-o/) | Онтология представляет происхождение между системами и допускает предметное расширение. | Связь provenance не равна разрешению продолжать работу. | ранее встречался |
| S48 | [Data Quality Vocabulary](https://www.w3.org/TR/vocab-dqv/) | Качество описывается так, чтобы потребитель оценил fitness for purpose; универсального определения нет. | Приёмка результата зависит от цели потребителя. | ранее встречался |
| S49 | [FHWA As-Built Utility Surveys](https://www.fhwa.dot.gov/construction/3d/hif16016.pdf) | Кейс Virginia/Michigan отмечает изменение сетей в течение проекта и ценность съёмки открытого объекта при строительстве. | Проверять актуальность передачи между стадиями; не переносить местные допуски. | новый URL |
| S50 | [QGIS Editing](https://docs.qgis.org/3.44/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html) | Topological editing двигает общие вершины соседних видимых editable layers. | Область эффекта инструмента может быть шире выбранного объекта. | ранее встречался |
| S51 | [QGIS Relations](https://docs.qgis.org/3.44/en/docs/user_manual/working_with_vector/joins_relations.html) | Связи позволяют создавать, перепривязывать и отвязывать child records; N:M использует отдельную связующую таблицу. | Техническая ссылка не задаёт бизнес-завершение. | новый URL |
| S52 | [QGIS Topology Checker](https://docs.qgis.org/3.44/en/docs/user_manual/plugins/core_plugins/plugins_topology_checker.html) | Validate All и Validate Extent имеют разные области; ошибки привязаны к rule/layer/feature. | Охват QA фиксируется явно. | новый URL |
| S53 | [QGIS Geometry Checker](https://docs.qgis.org/3.44/en/docs/user_manual/plugins/core_plugins/plugins_geometry_checker.html) | Допуски задаются в единицах слоя; исправление может удалить feature или изменить геометрию. | Автоисправление не безусловно разрешённая коррекция. | новый URL |
| S54 | [QGIS Offline Editing](https://docs.qgis.org/3.44/en/docs/user_manual/plugins/core_plugins/plugins_offline_editing.html) | Можно синхронизировать только выбранные features; remote layers копируются в локальную БД. | Локальный пакет не доказывает полноты центральной сети. | новый URL |
| S55 | [Partial Post](https://developers.arcgis.com/rest/services-reference/enterprise/partial-post/) | При частичном post список rows должен включать связанные изменённые данные; после выполняется reconcile. | Часть публикации должна быть замкнута по необходимым зависимостям; не вводит общий post в GeoService. | ранее встречался |
| S56 | [Validate Network Topology REST](https://developers.arcgis.com/rest/services-reference/enterprise/validatenetworktopology-utiility-network-server/) | Ответ отличает success, validateErrorsCreated и dirtyAreaCount; область может задаваться extent или IDs. | Успешное исполнение проверки не равно отсутствию ошибок. | новый URL |
| S57 | [Update subnetwork](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/update-a-subnetwork.html) | Параллельное обновление одной subnetwork может завершиться ошибкой. | Порядок координации не обещает техническую атомарность. | ранее встречался |
| S58 | [Subnetwork life cycle](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/subnetwork-life-cycle.html) | Clean означает согласованность производных данных с topology; административные изменения делают subnetworks dirty. | Приёмка производного результата имеет собственное основание. | новый URL |
| S59 | [Branch version conflicts](https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/manage-branch-version-conflicts.html) | Conflicts различаются по layer, категории update-delete и object ID. | Конфликт версий отличается от зависимости работ. | ранее встречался |
| S60 | [Giswater Mincut](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/mincut.html) | Расчёт отключения требует корректных arc-node, состояния клапанов и источников. | Карта без атрибутов состояния недостаточна для эксплуатационного решения. | ранее встречался |
| S61 | [Mincut Manager](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/mincut-manage.html) | Плановые, текущие и исторические зоны отключения управляются отдельно. | Результат расчёта не факт выполнения отключения. | ранее встречался |
| S62 | [FHWA R15B](https://www.fhwa.dot.gov/goshrp2/Solutions/All/R15B/Identifying_and_Managing_Utility_Conflicts) | UCM предназначена для раннего выявления конфликтов сетей и альтернатив решений. | Основание явной координации; заявленные выгоды не метрики GeoService. | новый URL |
| S63 | [Kentucky utility coordination case](https://www.fhwa.dot.gov/goshrp2/Content/Documents/SHRP2_R15B_KYTC.pdf) | KURTS сохраняет историю документов и альтернативы разрешения конфликтов с влиянием на сроки и затраты. | Сохранять историю замены обязательства и альтернативы. | новый URL |
| S64 | [FHWA utility coordination scan](https://international-dr.fhwa.dot.gov/scan/12025/) | Appendix D показывает согласованную многоуровневую эскалацию между дорожным ведомством и utility. | Пример процедуры, не источник наших ролей и сроков. | новый URL |
| S65 | [Replace feature](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/replace-feature.html) | Замена создаёт новый объект, старый становится obsolete; фиксируются дата и Workcat. | Замена физического объекта отличается от коррекции геометрии. | ранее встречался |
| S66 | [Search network and workcat](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/search.html) | Workcat связывает объекты одного дела; visit и psector имеют отдельные поиски. | Группировка объектов не определяет зависимость задач. | новый URL |
| S67 | [Add Visit](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/add-visit.html) | Полевой визит связывает элементы, события, параметры и документы. | Осмотр — самостоятельный результат без обязательного редактирования сети. | ранее встречался |
| S68 | [Divide Arc](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-divide.html) | Разделение дуги создаёт две новые; допустимость определяется каталогом узла. | Идентичность и состав результата могут измениться. | ранее встречался |
| S69 | [Digitalize network](https://docs.giswater.org/master/en/docs/giswater/for-users/user-manual/digitalization.html) | До ввода объектов нужны каталоги, map zones и настройка snapping. | Предпосылкой может быть конфигурация, не другая геометрия. | ранее встречался |
| S70 | [University Arkansas utility as-builts](https://fama.uark.edu/_resources/documents/ae-guide/part2_planning/criteria-for-Utility-As-Builts.pdf) | Требуются согласование формата до строительства, съёмка до засыпки, несколько deliverables и отражение удалённых сетей. | Пример приёмки полного комплекта; местные сроки/точности не переносятся. | новый URL |
| S71 | [Fuse Arc](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/arc-fusion.html) | Слияние требует одного каталога и отдельного решения о судьбе общего узла. | Область эффекта шире одной линии. | ранее встречался |
| S72 | [End Feature](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/end-feature.html) | Перевод в obsolete связывается с делом строительства и выбранными объектами. | История вывода отличается от удаления записи. | ранее встречался |
| S73 | [Psector manager](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/psector-management.html) | Сценарий можно выбрать, активировать, объединить, дублировать или восстановить. | Редакция сценария важна для потребителя результата. | новый URL |
| S74 | [Add Document](https://docs.giswater.org/master/en/docs/giswater/for-users/dialogs/add-doc.html) | Документ имеет тип, путь и связь с объектом. | Связанный файл ещё не принятый deliverable. | новый URL |
| S75 | [Engineering Survey Practice Guides 2025](https://www.landsd.gov.hk/doc/en/survey-mapping/Survey-related-guides-specifications/ESPG_2025_Edition.pdf) | Глава 12 требует своевременной съёмки установленных участков и набора сведений as-built; chainage лишь ориентир при изменении трассы. | Проверять назначение и состав результата; местные допуски не переносить. | новый URL |
