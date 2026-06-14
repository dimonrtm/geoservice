# Utility GIS editor — ответы по geometry / association conflict и risk-tiered routing

## Контекст

Файл подготовлен для варианта использования `Utility GIS editor`. Базовая модель из исследования: для инженерных сетей критичен branch/workspace workflow, reconcile/post, reviewer loop, явное разрешение конфликтов, проверка topology/connectivity, dirty areas, validation, trace и защита authoritative state.

В ответах ниже `Default` трактуется как authoritative branch/version, `Mine` / `Current` — как рабочая версия редактора, `Base` / `Common Ancestor` — как состояние, от которого разошлись изменения. Это соответствует типовой модели branch versioning и conflict resolution в ArcGIS Enterprise / ArcGIS Pro.

---

# Must

## 1. Вспомните последний реальный geometry/association conflict. Что изменяли оба участника?

Как `Utility GIS editor`, я бы описал такой реалистичный для utility-домена случай.

Была аварийная замена участка кабельной линии / трубы после полевого наряда. Я в своей named version правил геометрию линейного сегмента, переносил junction/device в фактическую точку подключения и обновлял association между устройством и линией. Параллельно другой редактор или диспетчерская версия уже запостила в `Default` изменение по тому же участку: поменяла connectivity association, terminal, asset type или привязку устройства к другому контейнеру / узлу.

То есть конфликт был не просто «две разные линии на карте». Один участник менял **геометрию и положение сетевых объектов**, второй — **логическую связь сети**: connectivity / containment / structural attachment association.

Для utility network это критично, потому что associations моделируют не только видимые геометрические совпадения, но и логические связи между spatial и nonspatial объектами. Внешне объект может выглядеть почти правильно, но trace, isolation или downstream analysis уже будут работать иначе.

---

## 2. Как вы обнаружили конфликт и поняли его сетевое последствие?

Сначала конфликт проявился на `reconcile`: система показала `Update-Update`, `Update-Delete` или связанный topological / relationship conflict. В Conflicts view я сравнил три состояния:

- `Mine` / `Current` — моя рабочая версия;
- `Default` / `Target` — authoritative состояние;
- `Base` / `Common Ancestor` — исходное состояние до расхождения.

Сетевое последствие стало понятно не по самому факту конфликта, а после проверки:

1. dirty areas появились на старой и новой геометрии;
2. association diff показал изменение connectivity / containment / structural attachment;
3. validation не очистила часть dirty areas или создала error dirty area;
4. trace до/после дал другой результат;
5. affected features / customers / devices / subnetworks изменились.

Ключевой вывод: conflict надо оценивать не только как «что перезаписать», а как «что изменится в сетевой модели после post».

---

## 3. Кто фактически отвечал за первое решение и почему именно он?

Первое решение должен принимать **автор edit version / назначенный Utility GIS editor**, потому что он ближе всего к work order, полевому sketch, фото, наряду и причине изменения.

Но его решение должно быть ограниченным уровнем риска.

| Уровень | Кто принимает первое решение | Почему |
|---|---|---|
| Simple | Editor | Конфликт локальный, не меняет connectivity / trace / service area |
| Normal | Editor + уведомление Reviewer | Есть затронутые данные, но validation и trace не показывают сетевого ущерба |
| High | Reviewer принимает решение после предложения Editor | Есть изменение topology/connectivity или спор с Default |
| Critical | Совместное решение Editor + Reviewer + профильный специалист | Возможна потеря обслуживания, неверный trace, нарушение network rule или downstream-риск |

Editor не должен автоматически «побеждать» только потому, что его версия активна. Для utility-сценария опасно автоматическое разрешение unreviewed конфликтов в пользу edit version без явного анализа сетевого последствия.

---

## 4. Какие данные нужны для решения: Base / Mine / Default, geometry diff, association diff, validation, trace?

Минимальный набор данных для UI conflict resolution:

| Данные | Зачем нужны |
|---|---|
| **Base / Common Ancestor** | Понять, от какого состояния разошлись обе правки |
| **Mine / Current / Edit version** | Увидеть изменения текущего Editor |
| **Default / Target** | Увидеть authoritative состояние на момент reconcile |
| **Geometry diff** | Сравнить старую и новую геометрию, displacement, split/merge, удаление |
| **Association diff** | Понять изменение connectivity, containment, structural attachment, terminal |
| **Validation result** | Проверить dirty areas, error dirty areas и network rule violations |
| **Trace before/after** | Проверить upstream/downstream/isolation/connected/subnetwork result |
| **Work order / field evidence** | Фото, sketch, номер наряда, дата полевого подтверждения |
| **Editor tracking / audit** | Кто, когда, в какой версии и почему изменил объект |

Для обычного GIS-конфликта иногда достаточно Base / Mine / Default. Для utility network этого недостаточно: обязательно нужны association diff, validation и trace impact.

---

## 5. Какие конфликты один участник может безопасно разрешить самостоятельно?

Один Editor может решать сам только конфликты, которые **не меняют сетевое поведение**.

Безопасные примеры:

- исправление подписи, комментария, naming, remark;
- изменение non-network атрибута, который не участвует в trace / subnetwork / rule;
- небольшая geometry correction без изменения connected endpoints;
- update attachment / фото, если объект и связь не меняются;
- конфликт по описательному полю, где Default явно устарел;
- merge geometry, если две правки затрагивают разные части geometry и не ломают endpoints;
- исправление cartographic-only смещения, если topology/connectivity unchanged.

Даже в этих случаях после решения должны быть:

- clean validation;
- отсутствие error dirty areas;
- отсутствие association diff или подтверждение, что association не менялась;
- trace unchanged, если объект входит в сетевой путь.

---

## 6. Какие признаки требуют обязательного совместного решения Editor и Reviewer?

Обязательное совместное решение нужно, если есть хотя бы один признак:

- конфликт затрагивает **Shape + association** одновременно;
- изменились endpoints линии, junction, device, terminal configuration;
- изменился connectivity / containment / structural attachment;
- validation создала error dirty area;
- trace before/after отличается;
- изменился набор affected customers / valves / switches / feeders / pipes;
- объект был удален в одной версии и изменен в другой;
- конфликт затрагивает service boundary, feeder, pressure zone, subnetwork;
- есть нарушение network rule;
- Default уже изменился после reconcile, и post требует повторного reconcile;
- автор Default-изменения недоступен, а изменение неочевидно;
- есть спор между work order и фактическими данными из поля.

Главный критерий: если результат может изменить поведение сети, Editor не должен решать один.

---

## 7. Согласны ли вы с уровнями Simple / Normal / High / Critical? Разложите 2–3 реальных примера.

Да, уровни реалистичны. Но их надо считать не по «сложности интерфейса», а по **сетевому последствию**.

| Уровень | Пример | Решение |
|---|---|---|
| **Simple** | Я поправил положение подписи/опоры на 20 см, другой редактор изменил комментарий. Connectivity, association и trace не изменились. | Editor решает сам, post разрешен после clean validation |
| **Normal** | Я уточнил geometry линии, другой редактор поменял material/status. Endpoints не изменились, trace identical, dirty areas очистились. | Editor решает, Reviewer видит audit note |
| **High** | Я перенес junction и линию, другой участник изменил connectivity association того же устройства. Trace изменился, но service loss не подтвержден. | Reviewer обязан проверить diff, validation, trace |
| **Critical** | Один участник удалил/заменил valve/switch, второй переподключил участок к другому feeder/pressure zone. Isolation/downstream trace изменился, часть потребителей может «потеряться» или попасть не в тот subnetwork. | Post блокируется до совместного решения |

Дополнительные реальные примеры:

### Пример 1 — Simple

Два редактора поменяли разные описательные атрибуты одного transformer / valve. Один исправил `comment`, второй уточнил `installation_date`. Geometry, association, terminal и trace не изменились. Это Simple.

### Пример 2 — High

Один редактор перенес junction на новую точку подключения, второй в Default уже поменял connectivity association. Визуально линия почти совпадает, но trace проходит через другой путь. Это High.

### Пример 3 — Critical

Один редактор удалил старый switch / valve как замененный, второй переподключил dependent segment к этому же объекту. После reconcile появляется update-delete conflict, validation показывает error dirty area, isolation trace теряет часть участка. Это Critical.

---

## 8. Что должно автоматически делать конфликт Critical: topology/connectivity, изменение trace, потеря обслуживания, нарушение network rule?

`Critical` должен не просто показывать красную метку. Он должен автоматически запускать protective workflow.

Система должна:

1. **заблокировать post** до явного решения;
2. запустить validation в affected extent;
3. построить trace before/after;
4. посчитать affected features / customers / devices / subnetworks;
5. показать association diff;
6. показать network rule violations;
7. создать обязательную задачу Reviewer;
8. потребовать evidence: work order, field confirmation, комментарий;
9. зафиксировать risk reason в audit;
10. запретить auto-resolve in favor of edit version;
11. потребовать повторного approval, если данные изменились после проверки.

Critical должен срабатывать при признаках:

| Признак | Почему Critical |
|---|---|
| topology/connectivity изменилась | Меняется фактический путь ресурса |
| trace изменился | Downstream analysis может стать неверным |
| есть потеря обслуживания / affected customers | Ошибка выходит за рамки GIS |
| нарушен network rule | Модель сети формально неконсистентна |
| dirty area с error/subnetwork error | Network topology не подтверждена |
| update-delete по сетевому объекту | Высокий риск потери реального актива |
| association diff без field evidence | Логическая связь сети могла быть изменена ошибочно |

---

## 9. Что происходит, если автор изменения в Default недоступен?

Если автор Default-изменения недоступен, нельзя автоматически считать его изменение менее важным.

Правильный порядок:

1. система показывает автора, время, version/post source и work order;
2. Editor делает первичное предложение решения;
3. Reviewer проверяет evidence;
4. если изменение затрагивает connectivity/trace/service — подключается профильный специалист;
5. если evidence недостаточно, post блокируется или переводится в escalated review;
6. Default-изменение можно заменить только с комментарием, почему оно признано устаревшим/ошибочным;
7. в audit сохраняется причина решения без автора Default.

Главный принцип: **недоступность автора — не основание для silent overwrite**.

---

## 10. Кто является профильным специалистом и в каких случаях его подключают?

Профильный специалист — это не GIS-администратор, а человек, который понимает физическую сеть и эксплуатационный смысл изменения.

| Домен | Профильный специалист | Когда подключать |
|---|---|---|
| Электросеть | инженер feeder / protection / switching | feeder change, switch, transformer, phase, isolation trace |
| Водоснабжение | инженер водопроводной сети / гидравлик | valve isolation, pressure zone, pipe replacement |
| Канализация | инженер sewer / drainage | flow direction, upstream/downstream, manhole connection |
| Газ | инженер газовой сети / safety officer | regulator, valve, pressure tier, safety isolation |
| Телеком | инженер ВОЛС / transport network | fiber splice, containment, circuit/path trace |

Его подключают при:

- изменении trace;
- изменении service area;
- изменении subnetwork;
- изменении terminal configuration;
- network rule violation;
- спорном field evidence;
- потенциальном влиянии на потребителей;
- аварийной схеме или временном переключении;
- конфликте между проектной документацией и фактической сетью.

---

## 11. Кто владеет authoritative data и имеет право окончательного решения?

Владелец authoritative data — **Data Owner / Asset Owner подразделения**, а не отдельный Editor.

В системе это может быть роль:

- `Utility Data Steward`;
- `Network Data Owner`;
- `Asset Data Owner`;
- `Version Administrator` с ограничением бизнес-прав;
- назначенный владелец домена сети.

Практическое разделение ответственности:

| Роль | Чем владеет |
|---|---|
| Editor | Своей правкой и объяснением причины изменения |
| Reviewer | Качеством review и подтверждением evidence |
| Профильный специалист | Инженерной корректностью сетевого решения |
| Data Owner | Authoritative state и окончательным бизнес-решением |
| Version Administrator | Технической возможностью управлять версиями и post |

Техническое право выполнить post не должно автоматически означать право принять спорное инженерное решение.

---

## 12. Что должно блокировать post, а что допускает продолжение workflow?

### Должно блокировать post

- unreviewed High/Critical conflict;
- dirty areas с error/subnetwork error в affected extent;
- trace before/after отличается без объяснения;
- network rule violation;
- update-delete/delete-update по сетевому объекту;
- изменение association без validation;
- Default изменился после reconcile — нужен повторный reconcile;
- нет work order/evidence для рискованного изменения;
- Reviewer rejected или request changes;
- stale approval после новых изменений;
- affected customers / service impact не подтверждены.

### Может продолжать workflow без post

- сохранение edit version;
- повторная local validation;
- подготовка proposed resolution;
- запрос Reviewer;
- запуск trace comparison;
- добавление field evidence;
- manual edit в своей версии;
- создание escalation task;
- обсуждение с профильным специалистом.

### Может допускать post

- Simple conflict reviewed by Editor;
- Normal conflict с clean validation;
- geometry diff без изменения endpoints и trace;
- attribute conflict по non-network field;
- Reviewer approved с evidence;
- association diff подтвержден профильным специалистом и validation clean;
- повторный reconcile после изменения Default выполнен успешно.

---

# Should

## 13. Реалистичны ли сроки эскалации: сразу, 2 рабочих часа, 1 день и 2 дня?

Да, сроки реалистичны, но их надо привязать к риску и операционному режиму.

| Риск | SLA эскалации | Реалистичность |
|---|---:|---|
| Critical | сразу | Да. Особенно если возможна потеря обслуживания или неверный isolation trace |
| High | до 2 рабочих часов | Да, если Reviewer доступен в рабочее время |
| Normal | до 1 рабочего дня | Реалистично для плановых изменений |
| Simple | до 2 рабочих дней или без эскалации | Лучше не эскалировать, а писать в audit |

Я бы изменил одно: для аварийной коррекции Critical не «сразу в течение рабочего дня», а **сразу по дежурному каналу**, потому что utility-конфликт может влиять на оперативные решения.

---

## 14. Может ли Reviewer понизить риск? Какие доказательства и комментарий обязательны?

Да, Reviewer может понизить риск, но только с доказательствами.

Обязательные доказательства:

- validation clean в affected extent;
- dirty area count = 0 или нет error dirty areas;
- trace before/after одинаковый либо отличие объяснено work order;
- association diff просмотрен;
- geometry endpoints не изменили connectivity;
- нет affected customers / service loss;
- нет network rule violation;
- есть ссылка на work order / field evidence;
- есть комментарий: почему риск понижен;
- указана версия данных, время проверки и кто подтвердил.

Пример обязательного комментария:

> Risk downgraded from High to Normal because geometry changed only between existing vertices, endpoints unchanged, no association diff, validation completed successfully, downstream trace unchanged, no affected customers.

Reviewer не должен понижать `Critical` до `Normal` только по визуальному осмотру карты. Для utility network визуальное совпадение не гарантирует корректную topology.

---

## 15. Что должно произойти с подтверждениями, если после решения данные изменились?

Все подтверждения должны стать **stale / invalidated**.

Правило:

если после approval изменились geometry, association, network attribute, terminal configuration или Default снова поменялся до post, то:

1. старый approval сохраняется в audit;
2. workflow возвращается в `Needs Recheck`;
3. validation запускается повторно;
4. trace запускается повторно;
5. Reviewer должен подтвердить заново;
6. post запрещен до нового approval.

Иначе возникает опасная ситуация: формально решение подтверждено, но фактически оно относится уже к старому состоянию данных.

---

## 16. Какие варианты решения должна предлагать система, а какие требуют manual edit?

### Система может предлагать автоматически

| Вариант | Когда допустимо |
|---|---|
| Keep Mine / Current | Моя версия подтверждена evidence и не ломает сеть |
| Keep Default / Target | Default новее или подтвержден другим work order |
| Revert to Base / Common Ancestor | Обе правки сомнительны |
| Merge non-overlapping geometry | Shape conflict затрагивает разные части feature |
| Keep both attachments/comments | Нет сетевого влияния |
| Create Reviewer task | High/Critical |
| Run validation/trace | Всегда для network-impact conflict |
| Request field evidence | Если данных недостаточно |
| Escalate to domain specialist | Если есть trace/service/rule impact |

### Требует manual edit

- переподключение device к другому terminal;
- исправление connectivity association;
- split/merge линии с изменением endpoints;
- update-delete сетевого feature;
- перенос объекта между container/subnetwork;
- конфликт, где trace changed, но evidence говорит, что физически сеть изменилась;
- нарушение network rule;
- восстановление объекта после ошибочного удаления;
- исправление containment/structural attachment для nonspatial object;
- корректировка временной аварийной схемы.

Принцип: система может предложить варианты, но не должна автоматически принимать инженерное решение там, где меняется сетевое поведение.

---

## 17. Что необходимо сохранить в audit для последующего расследования?

Минимальный audit package:

- conflict id;
- layer/table/object global id;
- conflict type: update-update, update-delete, delete-update, relationship/topological;
- risk tier before/after;
- Base / Mine / Default snapshot или diff;
- geometry diff;
- association diff;
- dirty areas до/после;
- validation result;
- trace before/after;
- affected subnetworks/customers/devices;
- work order id;
- evidence links: фото, sketch, field note;
- кто создал version;
- кто изменил Default;
- кто принял решение;
- кто review approved/rejected;
- reason comment;
- timestamps: detected, assigned, resolved, approved, posted;
- post result;
- повторные reconcile/post attempts;
- признак stale approval, если был;
- кто понизил или повысил risk tier;
- причина override, если выбрали Mine против Default или Default против Mine.

Особенно важно сохранять не только финальное состояние, но и **почему отклонили Mine или Default**. Иначе расследование после неверного post сведется к ручному восстановлению контекста.

---

## 18. Где предложенная модель создаст задержки, лишние согласования или размытую ответственность?

Риски процесса:

| Где возникнет проблема | Почему |
|---|---|
| Все geometry conflicts отправляются Reviewer | Много false positive, редакторы начнут обходить процесс |
| Reviewer обязан смотреть Simple | Лишняя задержка без сетевого риска |
| Нет четкого Data Owner | Спорные решения будут зависать между Editor и Reviewer |
| Critical требует слишком много людей | Аварийные correction будут тормозиться |
| Risk tier считается только по типу объекта | Не учитывается реальное trace/service impact |
| Approval не инвалидируется после изменений | Формально approved, фактически уже другие данные |
| Default author всегда считается ответственным | Авторство часто не равно компетенции или доступности |
| Нет SLA для Reviewer | High/Critical будут висеть без владельца |
| Нет emergency path | Аварийная коррекция будет конфликтовать с формальным review |

Главная опасность — сделать workflow «юридически красивым», но непригодным для аварийных и ежедневных utility-правок.

---

# Nice

## 19. Когда авторство объекта является плохим критерием назначения ответственного?

Авторство плохой критерий, когда:

- объект был создан миграцией/import, а не текущим инженером;
- автор давно не работает или недоступен;
- объект менялся автоматическим скриптом;
- автор правки — полевой мобильный пользователь, но решение должен принять инженер сети;
- Default-изменение пришло из bulk update;
- конфликт затрагивает не объект автора, а downstream trace;
- один пользователь создал feature, другой отвечает за asset domain;
- ownership должен определяться feeder/pressure zone/AOI, а не `created_by`;
- объект относится к чужому эксплуатационному району;
- автор не имеет доменной компетенции по affected subnetwork.

Лучший критерий — **ответственность за affected network area + тип изменения + risk tier**, а не `created_by`.

---

## 20. Какие конфликты нельзя корректно классифицировать автоматически?

Полностью автоматически трудно классифицировать:

- «правильную» сторону в споре Mine vs Default, если оба имеют field evidence;
- старую фактическую сеть, где GIS давно не совпадает с реальностью;
- изменение, которое визуально мало, но меняет аварийный isolation scenario;
- конфликт, где trace changed ожидаемо по work order;
- временные operational states: переключение, байпас, аварийная схема;
- неполные полевые данные;
- конфликт между проектной и фактической документацией;
- спорную containment/structural attachment модель;
- массовый bulk update, где ошибка проявляется только на downstream analytics;
- ситуацию, где Default технически новее, но фактически ошибочен;
- ситуацию, где Mine технически корректен, но нарушает утвержденный проектный контур.

Автомат может хорошо найти признаки риска, но не всегда может понять инженерную правду.

---

## 21. Какой один шаг процесса вы бы убрали или изменили?

Я бы убрал обязательное согласование Reviewer для всех `Normal`, если выполнены условия:

- validation clean;
- trace unchanged;
- нет association diff;
- нет network rule violation;
- geometry endpoints unchanged;
- audit comment заполнен;
- affected customers = 0;
- Default не изменился повторно после reconcile.

Вместо этого сделал бы `Normal` как **post allowed with audit + sample review**.

Причина: иначе команда утонет в согласованиях, а Reviewer будет тратить внимание не на High/Critical, а на безопасные повседневные исправления.

---

## 22. При каком результате вы отказались бы от risk-tiered routing?

Я бы отказался или сильно пересобрал risk-tiered routing, если в пилоте:

- больше 30–40% High/Critical оказываются false positive;
- Reviewer становится bottleneck и post задерживается без снижения ошибок;
- Editors не понимают, почему конфликт получил риск;
- Critical не ловит реальные trace/service incidents;
- manual baseline быстрее и безопаснее;
- после внедрения не падают Review Error Count и Return Rate;
- участники начинают обходить процесс через прямую правку Default;
- post latency растет, а количество проблем после post не уменьшается;
- Data Owner не принимает модель ответственности;
- risk tier невозможно объяснить в audit.

Risk-tiered routing имеет смысл только если он снижает риск неверного authoritative state, а не просто добавляет этапы.

---

# Финальная проверка

## Сценарий для участников

Участникам надо дать не абстрактную схему, а короткий практический сценарий.

> У вас есть named version по work order. Вы перенесли участок линии и junction. В Default за это время другой участник изменил association того же device. Reconcile показал conflict. Validation создала dirty areas. Trace before/after отличается.

Попросите каждого участника самостоятельно пройти цепочку:

| Шаг | Что участник должен сделать |
|---|---|
| Обнаружение | Где он увидел conflict и какие объекты затронуты |
| Риск | Какой tier он назначил: Simple / Normal / High / Critical |
| Ответственный | Кто принимает первое решение и кто подтверждает |
| Решение | Keep Mine, Keep Default, Base, merge, manual edit |
| Подтверждение | Какие evidence, validation и trace нужны |
| Эскалация | Кого подключить и в какие сроки |
| Post | Что блокирует post и что позволяет продолжить |

Затем задать главный вопрос:

> **Что в этой модели опасно, нереалистично или не соответствует вашей фактической работе?**

Лучшие уточняющие вопросы после этого:

1. Где система заставила бы вас ждать без пользы?
2. Какой conflict вы бы точно не доверили автоматике?
3. В каком месте Reviewer не имеет достаточной компетенции?
4. Когда Editor должен иметь право post без Reviewer?
5. Какой признак Critical вы считаете самым важным: trace, service loss, topology, association или network rule?
6. Что чаще всего скрывает реальную проблему: geometry diff, association diff или устаревший Default?
7. Кто реально владеет authoritative data в вашей организации, а не «по документу»?
8. Что должно быть emergency exception, а что нельзя обходить даже при аварии?
9. Какие evidence реально доступны в момент принятия решения?
10. Где audit будет полезен, а где превратится в формальность?

---

# Короткий итог

Для `Utility GIS editor` модель `Simple / Normal / High / Critical` подходит, но только если риск считается не по «типу конфликта в БД», а по **сетевому последствию**:

- dirty areas;
- validation errors;
- association diff;
- trace change;
- affected service;
- network rule violation;
- update-delete по сетевым объектам;
- изменение Default после reconcile.

Post должен блокироваться не каждым конфликтом, а только тем, где есть риск неверного authoritative network state. Самый опасный сценарий — auto-resolve или post с unreviewed конфликтами, потому что после post состояние Default становится authoritative, а последствия могут проявиться уже в trace, аварийном отключении или downstream-системах.

---

# Источники

1. Загруженный файл пользователя: `Ф2(5).md` — исследование веб-ГИС сервисов для совместного редактирования пространственных данных; сценарий `Utility GIS editor`, branch/workspace editing, reconcile/post, reviewer workflow, conflict handling.
2. Esri ArcGIS Pro documentation — **Reconcile and post edits to a branch version**: https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.html
3. Esri ArcGIS Pro documentation — **Manage branch version conflicts**: https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/manage-branch-version-conflicts.html
4. Esri ArcGIS Pro documentation — **Dirty areas in a utility network**: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/dirty-areas-in-a-utility-network.html
5. Esri ArcGIS Pro documentation — **Validate a network topology**: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/validate-a-network-topology.html
6. Esri ArcGIS Pro documentation — **Associations**: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/associations.html
7. Esri ArcGIS Pro documentation — **Network topology**: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/about-network-topology.html
