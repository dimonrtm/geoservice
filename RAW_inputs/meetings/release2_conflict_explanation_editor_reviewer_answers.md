# Release 2 Conflict Explanation — ответы для Editor и Reviewer

Дата: 2026-06-14
Вариант использования: `Utility GIS editor`
Роли: `Utility GIS editor`, `Reviewer`

## Основание

Ответы подготовлены на основе загруженного исследования по совместному редактированию пространственных данных и доменной проверки по ArcGIS Enterprise / Utility Network:

- В исходном файле `Utility GIS editor` описан как инженер по эксплуатации сети, работающий с линиями, устройствами, узлами, associations и nonspatial objects.
- Рабочий процесс строится вокруг named branch version, reconcile/post, Conflicts view, validation topology и reviewer workflow.
- Для Utility Network недостаточно сравнивать только Base / Mine / Default: для безопасного решения нужны geometry diff, association diff, dirty areas, validation и trace before/after.

---

# 1. Ответы от имени `Utility GIS editor`

## Must

### 1. Вспомните последний конфликт, который вам пришлось разбирать. Что именно изменилось?

Последний конфликт был на участке сети, где я в своей `edit version` переносил junction и корректировал geometry линии по фактической схеме после полевого наряда. Параллельно в `Default` другой участник изменил association того же device: не саму видимую геометрию, а логическую связь устройства с сетью.

Для меня это был не обычный geometry conflict. Опасность была в том, что визуально линия могла выглядеть почти правильно, но connectivity association уже указывала на другое сетевое состояние. В Utility Network association может описывать connectivity, containment и structural attachment, поэтому её изменение нужно рассматривать отдельно от линии на карте.

### 2. Как вы впервые поняли, что возник конфликт?

Я понял это после reconcile с `Default`: система показала конфликт в Conflicts view. Там было видно, что моя version и Default изменили связанные объекты одного сетевого участка.

Первый сигнал — не только красная строка в конфликте, а комбинация признаков:

| Признак | Что он для меня означал |
|---|---|
| `Update-Update` / related conflict | один и тот же объект или связанный объект изменён в обеих версиях |
| dirty area после reconcile | topology ещё не отражает текущее состояние сети |
| изменённая association | конфликт может быть логическим, а не только геометрическим |
| trace before/after отличается | возможно изменилось сетевое последствие |

### 3. Какое решение вы должны были принять после обнаружения?

Я должен был выбрать не “чью правку оставить”, а **какое состояние сети безопасно довести до post**.

Фактически у меня было четыре варианта:

| Вариант | Когда подходит |
|---|---|
| **Keep Mine** | моя версия подтверждена work order / field evidence, validation чистая, trace ожидаемо изменился или не изменился |
| **Keep Default** | изменение в Default новее, подтверждено другим work order или моя версия устарела |
| **Manual edit** | ни Mine, ни Default не дают корректную сеть после сравнения geometry + association |
| **Передать Reviewer** | есть trace impact, dirty/error dirty area, спорная association, service area/subnetwork impact |

### 4. Какие данные нужны, чтобы выбрать Keep Mine, Keep Default или Manual edit?

Для решения мне нужны:

| Данные | Зачем |
|---|---|
| **Base / Common Ancestor** | понять исходное состояние до расхождения |
| **Mine / Current** | увидеть моё изменение |
| **Default / Target** | увидеть authoritative состояние на момент reconcile |
| **geometry diff** | понять, что физически перемещено, удалено, split/merge |
| **association diff** | понять, изменилась ли connectivity/containment/attachment |
| **validation result** | увидеть dirty/error dirty areas и network rule violations |
| **trace before/after** | понять сетевой эффект, а не только diff объекта |
| **work order** | проверить, какое изменение было заказано |
| **field evidence** | фото, sketch, акт, комментарий бригады |
| **author/time/editor tracking** | понять источник и свежесть изменения |
| **affected network elements** | subnetwork, feeder/pressure zone, valves/switches/customers/devices |

### 5. Достаточно ли Base / Mine / Default? Чего в таком сравнении не хватает?

Нет, для Utility Network этого недостаточно.

`Base / Mine / Default` показывает, **что изменилось в данных**, но не показывает, **что изменилось в сети**. Не хватает:

- association diff;
- dirty areas до/после;
- validation status;
- trace before/after;
- affected service/subnetwork;
- network rule violations;
- field evidence;
- причины изменения;
- информации, не устарело ли approval после нового reconcile.

В Conflicts view можно сравнивать `Current`, `Target`, `Common Ancestor`, но это ещё не доказывает безопасность utility‑сети. Для сети dirty areas показывают, что изменения ещё не отражены в topology, а trace может быть недостоверен при dirty areas.

### 6. Как лучше показать geometry diff: наложение, переключение версий или side-by-side?

Лучший вариант — **три режима сразу**, но с разным приоритетом:

| Режим | Для чего нужен |
|---|---|
| **Наложение** | быстро увидеть displacement, split/merge, изменение endpoints |
| **Side-by-side** | спокойно сравнить Mine и Default без визуального шума |
| **Переключение версий** | проверить контекст: соседние объекты, направление сети, container, device |

Первым я бы показывал **наложение Mine vs Default поверх Base**, потому что Editor должен быстро понять: объект сдвинулся, удалён, разделён или подключён к другой точке. Side-by-side нужен как режим проверки, а переключение — для детального анализа.

### 7. Какие изменения association необходимо объяснять отдельно от геометрии?

Отдельно нужно объяснять любые association, которые меняют логическую сеть:

| Association change | Почему отдельно |
|---|---|
| connectivity association изменена | может поменяться фактическая connected path |
| containment association изменена | объект может оказаться в другом container: substation, duct, cabinet |
| structural attachment изменён | меняется привязка к опоре/структуре |
| terminal/device association изменена | возможен другой вход/выход устройства |
| association с nonspatial object | на карте не видно, но topology/trace меняются |
| удаление association | объект может стать “висячим” или unlocatable |
| создание association без правила | может дать network error |

Association в Utility Network моделируют connectivity, containment и structural attachment между nonspatial objects и noncoincident network features; это не то же самое, что геометрическое совпадение на карте.

### 8. Как понять, изменились ли connectivity, topology или trace?

Я бы смотрел в таком порядке:

1. изменились ли endpoints линии или положение junction/device;
2. есть ли association diff;
3. появились ли dirty areas по geometry, associations, network attributes или terminal configuration;
4. прошла ли Validate Network Topology;
5. изменился ли trace before/after;
6. изменился ли affected subnetwork / feeder / pressure zone / service area;
7. есть ли error dirty areas или subnetwork error.

Dirty areas создаются при изменении geometry, asset group/type, network attributes, associations и terminal configuration. Это прямой сигнал, что network topology ещё не синхронизирована с тем, что видно на карте.

### 9. Какое сетевое последствие должно быть показано первым?

Первым нужно показать **самое дорогое последствие для эксплуатации**, а не технический diff.

Для utility‑сети я бы ранжировал так:

1. affected customers / affected service;
2. изменённый subnetwork / feeder / pressure zone;
3. trace before/after changed;
4. connectivity changed;
5. dirty/error dirty area;
6. network rule violation;
7. geometry/attribute diff.

Человеческий вывод должен звучать так:

> “После выбора Keep Mine устройство окажется в другом subnetwork, downstream trace изменится, dirty area требует validation. Post пока небезопасен.”

### 10. Какие validation errors и dirty areas действительно помогают принять решение?

Помогают не все dirty areas, а те, которые объясняют **что именно стало небезопасным**.

| Validation / dirty area | Помогает? | Почему |
|---|---:|---|
| Dirty by geometry update | Да | показывает, где topology устарела из-за геометрии |
| Dirty by association update | Да | показывает логическое изменение сети |
| Dirty by delete | Да | важно для update-delete/delete-update |
| Feature error | Да | объект нарушает правила сети |
| Object error | Да | особенно для nonspatial objects |
| Subnetwork error | Да | высокий риск для trace и эксплуатации |
| Dirty area без связи с конфликтом | Частично | может быть шумом |
| Dirty area вне trace path | Частично | важна, но не всегда блокирует конкретный post |

Статусы dirty areas хорошо подходят как объяснимые причины risk tier: modified, deleted, associated objects modified, feature error, object error, subnetwork error.

### 11. Что должно объяснять назначенный risk tier?

Risk tier должен объяснять не “сложность конфликта”, а **почему это опасно для сети**.

| Risk tier | Что система должна объяснить |
|---|---|
| Simple | изменён non-network атрибут, trace/topology не затронуты |
| Normal | есть geometry diff, но endpoints/connectivity/trace не изменились |
| High | изменена association или dirty area пересекает trace path |
| Critical | trace changed, affected service/subnetwork changed, есть network rule/subnetwork error |

Плохое объяснение:

> “Risk = High, потому что объект изменён в двух версиях.”

Хорошее объяснение:

> “Risk = High, потому что Mine переносит junction, Default меняет association того же device, validation создала dirty area, trace before/after отличается.”

### 12. В каких случаях Editor может разрешить конфликт самостоятельно?

Я как Editor могу сам разрешить конфликт, если одновременно выполняются условия:

- конфликт локальный;
- нет association diff;
- endpoints не изменились;
- trace before/after не изменился;
- validation clean;
- нет error dirty areas;
- work order однозначно подтверждает мою правку;
- изменение не затрагивает service area/subnetwork;
- Default‑изменение не новее и не связано с другим work order.

Типовые самостоятельные случаи:

| Случай | Можно самому? |
|---|---:|
| исправление комментария | Да |
| корректировка подписи / non-network атрибута | Да |
| небольшой geometry cleanup без endpoints | Да |
| изменение material без влияния на network attributes | Обычно да |
| association changed | Нет, нужен минимум review |
| trace changed | Нет |
| affected customers changed | Нет |
| update-delete device/line | Нет |

### 13. Что должно блокировать выбор Keep Mine или Keep Default?

Выбор Keep Mine / Keep Default должен блокироваться, если:

- есть unresolved association diff;
- trace before/after differs без объяснения;
- validation не выполнена;
- есть error dirty area;
- есть subnetwork error;
- изменён terminal/device connection;
- объект удалён в одной версии и изменён в другой;
- affected service/customers changed;
- work order отсутствует или противоречит выбранной версии;
- approval устарел после нового изменения;
- Default изменился после reconcile.

Post может обнаружить новые конфликты, если Default изменился после reconcile и до post; в этом случае требуется повторный reconcile. После post изменения уже применены в Default и не могут быть просто undone.

### 14. Когда система должна требовать Manual edit, evidence или передачу Reviewer?

| Условие | Что требовать |
|---|---|
| Mine и Default оба частично правильные | Manual edit |
| association изменилась отдельно от geometry | Reviewer |
| trace changed | Reviewer + evidence |
| affected subnetwork changed | Reviewer + профильный специалист |
| work order не подтверждает изменение | evidence |
| field sketch отличается от Mine/Default | Manual edit |
| dirty/error dirty area после validation | Manual edit или Reviewer |
| update-delete / delete-update | Reviewer |
| Critical risk | Reviewer + профильный специалист + post gate |

### 15. По каким признакам Editor понимает, что решение безопасно для post?

Я считаю решение безопасным для post, если:

- все conflicts reviewed;
- выбранное resolution объяснено;
- validation выполнена в affected extent;
- dirty areas очищены или объяснены;
- нет error/subnetwork error;
- trace before/after либо совпадает, либо отличается ожидаемо по work order;
- association diff просмотрен;
- affected service/subnetwork подтверждены;
- Reviewer не требуется или уже approved;
- после approval данные не изменялись;
- повторный reconcile не выявил новых конфликтов.

Validate Network Topology нужен, потому что после редактирования topology устаревает, а validate обновляет topology по dirty areas; без этого анализ сети может опираться на старое состояние.

## Should

### 16. Нужно ли показывать автора, время, work order и причину каждого изменения?

Да. Это обязательно для объяснимого решения.

Мне нужно видеть:

| Поле | Зачем |
|---|---|
| автор Mine | понимаю, кто делал мою/командную правку |
| автор Default | понимаю источник конкурирующего изменения |
| время изменения | определяю свежесть |
| work order | связываю diff с заданием |
| причина изменения | понимаю, аварийная это коррекция или плановая |
| версия / post source | понимаю, откуда изменение попало в Default |
| комментарий | вижу доменное объяснение |

Без этого конфликт превращается в технический diff без контекста.

### 17. Какие field evidence нужны рядом с конфликтом?

Рядом с конфликтом нужны:

- фото до/после;
- field sketch;
- номер work order;
- акт/документ;
- комментарий бригады;
- GPS/координата замера;
- timestamp field observation;
- имя полевого исполнителя;
- ссылка на external document;
- причина отклонения от проектной схемы.

Для High/Critical evidence должен быть обязательным, а не “дополнительным”.

### 18. Что важнее увидеть первым: объект конфликта, причину, риск или сетевое последствие?

Первым я хочу видеть **сетевое последствие**, затем объект и причину.

Оптимальный порядок экрана:

1. краткий вывод: “что произошло и чем опасно”;
2. risk tier и причина риска;
3. affected service/subnetwork/trace;
4. объект конфликта на карте;
5. recommended next action;
6. Base/Mine/Default;
7. geometry/association diff;
8. validation/dirty areas;
9. audit/evidence.

Если первым показать таблицу атрибутов, Editor может выбрать Keep Mine/Default по привычке, не поняв сетевой эффект.

### 19. Какие детали можно скрыть до раскрытия блока «Подробнее»?

Можно скрыть:

- полный список атрибутов без конфликтов;
- технические GlobalID/ObjectID;
- JSON trace result;
- raw validation log;
- полный audit trail;
- историю всех reconcile attempts;
- bitmask dirty area, если есть человекочитаемый статус;
- длинные комментарии;
- старые attachments;
- secondary affected objects.

Но нельзя скрывать:

- affected service/subnetwork;
- association diff;
- trace changed;
- validation errors;
- кто и когда изменил Default;
- почему назначен risk tier;
- что блокирует post.

### 20. Должна ли система рекомендовать решение? Как объяснить рекомендацию?

Да, но только как **recommendation, not decision**.

Формат:

> “Рекомендация: Manual edit. Причина: Mine переносит junction, Default меняет association того же device. Trace before/after отличается, affected subnetwork changed. Keep Mine или Keep Default могут сохранить неполную сеть.”

Для Simple/Normal система может рекомендовать Keep Mine/Default. Для High/Critical рекомендация должна чаще быть “Reviewer required” или “Manual edit required”.

### 21. Когда автоматическая рекомендация будет опасной или недостоверной?

Она опасна, если:

- trace не запускался;
- validation не выполнена;
- есть dirty areas в trace path;
- evidence отсутствует;
- Default изменился после reconcile;
- association diff не разобран;
- полевая схема противоречит данным;
- изменение аварийное/временное;
- есть nonspatial objects;
- affected customers неизвестны;
- system confidence низкий, но рекомендация выглядит уверенно.

Trace results не гарантированно точны при наличии dirty areas; проверять это можно через Validate Consistency или Dirty Area Count.

### 22. Как объяснить, почему конфликт назначен именно этому Editor?

Объяснение должно быть не по авторству объекта, а по ответственности:

> “Назначено вам, потому что ваша edit version содержит последнее изменение geometry по work order WO‑1247, конфликт затрагивает ваш affected extent, а competing change в Default меняет association того же device.”

Критерии назначения:

- владелец edit version;
- автор последнего изменения в Mine;
- work order assignee;
- AOI/network area owner;
- asset domain owner;
- наличие прав на manual edit;
- не авторство исторического объекта.

### 23. Какие следующие действия должны быть доступны прямо из explanation?

Нужны кнопки:

- Open geometry diff;
- Open association diff;
- Run validation;
- Run trace before/after;
- Show affected service;
- Attach evidence;
- Choose Keep Mine;
- Choose Keep Default;
- Start Manual edit;
- Send to Reviewer;
- Request domain specialist;
- Add comment;
- Mark as unsafe for post;
- Save resolution reason.

### 24. Что должно произойти с explanation и approval после изменения данных?

Explanation должен стать `stale`, а approval — недействительным.

Правило:

> Любое изменение geometry, association, network attribute, terminal configuration, trace result или Default после approval требует повторного explanation и повторного review.

На экране должно быть:

- “Approval invalidated: data changed after review”;
- что именно изменилось;
- кто изменил;
- когда изменил;
- какой новый риск;
- какие проверки надо повторить.

### 25. Какие сведения нужно сохранить в audit вместе с решением?

Сохранять нужно:

- conflict id;
- object ids/global ids;
- layers/tables;
- Base/Mine/Default snapshots или diff;
- chosen resolution;
- rejected alternatives;
- risk tier before/after;
- reason comment;
- author/time/work order;
- geometry diff summary;
- association diff summary;
- validation result;
- dirty area status;
- trace before/after summary;
- affected service/subnetwork;
- evidence links;
- Editor decision;
- Reviewer decision;
- specialist decision, если был;
- approval invalidation events;
- post result;
- повторные reconcile/post attempts.

## Nice

### 26. Какие термины непонятны без пояснений?

Без пояснений могут быть непонятны:

| Термин | Как объяснить человеку |
|---|---|
| Base / Common Ancestor | “как объект выглядел до расхождения версий” |
| Mine / Current | “ваше текущее изменение” |
| Default / Target | “текущее authoritative состояние” |
| association | “логическая связь объектов сети, не всегда видимая на карте” |
| trace | “проверка, куда сеть фактически соединяется/питается/изолируется” |
| dirty area | “область, где карта уже изменена, но network topology ещё не пересчитана” |
| topology | “внутреннее сетевое представление для анализа и trace” |
| subnetwork | “участок сети под контроллером/источником/зоной” |

### 27. Нужен ли краткий человекочитаемый вывод?

Да, обязательно.

Шаблон:

> **Что произошло:** в вашей версии перенесён junction и изменена линия; в Default изменена association того же device.
> **Чем опасно:** trace before/after отличается, возможно изменение subnetwork.
> **Что делать:** не выбирать Keep Mine/Default автоматически; выполнить validation, открыть association diff, передать Reviewer или сделать Manual edit.

### 28. Нужна ли история похожих конфликтов и ранее принятых решений?

Да, но не первой строкой. Она полезна в блоке “Похожие случаи”.

Показывать:

- похожие conflicts на этом asset type;
- какой resolution выбирали;
- были ли проблемы после post;
- кто подтверждал;
- сколько раз risk downgrade оказался ошибочным;
- типовой pattern: “geometry moved + association changed”.

### 29. Когда сравнение нескольких объектов должно группироваться в один конфликт?

Группировать нужно, когда объекты образуют одну сетевую причину:

- junction + connected line;
- device + terminal + association;
- container + content objects;
- line split + created junctions;
- valve/switch + affected trace;
- several dirty areas от одного work order;
- одна association изменила несколько related objects.

Не нужно группировать только по spatial proximity. Объекты рядом на карте могут относиться к разным subnetworks.

### 30. Какой объём информации превращает explanation в перегруженный экран?

Экран перегружен, если сразу показывать:

- все поля Base/Mine/Default;
- весь JSON trace;
- все dirty areas в районе;
- все attachments;
- технические ObjectID/GlobalID без смысла;
- длинную историю изменений;
- карту, таблицу, логи и evidence одновременно.

Правило: первый экран должен отвечать на три вопроса:

> Что произошло? Чем опасно? Что делать дальше?

Всё остальное — в “Подробнее”.

### 31. Что заставило бы открыть внешнюю GIS-систему или обратиться к специалисту?

Я открою внешнюю GIS‑систему или обращусь к специалисту, если:

- trace changed, но explanation не показывает почему;
- affected customers/subnetwork не рассчитаны;
- field evidence отсутствует;
- association diff непонятен;
- схема в work order противоречит карте;
- conflict затрагивает safety/isolation;
- есть subnetwork error;
- система предлагает Keep Mine без validation;
- данные выглядят устаревшими;
- нужно проверить документы, которых нет в conflict explanation.

### 32. При каком результате я перестал бы доверять conflict explanation?

Я перестану доверять, если:

- система говорит “safe”, но trace changed;
- risk tier не объяснён;
- dirty areas есть, но они скрыты;
- recommendation противоречит evidence;
- после изменения данных approval не сброшен;
- association diff не показан;
- affected service считается неверно;
- “Keep Mine” предлагается для Critical без Reviewer;
- прошлые approved conflicts приводили к проблемам после post;
- система часто даёт false safe.

## Сценарная проверка для Editor

**Сценарий:**
В `edit version` перенесён junction и изменена линия. В `Default` другой участник изменил association того же device. Validation создала dirty area, а trace before/after отличается.

### Как Editor должен пройти сценарий

| Шаг | Что я делаю как Editor |
|---|---|
| Обнаружение | Вижу conflict после reconcile и открываю explanation |
| Понимание причины | Понимаю: Mine меняет geometry, Default меняет association |
| Оценка последствия | Смотрю trace before/after, affected subnetwork/service |
| Risk tier | Назначаю минимум High, возможно Critical при service/subnetwork impact |
| Выбор решения | Не выбираю Keep Mine/Default автоматически; проверяю Manual edit или Reviewer |
| Проверка | Запускаю validation, смотрю dirty area, association diff, work order, field evidence |
| Сохранение причины | Пишу: “geometry и association конфликтуют; trace changed; требуется review/manual edit” |

### Финальный вопрос для Editor

**Что в объяснении отсутствует, избыточно или может подтолкнуть к опасному решению?**

Хороший ответ Editor:

> Опасно, если система показывает только Mine/Default и кнопку Keep Mine. Мне нужен первый вывод по trace/subnetwork/service impact. Избыточно — сразу показывать все атрибуты. Отсутствует — association diff, work order, field evidence, причина risk tier и понятный post gate.

---

# 2. Ответы от имени `Reviewer`

## Must

### 1. Вспомните последний конфликт, который вы проверяли. Какое решение ожидалось от вас?

От меня как Reviewer ожидалось не просто подтвердить выбор Editor, а проверить, можно ли безопасно довести resolution до post в `Default`.

Конфликт был такой: Editor выбрал Keep Mine после переноса junction и изменения линии. В `Default` уже была изменена association того же device. Validation общей ошибки не показала, но trace before/after отличался и затрагивал другой subnetwork.

Моё решение: подтвердить Keep Mine, вернуть на Manual edit, повысить risk tier или подключить профильного специалиста.

### 2. Что должно быть видно сразу, чтобы понять суть конфликта?

Сразу должно быть видно:

- краткий summary;
- risk tier и причина;
- выбранное решение Editor;
- competing change в Default;
- geometry diff;
- association diff;
- trace impact;
- validation/dirty areas;
- affected service/subnetwork;
- work order/evidence;
- что блокирует approve/post.

Первый экран Reviewer должен быть не таблицей атрибутов, а risk explanation.

### 3. Достаточно ли Base / Mine / Default для review? Чего не хватает?

Нет. Для review Base/Mine/Default — только начало.

Не хватает:

- Editor proposed resolution;
- reason comment;
- work order;
- field evidence;
- validation result;
- dirty area status;
- association diff;
- trace before/after;
- affected customers/devices/subnetworks;
- post gate status;
- stale approval check;
- history of Default changes.

В branch conflicts `Current`, `Target`, `Common Ancestor` помогают сравнить представления объекта, но Reviewer должен проверить последствия для сети и корректность решения, а не только выбрать одну из трёх версий.

### 4. Как проверить, что решение Editor соответствует work order и field evidence?

Я проверяю:

| Проверка | Что должно совпасть |
|---|---|
| work order scope | affected objects входят в задание |
| field sketch | geometry и connection соответствуют sketch |
| фото | device/junction действительно перенесён |
| timestamp | field evidence свежее, чем Default change |
| комментарий бригады | причина изменения понятна |
| association diff | логическая связь соответствует field evidence |
| trace | изменение ожидаемо и объяснимо |
| affected service | нет неожиданной потери обслуживания |

Если work order говорит “перенести junction”, но не говорит “переподключить device к другому subnetwork”, Keep Mine нельзя подтверждать без дополнительного evidence.

### 5. Какие geometry и association changes требуют отдельного внимания?

Отдельного внимания требуют:

- перенос junction;
- изменение endpoints линии;
- split/merge линии;
- удаление device/junction/line;
- изменение terminal connection;
- новая/удалённая connectivity association;
- containment change;
- structural attachment change;
- association с nonspatial object;
- изменение asset group/type или network attribute;
- любые изменения, создающие dirty area по association или subnetwork error.

### 6. Как показать влияние на connectivity, topology, trace и service area?

Нужно показать четыре уровня:

| Уровень | Как показать |
|---|---|
| Connectivity | “что с чем теперь соединено” before/after |
| Topology | dirty areas, validation status, topology clean/dirty |
| Trace | trace before/after с diff результатов |
| Service area | affected customers/devices/subnetworks/feeder/pressure zone |

Для Reviewer важно видеть не только карту, но и список добавленных/исключённых trace elements.

### 7. Какие validation results и dirty areas действительно подтверждают безопасность?

Подтверждают безопасность:

- validation выполнена в правильном affected extent;
- dirty areas по конфликтным объектам очищены;
- нет feature/object/subnetwork error;
- trace с Validate Consistency не падает;
- affected subnetwork ожидаемый;
- no unexpected affected customers/devices.

Не подтверждают безопасность:

- validation выполнена не на весь affected extent;
- dirty areas остались, но их скрыли;
- trace запускался с отключённой consistency проверкой;
- есть error dirty area без объяснения;
- Default изменился после validation.

### 8. Как Reviewer должен оценивать назначенный risk tier?

Reviewer должен проверить, соответствует ли risk tier фактам:

| Факт | Минимальный risk |
|---|---|
| non-network attribute only | Simple |
| geometry cleanup без endpoints/trace impact | Normal |
| association diff | High |
| trace changed | High |
| affected subnetwork changed | High/Critical |
| service loss / affected customers | Critical |
| network rule violation | Critical |
| subnetwork error | Critical |
| update-delete по сетевому объекту | High/Critical |

Если система поставила Normal, но trace changed — Reviewer обязан повысить риск.

### 9. Какие признаки требуют повышения риска до High или Critical?

До **High**:

- association changed;
- endpoints changed;
- trace changed;
- dirty area intersects trace path;
- affected subnetwork changed;
- work order не полностью объясняет изменение;
- manual edit likely required.

До **Critical**:

- affected customers/service changed;
- isolation/safety trace changed;
- subnetwork error;
- network rule violation;
- device/switch/valve удалён или переподключён;
- conflicting delete/update;
- риск неверного authoritative state после post;
- профильный специалист нужен до решения.

### 10. Когда Reviewer может подтвердить Keep Mine или Keep Default?

Reviewer может подтвердить **Keep Mine**, если:

- Mine соответствует work order;
- field evidence подтверждает Mine;
- association diff ожидаемый;
- validation clean;
- trace impact ожидаемый;
- affected subnetwork/service понятен;
- Default change устарел или менее подтверждён;
- Editor дал корректный reason.

Reviewer может подтвердить **Keep Default**, если:

- Default новее;
- Default связан с более актуальным work order;
- Mine не подтверждён evidence;
- Mine создаёт dirty/error/subnetwork issue;
- trace impact от Mine опасный;
- field evidence против Mine.

### 11. Когда обязательно вернуть конфликт на Manual edit?

Manual edit обязателен, если:

- Mine и Default оба частично правильные;
- простая замена ломает association;
- trace changed неожиданно;
- geometry и association не согласованы;
- нужно переподключить terminal/device;
- удаление и update конфликтуют;
- validation оставляет error dirty area;
- affected subnetwork неправильный;
- evidence требует третьего состояния, отличного от Mine и Default.

### 12. Что должно блокировать approve и post?

Блокировать approve/post должно:

- отсутствие evidence для High/Critical;
- неясный trace impact;
- dirty/error dirty area в affected area;
- subnetwork error;
- unresolved association diff;
- stale approval;
- Default changed after reconcile;
- no validation after manual edit;
- work order mismatch;
- Reviewer не указал comment для risk downgrade/approve Critical;
- профильный специалист required, но не подтвердил.

### 13. Когда нужен профильный специалист по затронутой части сети?

Профильный специалист нужен, когда конфликт влияет на физическую эксплуатацию сети:

| Доменный случай | Кого подключать |
|---|---|
| switch/feeder/isolation trace | инженер электросети |
| valve/pressure zone | инженер водоснабжения |
| regulator/pressure tier/safety | инженер газовой сети |
| duct/fiber/splice path | инженер телеком |
| sewer flow direction/upstream-downstream | инженер канализации |
| спор field evidence vs GIS | ответственный инженер участка |

### 14. Какие evidence обязательны для High и Critical?

Для **High**:

- work order;
- reason comment Editor;
- geometry diff;
- association diff;
- validation result;
- trace before/after;
- field evidence или объяснение, почему его нет.

Для **Critical**:

- всё из High;
- подтверждение профильного специалиста;
- affected service/customers/devices/subnetworks;
- explicit post approval;
- risk acceptance comment;
- rollback/correction plan, если post аварийный;
- audit record.

### 15. Как убедиться, что после review данные не изменились?

Нужно проверить:

- version state id / edit timestamp;
- hash или snapshot conflict package;
- changed objects после approval;
- повторный reconcile status;
- повторную validation;
- trace result timestamp;
- stale approval flag.

Если после approval изменились geometry, association, network attribute, terminal configuration или Default, review должен стать недействительным.

## Should

### 16. Нужно ли показывать исходное предложение Editor и альтернативные решения?

Да. Reviewer должен видеть:

- что выбрал Editor;
- почему выбрал;
- какие варианты были доступны;
- почему не выбраны Keep Default / Manual edit;
- system recommendation;
- расхождение между recommendation и решением Editor.

### 17. Каким должно быть объяснение причины выбора Editor?

Хорошее объяснение Editor:

> “Выбран Keep Mine, потому что work order WO‑1247 подтверждает перенос junction, фото от 2026‑06‑14 показывает новое положение, Default association была создана до полевого уточнения. После validation dirty areas очищены, trace изменился ожидаемо: device перешёл в subnetwork X.”

Плохое объяснение:

> “Оставил моё, потому что я так правил.”

### 18. Нужно ли видеть автора, время, work order и историю изменений Default?

Да. Особенно для Default.

Reviewer должен понять:

- кто изменил Default;
- когда;
- из какой version/post;
- по какому work order;
- были ли это аварийные изменения;
- есть ли уже downstream consumers;
- не конфликтует ли Default с более свежим field evidence.

### 19. Как показывать trace before/after и affected customers/devices/subnetworks?

Показывать нужно так:

| Блок | Содержание |
|---|---|
| Summary | “Trace changed: +12 devices, -1 switch, subnetwork changed” |
| Before | список/карта до решения |
| After | список/карта после решения |
| Diff | added/removed affected elements |
| Service | affected customers/devices |
| Subnetwork | before/after subnetwork name/status |
| Confidence | clean/dirty/invalid trace |

Не надо показывать только две карты без diff‑списка. Reviewer должен видеть, **что именно добавилось или исчезло**.

### 20. Какие автоматические рекомендации допустимы для Reviewer?

Допустимы:

- “Requires manual edit”;
- “Reviewer approval required”;
- “Risk should be raised to High”;
- “Run validation before approve”;
- “Trace changed; check affected service”;
- “Keep Mine appears consistent with work order, but association diff requires review”.

Недопустимо для High/Critical:

- автоматически approve;
- автоматически downgrade risk;
- рекомендовать Keep Mine без validation/trace/evidence.

### 21. Что должна объяснять система, если её рекомендация отличается от решения Editor?

Она должна объяснить конфликт между решением и фактами:

> “Editor выбрал Keep Mine, но system recommendation = Manual edit, потому что Default изменил association того же device, trace before/after отличается, affected subnetwork changed. Keep Mine сохранит geometry, но может потерять корректную association.”

### 22. Может ли Reviewer понизить risk tier? Какие доказательства и комментарий обязательны?

Да, но только с обязательными доказательствами:

- validation clean;
- no error dirty areas;
- trace unchanged или expected change;
- affected service unchanged;
- association diff explained;
- work order/evidence подтверждают решение;
- Reviewer comment обязателен.

Пример comment:

> “Risk downgraded High → Normal: association diff не влияет на connectivity, trace before/after identical, dirty areas cleaned after validation, work order confirms geometry correction only.”

### 23. Может ли Reviewer изменить resolution самостоятельно или должен вернуть работу?

Зависит от типа конфликта.

| Случай | Действие Reviewer |
|---|---|
| простое Keep Default вместо Keep Mine по атрибуту | может изменить сам |
| non-network field | может изменить сам |
| geometry + association | лучше вернуть на Manual edit |
| trace changed | вернуть Editor или профильному специалисту |
| Critical | не менять молча, только через explicit decision |
| нужно физически переподключить сеть | вернуть на Manual edit |

Reviewer не должен становиться “скрытым Editor” для инженерной сети.

### 24. Когда комментарий обязателен для approve, reject или risk downgrade?

Комментарий обязателен при:

- approve High/Critical;
- reject;
- risk downgrade;
- override system recommendation;
- Keep Mine при Default newer;
- Keep Default при Mine evidence present;
- Manual edit required;
- specialist escalation;
- post gate override;
- approval after trace changed.

### 25. Какие действия должны быть доступны из conflict explanation?

Для Reviewer:

- Approve;
- Reject;
- Request changes;
- Require Manual edit;
- Raise risk;
- Downgrade risk with comment;
- Open geometry diff;
- Open association diff;
- Run/re-run validation;
- Run trace before/after;
- View evidence;
- Request specialist;
- Block post;
- Mark post safe;
- Add audit comment.

### 26. Как должен выглядеть повторный review после изменения данных?

Повторный review должен явно показывать:

- что изменилось после прошлого approval;
- какой approval стал stale;
- новый diff;
- новый validation result;
- новый trace before/after;
- новый risk tier;
- кто внёс изменения;
- что нужно подтвердить заново.

Нельзя просто сохранить старую галочку approve.

### 27. Что необходимо сохранить в audit для расследования решения?

Для Reviewer audit должен включать:

- proposed resolution Editor;
- final Reviewer decision;
- alternatives considered;
- risk tier before/after;
- downgrade/upgrade reason;
- evidence reviewed;
- validation result;
- trace before/after;
- affected service/subnetwork;
- specialist decision;
- stale approval events;
- post gate decision;
- timestamps;
- user ids;
- comments;
- final post result.

## Nice

### 28. Какие конфликты можно проверять пакетно, а какие только по одному?

**Пакетно можно:**

- non-network attributes;
- одинаковый field update по группе объектов;
- geometry cleanup без connectivity impact;
- conflicts одного work order без trace/service impact;
- Simple/Normal с clean validation.

**Только по одному:**

- device/junction/line connectivity;
- association changes;
- trace changed;
- affected service/subnetwork;
- update-delete;
- High/Critical;
- safety/isolation;
- conflicting evidence.

### 29. Как сортировать очередь: risk, SLA, affected service, work order или domain?

Очередь Reviewer лучше сортировать так:

1. Critical;
2. SLA breach;
3. affected service/customers;
4. trace changed;
5. High;
6. work order priority;
7. domain/area;
8. oldest first.

Одна только дата создания — плохой порядок, потому что безопасный старый Normal не должен идти выше свежего Critical.

### 30. Нужна ли история аналогичных конфликтов и прошлых решений?

Да, но как вспомогательный блок.

Полезно видеть:

- как решали такой же asset type;
- кто подтверждал;
- был ли post incident;
- типовой safe resolution;
- частоту false positive;
- похожие conflicts по feeder/pressure zone.

Но история не должна заменять текущую validation/trace.

### 31. Какие детали стоит скрыть до открытия блока «Подробнее»?

Скрыть:

- raw attribute table;
- полный JSON trace;
- все GlobalID;
- длинные logs;
- старые reconcile attempts;
- unrelated dirty areas;
- все attachments без фильтра.

Оставить сразу:

- risk;
- cause;
- proposed resolution;
- trace impact;
- validation status;
- affected service;
- post gate.

### 32. Что создаст review fatigue или ложное чувство безопасности?

Review fatigue создаст:

- слишком много Normal conflicts на ручном review;
- одинаковые false positive;
- отсутствие группировки;
- длинные экраны без summary;
- обязательные комментарии на Simple;
- постоянные “High” без реального impact.

Ложное чувство безопасности создаст:

- зелёный статус без trace;
- “validation passed” без affected extent;
- скрытые dirty areas;
- recommendation без confidence;
- approval, который не сбрасывается после изменения данных.

### 33. Когда Reviewer обязан открыть внешнюю GIS-систему или исходные документы?

Reviewer обязан открыть внешние источники, если:

- field evidence отсутствует;
- work order неясный;
- trace impact спорный;
- affected service критичный;
- association diff непонятный;
- схема сети имеет юридический/эксплуатационный риск;
- специалист требует исходный документ;
- system explanation противоречит карте;
- есть post incident history.

### 34. При каком результате Reviewer перестанет доверять conflict explanation?

Reviewer перестанет доверять, если:

- system recommendation часто противоречит реальным последствиям;
- trace impact скрывается;
- risk tier не объясняется;
- dirty areas не показываются;
- approval не invalidated после изменений;
- affected service считается неверно;
- evidence “прикреплено”, но не связано с объектом;
- Keep Mine предлагается при association diff без review;
- прошлые approved conflicts привели к аварийным correction.

## Сценарная проверка для Reviewer

**Сценарий:**
Editor выбрал Keep Mine после переноса junction. В `Default` изменена association того же device. Validation завершилась без общей ошибки, но trace before/after отличается и затронут другой subnetwork.

### Как Reviewer должен пройти сценарий

| Шаг | Действие Reviewer |
|---|---|
| Проверка evidence | Проверяю work order, фото, sketch, комментарий бригады |
| Оценка риска | Повышаю до High/Critical, потому что trace и subnetwork changed |
| Проверка решения Editor | Проверяю, не сохраняет ли Keep Mine неправильную association |
| Approve/reject/manual edit | Скорее Manual edit или reject до объяснения trace impact |
| Эскалация | Подключаю профильного специалиста по affected subnetwork |
| Post gate | Блокирую post до validation + trace + evidence + final approval |

### Финальный вопрос для Reviewer

**Что здесь может заставить Reviewer подтвердить опасное решение или необоснованно задержать безопасное?**

Хороший ответ Reviewer:

> Опасное решение можно подтвердить, если explanation показывает “validation passed” как зелёный статус, но прячет trace/subnetwork change. Ещё опаснее, если Keep Mine выглядит как recommended action без объяснения association diff. Безопасное решение можно задержать, если все geometry changes автоматически получают High/Critical, даже когда trace unchanged, dirty areas cleaned и work order полностью подтверждает correction.

---

# Итоговая модель для Release 2 Conflict Explanation

Для `Editor` объяснение должно отвечать:

> **Что произошло? Чем это опасно для сети? Что мне делать дальше?**

Для `Reviewer` объяснение должно отвечать:

> **Доказал ли Editor, что выбранное решение соответствует work order, evidence, validation и trace, и можно ли безопасно открыть post gate?**

Критически важно: `Base / Mine / Default` — это только слой сравнения версий. Для Utility GIS его нельзя считать полноценным conflict explanation без geometry diff, association diff, dirty areas, validation, trace before/after, affected service/subnetwork, evidence, risk reason и audit.

---

# Источники для доменной проверки

1. Загруженный файл: `Ф2.md` — анализ веб‑ГИС сервисов для совместного редактирования пространственных данных.
2. Esri ArcGIS Pro Documentation — Manage branch version conflicts: https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/manage-branch-version-conflicts.html
3. Esri ArcGIS Pro Documentation — Reconcile and post edits to a branch version: https://doc.esri.com/en/arcgis-pro/latest/help/data/geodatabases/overview/reconcile-and-post-edits-to-a-branch-version.html
4. Esri ArcGIS Pro Documentation — Dirty areas: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/dirty-areas-in-a-utility-network.html
5. Esri ArcGIS Pro Documentation — Connectivity and associations: https://pro.arcgis.com/en/pro-app/latest/help/data/utility-network/about-connectivity-and-associations.htm
6. Esri ArcGIS Pro Documentation — Validate a network topology: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/validate-a-network-topology.html
7. Esri ArcGIS Pro Documentation — Utility network trace types: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/utility-network-trace-types.html
8. Esri ArcGIS Pro Documentation — Configure a trace: https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/configure-a-trace.html
