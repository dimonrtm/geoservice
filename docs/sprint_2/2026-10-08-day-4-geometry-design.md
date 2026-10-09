# День 4: детерминированная геометрия и command fingerprint

Дата: 8 октября 2026 года.
Статус: письменная спецификация принята пользователем 8 октября 2026 года ответом «Принимаю». Реализация не начата.
Основание: [анализ и ответы пользователя](2026-10-08-day-4-geometry-analysis.md), [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md), [спецификация Дня 2](2026-10-01-day-2-first-save-schema-design.md).
Исследованный код: HEAD `ba1c37f`.

## 1. Цель и границы

День 4 календарного плана от 6 августа создаёт детерминированное ядро редактирования одной внутренней вершины существующей линии. Одинаковый запрос в одной EditVersion должен давать одинаковый canonical intent и fingerprint независимо от текущего snapshot, перезапуска backend, внешнего Decimal context и изменения общей настройки сетки.

В согласованный объём входят:

- точный числовой разбор будущего Save request;
- Decimal canonicalization и structure guard;
- отдельная проверка перехода относительно current snapshot;
- версионированный command fingerprint для допустимых запросов и domain rejections;
- неизменяемая geometry policy в EditVersion;
- migration/backfill существующих версий и назначение policy новым версиям;
- точечное исправление workspace geometry readback;
- unit tests и integration tests перечисленных границ.

Полный Save endpoint, транзакция mutation, durable replay orchestration, PostGIS valid/simple/AOI guards и UI остаются следующим дням. День 4 определяет их входные контракты, но не объявляет весь first-save сценарий реализованным.

Исходная геометрия в `utility_network.default_state_features` не изменяется. Backfill policy не изменяет current geometry, operation, draft revision, registry или history.

## 2. Состояние кода и архитектурное решение

Настройки уже содержат Decimal grid и rounding mode. Общая GeoJSON schema использует float. `EditVersionService` умеет открывать/переоткрывать версии, но Save отсутствует. Схема command registry и change events уже реализована; алгоритма fingerprint нет. Workspace SQL использует `ST_AsGeoJSON(...)` без явно заданной точности.

Выбран вариант хранения policy непосредственно в EditVersion. Отдельный каталог policies не создаётся: в Sprint 2 нет отдельного процесса управления несколькими наборами правил.

Границы компонентов:

| Компонент | Вход | Выход и ответственность |
| --- | --- | --- |
| Parser | Исходные JSON bytes | Проверенный request с Decimal coordinates; ошибки формата |
| Geometry policy | Закреплённые поля версии | Проверенные grid, mode и версия алгоритма |
| Canonicalization | Request, baseline, policy | Candidate либо полное представление несопоставимой структуры; baseline diff |
| Structure/transition guard | Baseline, candidate, отдельно current | Допустимость структуры и смены вершины; no-op и operation |
| Fingerprint | Нормализованный intent и неизменяемый контекст | Строка SHA-256 с версией формата |
| Geometry codec | EWKB / canonical coordinates | Точные storage values и GeoJSON без десятичного обрезания |
| Repository/open flow | Settings при создании; сохранённая policy при чтении | Durable policy и корректное повторное открытие |

Чистое ядро не импортирует SQLAlchemy, FastAPI, Shapely или глобальные settings. Parser и codec являются адаптерами. Не создаётся универсальный drawing/geometry framework.

## 3. Geometry policy v1

### 3.1. Пространственный контракт

- SRID `4326`, координаты XY: X — longitude, Y — latitude.
- Origin сетки `(0,0)`.
- Rounding mode `ROUND_HALF_AWAY_FROM_ZERO`; числовая реализация использует Decimal и `ROUND_HALF_UP`.
- Default и минимальный шаг — `0.0000001°`.
- Более крупные шаги настраиваются; более мелкие в Sprint 2 запрещены.

На широте demo `44.8205°` default соответствует примерно 11.1 мм по широте и 7.9 мм по долготе. Это разрешение хранения, не доказательство positional accuracy исходных данных.

### 3.2. Технические пределы

Следующие конкретные пределы дополняют согласованное минимальное разрешение:

| Параметр | Контракт |
| --- | --- |
| Величина grid | От `0.0000001` до `360` включительно |
| Десятичное представление grid | После удаления лишних конечных нулей не более 9 позиций после запятой; эквивалентно целому `grid * 10^9` |
| Режим и версия | Только `ROUND_HALF_AWAY_FROM_ZERO` и версия `1` |
| Числовой token координаты в JSON | До 64 ASCII-символов, включая знак, точку и exponent |
| Явная exponent координаты | По модулю не больше 324 |
| Входной диапазон X/Y | `[-180,180]` / `[-90,90]` |

Дополнительные разряды записи шага позволяют сохранить поддержку `0.00000025`, величина которого больше минимального шага. Они не разрешают перемещения с субмиллиметровым шагом.

Ограничение длины числа ограничивает вычислительную работу parser, а не определяет точность сохраняемых перемещений. Оно допускает ранее согласованное число `0.000000149999999999999999999`.

Проверки выполняются точно, без float, округления настройки или автоматической подстановки default при ошибке. Настройка `1E+1000`, разрешённая старым settings-only тестом, становится недопустимой. Ошибка configuration блокирует migration/startup.

## 4. Формат запроса и точный parsing

Parser предназначен для будущего PUT из ТЗ. Реализация самого endpoint не входит в День 4.

Request содержит только `commandId`, `draftVersionToken`, `geometry`. UUID передаётся строкой и разбирается как UUID. Token — непустая строка, без числового преобразования, trim или Unicode normalization. `"1"` и `"01"` — разные expected tokens.

Geometry содержит только `type="LineString"` и `coordinates`. Coordinates — массив минимум из двух XY-пар; каждая ордината — конечный JSON number в допустимом диапазоне. Scientific notation разрешена.

До use case отклоняются:

- malformed JSON и повторяющиеся ключи любого JSON object;
- неизвестные поля;
- отсутствующие/неправильные identifiers или token;
- другой geometry type, включая MultiLineString;
- пустой LineString или одна вершина;
- неправильная вложенность, Z/M или XY-пары другой длины;
- координаты string, bool, null, NaN/Infinity;
- превышение числовых ограничений или входного диапазона.

Эти ошибки не резервируют CommandId. Исправленный запрос может использовать тот же ID.

Исходные JSON numbers разбираются непосредственно в Decimal. Пропуск через существующую float GeoJSON schema до canonicalization запрещён. Для числовых hooks используется исходный token с проверкой длины/exponent до создания Decimal. Нецелочисленные и целочисленные JSON numbers обрабатываются одинаково по значению.

Request LineString из двух вершин проходит проверку формата, но относительно eligible baseline из трёх вершин получает domain `GEOMETRY_STRUCTURE_CHANGED`. Baseline LineString из двух вершин сам не eligible и даёт `FEATURE_NOT_EDITABLE`. Изменение parts уже исключено LineString-only форматом; независимый domain guard также не разрешает подменить geometry type.

## 5. Canonicalization

### 5.1. Округление к сетке

Пусть `g` — закреплённый grid:

`Q(x) = g * round_half_away_from_zero(x / g)`.

Это кратность шагу, а не округление количества десятичных знаков. При `g=0.0000001`:

| Вход | Q(x) |
| --- | --- |
| `0.00000015` | `0.0000002` |
| `-0.00000015` | `-0.0000002` |
| `0.000000149999999999999999999` | `0.0000001` |
| `-0.000000149999999999999999999` | `-0.0000001` |

Для независимости от внешнего Decimal context расчёт использует новый локальный Context с явно заданными precision, rounding, exponent bounds и traps. Недостаточная precision промежуточного деления не должна превращать число ниже midpoint в midpoint.

Способ обеспечить достаточную precision:

1. Из Decimal tuples привести x и g к общему десятичному масштабу без округления, получив целые N и положительное D, для которых `x/g = N/D`.
2. Взять precision не меньше `digits(abs(N)) + digits(D) + 2`, считая `digits(0)=1`; exponent bounds `[-4096,4096]` покрывают согласованные входы.
3. Выполнить Decimal division, затем `to_integral_value(rounding=ROUND_HALF_UP)` и точное умножение на g в достаточном локальном context.
4. Нормализовать числовой ноль; не переносить flags/traps внешнего context.

Обоснование: ненулевое расстояние рационального `N/D` от половины целого не меньше `1/(2D)`; выбранная precision делает погрешность деления меньше этого расстояния. Точный midpoint представим конечной дробью и не теряется. Unit tests сверяют результаты с независимым целочисленным oracle через quotient/remainder, а не с повторным вызовом production rounding.

### 5.2. Восстановление baseline

Для каждой ординаты r из request и соответствующей ординаты b из baseline:

`candidate = b`, если `Q(r) == Q(b)`; иначе `candidate = Q(r)`.

Правило действует отдельно для X и Y. Если меняется только X, Y восстанавливается точно из baseline при совпадении на сетке.

Пример: baseline X `65.52500004`, request X `65.52500003`, grid `0.0000001`. Округлённые значения совпадают; candidate X равен `65.52500004`, а не `65.5250000`.

Baseline не переписывается. Candidate намеренно может содержать baseline coordinates вне сетки. Точный baseline request и повтор canonical candidate являются неподвижными точками алгоритма.

Входное изменение endpoint или нескольких внутренних вершин не является автоматическим отказом: сравнивается resulting candidate после этого правила.

### 5.3. Структура и ошибки

Baseline eligible, если это существующая line feature с 2D LineString минимум из трёх вершин. Позиция вершины в baseline array задаёт её identity.

При несовпадении числа вершин request не сопоставляется с baseline через усечённый zip. Массивы не сортируются; направление линии не нормализуется.

Для сопоставимой структуры строится полный candidate, затем проверяется:

1. Endpoints точно равны baseline.
2. Внутренних вершин, отличающихся от baseline, не больше одной.
3. Resulting coordinates остаются в географическом диапазоне.

Нарушение endpoints/count/числа изменённых вершин даёт `GEOMETRY_STRUCTURE_CHANGED`. Выход resulting coordinates за диапазон даёт `GEOMETRY_INVALID`; clamp запрещён. При одновременных нарушениях structure имеет приоритет перед диапазоном candidate. Проверка eligibility предшествует structure.

Изменение X и Y одной вершины считается одним изменением вершины. Нулевая разница допустима для baseline/Revert/no-op. Empty/collapsed/non-simple после построения геометрии проверяется последующим spatial boundary; parser не заменяет эту проверку.

## 6. Current snapshot, переходы и no-op

Current не канонизируется заново. Он сравнивается с точным baseline для определения уже изменённой вершины.

| Current относительно baseline | Candidate | Результат |
| --- | --- | --- |
| Baseline | Baseline | No-op |
| Baseline | Отличается A | Save A |
| Отличается A | Точно равен current | No-op |
| Отличается A | Новая позиция A | Save A |
| Отличается A | Baseline | Revert |
| Отличается A | Отличается B | `GEOMETRY_STRUCTURE_CHANGED`; сначала отдельный Revert |

Candidate == baseline задаёт `operation=unchanged`; иначе `operation=updated`. Candidate == current задаёт no-op. Эти сравнения не взаимозаменяемы.

Current с другой структурой, изменёнными endpoints или несколькими baseline отличиями не исправляется автоматически. Чистый guard сигнализирует повреждённый/неподдерживаемый контекст; будущий use case отображает его в существующий `WORK_ORDER_CONTEXT_INVALID`.

Проверка перехода применяется к новой команде после распознавания replay. Fingerprint не зависит от current. Поэтому прежний successful/rejected result не переоценивается как новый переход после изменения snapshot. Согласованное исключение повторной проверки доступа из Дня 2 сохраняется.

## 7. Fingerprint v1

### 7.1. Каноническая сериализация

Используется SHA-256. Внешний формат:

`geom-v1:sha256:<64 lowercase hex digits>`.

Хешируется UTF-8 канонического JSON без BOM и завершающего перевода строки. Формат соответствует `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)`. Ключи объектов сортируются; массивы сохраняют порядок.

Все геометрические ординаты и grid внутри хешируемого JSON представлены десятичными строками без exponent, без лишних ведущих/конечных нулей; у целого числа нет десятичной точки. Любой числовой ноль кодируется `"0"`. Сериализация Decimal не использует `normalize()` с неконтролируемым context и не проходит через float.

UUID — lowercase стандартная запись с дефисами. Counts, SRID, версии формата/алгоритма, baseline revision и vertex index — JSON integers; отсутствие index — JSON null. Token сохраняется как исходная opaque string. HTTP geometry при этом остаётся массивом JSON numbers.

### 7.2. Baseline structure hash

Хешируются format `baseline-structure-v1`, dimensions, geometry с точными нормализованными Decimal strings, partCount, SRID и vertexCounts. Для LineString partCount=1, vertexCounts содержит одно число. Включение всей последовательности baseline coordinates намеренно сильнее проверки только количества вершин.

Адаптер поддерживает также существующий 2D Point baseline, чтобы идентичность domain отказа `FEATURE_NOT_EDITABLE` не требовала притвориться, что baseline — линия: partCount=1, vertexCounts=[1], geometry coordinates — обычная XY-пара. Missing/corrupt baseline относится к проверке контекста вызывающим use case, а не заменяется выдуманной geometry.

Внешняя запись baseline digest: `sha256:<hex>`.

### 7.3. Envelope команды

Точный набор ключей и вложенность показаны в контрольном примере ниже. Значимые поля:

- fingerprintVersion=1 и commandType=`replace_feature_geometry`;
- workOrderId, editVersionId, featureId, actorUserId;
- baseline.defaultStateId, baseline.networkRevision, baseline.structureHash;
- draftVersionToken из request;
- geometryPolicy: version, xyResolution, roundingMode, srid, origin;
- geometryRepresentation и geometry;
- vertexIndex.

CommandId не входит: это ключ registry. Не входят current geometry/revision, время, correlationId, access state, spatial verdict, сообщение ошибки или результат перехода.

VertexIndex равен индексу единственной отличающейся внутренней вершины только при допустимом baseline structure diff; при baseline equality, несовместимой структуре или недопустимом diff — null. Полная geometry всегда остаётся в envelope.

### 7.4. Успешные и отклоняемые запросы

При сопоставимом LineString baseline/request используется `geometryRepresentation="baseline_aligned"` и candidate из раздела 5. Он участвует в fingerprint даже при последующем endpoint/multiple-vertex/range rejection.

При несопоставимой структуре, включая другой vertex count или неeligible Point baseline, используется `geometryRepresentation="unmatched_structure"` и весь request geometry. Числа нормализуются по записи, но не округляются к grid. VertexIndex=null. Нельзя усекать массив, заменять невалидную структуру пустой или хешировать только error code.

Следствия:

- `1`, `1.0`, `1e0` эквивалентны во всех ветках;
- в baseline_aligned ветке raw requests, дающие один candidate, имеют одинаковый fingerprint;
- в unmatched_structure ветке разные точные числовые значения различаются, даже если округлились бы одинаково;
- исправленный count или другое canonical содержимое меняет fingerprint;
- будущий spatial отказ не меняет fingerprint already-built candidate.

### 7.5. Replay

Одинаковые ID + fingerprint возвращают сохранённый terminal result. Тот же ID с другим fingerprint даёт `COMMAND_ID_REUSED`. Новый ID запускает новую проверку даже при том же fingerprint.

После отказа переместить B из-за уже изменённой A отдельный Revert не отменяет сохранённый отказ команды B. Новая попытка получает новый ID и актуальный token. Исправление format error до use case не требует нового ID.

Смена global settings не меняет fingerprint существующей версии, поскольку policy закреплена. Policy v1 и fingerprint v1 продолжают интерпретироваться по прежним правилам при будущих обновлениях; несовместимая смена алгоритма требует новой policy version.

### 7.6. Контрольный пример

Все UUID примера синтетические. Grid `0.0000001`; перемещена внутренняя вершина L-003 по Y с `44.8205` на `44.8215`.

Точные UTF-8 bytes baseline document — следующая одна строка без завершающего newline:

```json
{"dimensions":2,"format":"baseline-structure-v1","geometry":{"coordinates":[["65.52","44.82"],["65.525","44.8205"],["65.53","44.82"]],"type":"LineString"},"partCount":1,"srid":4326,"vertexCounts":[3]}
```

Baseline digest:

```text
sha256:342079da420e7190d6e5156e1ba210a5c41147c464569c4b8578f3568e8e8a39
```

Точные bytes envelope — следующая одна строка:

```json
{"actorUserId":"00000000-0000-0000-0000-000000000004","baseline":{"defaultStateId":"00000000-0000-0000-0000-000000000005","networkRevision":1,"structureHash":"sha256:342079da420e7190d6e5156e1ba210a5c41147c464569c4b8578f3568e8e8a39"},"commandType":"replace_feature_geometry","draftVersionToken":"1","editVersionId":"00000000-0000-0000-0000-000000000002","featureId":"00000000-0000-0000-0000-000000000003","fingerprintVersion":1,"geometry":{"coordinates":[["65.52","44.82"],["65.525","44.8215"],["65.53","44.82"]],"type":"LineString"},"geometryPolicy":{"origin":["0","0"],"roundingMode":"ROUND_HALF_AWAY_FROM_ZERO","srid":4326,"version":1,"xyResolution":"0.0000001"},"geometryRepresentation":"baseline_aligned","vertexIndex":1,"workOrderId":"00000000-0000-0000-0000-000000000001"}
```

Command fingerprint:

```text
geom-v1:sha256:1d01069ca8b22bf671865e99d831dc1ebc0fa2f65d71b64c972d99e2c414b622
```

Значения рассчитаны стандартной SHA-256 реализацией .NET по указанным UTF-8 bytes при подготовке документа. Это контрольные константы для будущих тестов, не результат проверки ещё не написанной реализации.

## 8. Durable policy в EditVersion

### 8.1. Поля и защита

| Поле | Тип | Требование |
| --- | --- | --- |
| geometry_xy_resolution | NUMERIC без фиксированного scale | NOT NULL; допустимый finite grid из раздела 3 |
| geometry_rounding_mode | VARCHAR(32) | NOT NULL; ROUND_HALF_AWAY_FROM_ZERO |
| geometry_policy_version | SMALLINT | NOT NULL; 1 |

Не использовать NUMERIC с scale, который молча округляет введённую настройку до проверки. CHECK исключает NaN/Infinity, нарушенный диапазон и недопустимую кратность `1e-9`. CHECK отдельно фиксирует mode/version v1.

BEFORE UPDATE trigger отклоняет изменение любого из трёх полей. Существующие updates revision, last_opened_at и других разрешённых полей продолжают работать. Постоянных server defaults для policy нет: каждый путь создания обязан явно назначать её.

Metadata отражает fields/CHECK; trigger создаётся только migration. `Base.metadata.create_all()` не заменяет полноценную schema.

### 8.2. Создание и повторное открытие

Settings валидируются при старте. При создании `EditVersionService` получает policy, передаёт её в `WorkOrderRepository.create_open_edit_version`; root и policy сохраняются атомарно.

Повторное открытие через `touch_edit_version` не переназначает policy. Сохранение/чтение geometry в этой версии использует persisted policy. После смены settings только новые версии получают новый grid.

Открытая версия с неизвестной policy version не обрабатывается как v1: это несовместимый контекст. В текущей schema запись такой версии запрещена CHECK.

### 8.3. Migration и backfill

Новая migration после `b7d2e9f4a6c8` выполняется одной transaction:

1. Проверяет geometry settings обновления.
2. Добавляет policy fields.
3. Заполняет все существующие EditVersion текущими grid/mode и version=1.
4. Включает NOT NULL, CHECK и trigger неизменности.

Backfill не меняет геометрию и не создаёт change events. Повтор `alembic upgrade head` и restart не переназначают policy.

Migration использует стабильный локальный контракт validation v1 без импорта изменяемого runtime Settings и без зависимости от JWT/security settings. Runtime и migration сверяются общей таблицей граничных примеров в тестах.

Сервис migrate в Compose получает те же geometry env values и defaults, что API. Для ручного запуска Alembic в runbook явно задаются те же значения. При отсутствии env default в обоих путях — `0.0000001`. Нестандартная runtime configuration не должна молча теряться в окружении migrator.

Порядок обновления: остановить API, запустить migration с согласованной конфигурацией, запустить новый API. Rolling update со старым writer не поддерживается этим этапом. Новые/существующие тестовые fixtures, создающие EditVersion напрямую, явно задают policy.

Downgrade удаляет trigger и policy fields. Он теряет закреплённую policy; после повторного upgrade старые значения не восстанавливаются автоматически. Геометрия и Day 2 history при downgrade этой migration не переписываются.

## 9. Точное хранение и readback

### 9.1. Что означает точный baseline

Baseline — значения, уже находящиеся в PostGIS. Восстановление неизвестных десятичных литералов до первоначальной загрузки не обещается.

Baseline/current читаются через EWKB. Для Decimal вычислений каждое конечное binary64 значение получает детерминированное кратчайшее десятичное представление, которое преобразуется обратно в то же binary64 значение; используется контракт `Decimal(repr(value))` для float, полученного из EWKB. Это допустимая граница чтения storage, а не разрешение преобразовать входной request в float.

Координаты baseline сохраняются также в исходном storage представлении. При выборе baseline ordinate она копируется без округления; Revert восстанавливает исходную геометрию. Signed zero baseline сохраняется при storage copying, хотя fingerprint и numeric equality считают оба нуля одинаковыми.

### 9.2. Запись candidate

Candidate содержит либо ординаты baseline, либо координаты сетки с не более чем 9 десятичными позициями в географическом диапазоне. На storage boundary grid ordinates переводятся в binary64 с проверкой, что обратная кратчайшая Decimal запись равна canonical числу. Нельзя молча принять потерю различимости.

Decimal вычисления не обещают точного двоичного представления десятичных дробей. Гарантия — устойчивость canonical decimal round-trip и сохранение baseline storage values. Неуспех проверки обратимости считается ошибкой реализации/адаптера и не превращается в успешный Save.

Не применять ST_SnapToGrid или full-line normalization к baseline, current или candidate как скрытый второй этап округления.

### 9.3. Workspace

В `workspace_aggregate.sql` geometry features передаётся через EWKB (допустимо hex-представление внутри существующего JSON aggregate). Repository декодирует geometry и возвращает прежнее поле `geometry_data` с GeoJSON numbers, используя codec. Публичная форма workspace не меняется.

Codec проверяет type/SRID/dimensions, сохраняет порядок координат и не обрезает десятичные разряды. Для текущих workspace features нужны Point и LineString. Общие legacy GIS APIs и AOI display projection не перестраиваются; authoritative AOI для будущей spatial validation читается непосредственно из БД.

Используются уже установленные GeoAlchemy2/Shapely. Неподдерживаемая geometry не приводится молча к 2D или LineString. Существующая workspace float schema допустима на выходе после lossless decoding; её JSON serialization проверяется на реальном HTTP response.

Новые поля changeSet/basicValidation/token и новый Save endpoint не добавляются этим разделом.

## 10. Затрагиваемые области

Пути относительно корня репозитория; перечисленные новые модули — планируемые, не уже созданные.

| Область | Файлы/каталоги |
| --- | --- |
| Чистое ядро | Новые модули в `apps/backend/utility_service/domain_services/edit_geometry/`: policy, canonicalization, structure, fingerprint и типы результатов |
| Транспортный разбор | Новый parser в `apps/backend/utility_service/web_api/`; request DTO в `use_cases/schemas/edit_version/`, без подключения PUT |
| Settings | `apps/backend/utility_service/utils/settings.py`, соответствующие tests |
| Root model и migration | `infrastructure/postgresql/models/work_order/edit_version.py`, новая Alembic revision |
| Open/reopen | `use_cases/services/edit_version_service.py`, `use_cases/deps.py`, `infrastructure/postgresql/repositories/work_order_repository.py` |
| Codec/readback | Новый infrastructure codec, `infrastructure/postgresql/sql/workspace_aggregate.sql`, repository workspace projection |
| Deployment | `infra/docker-compose.yml`, соответствующие test/runbook настройки окружения migration |
| Проверки | Domain/parser unit tests; settings/open/workspace regression; first-save metadata/migration tests; новые isolated DB integration tests |
| Документация | Артефакты и runbook в `docs/sprint_2/` |

Общий рефакторинг feature CRUD, auth, seed dataset или остальных GeoJSON API не входит в задачу.

## 11. Приёмка

| Группа | Обязательные доказательства |
| --- | --- |
| Grid | Default/min/max; non-default `0.00000025`; отказ для более мелкой сетки, лишней дробной precision и `1E+1000`; симметричные midpoint и числа по обе стороны |
| Decimal context | Изменение внешних precision/rounding/traps не меняет результат; независимый integer oracle |
| Parser | Исходные JSON bytes; точный below-midpoint пример; scientific notation, zero, wrong types/shape, duplicate keys, limits; пустой/одноточечный LineString не доходит до use case |
| Canonicalization | Идемпотентность; покоординатное восстановление baseline; off-grid baseline и endpoint noise; несколько raw отличий с одним/нулевым resulting diff |
| Structure | Endpoint, count/type, две внутренние вершины, X+Y одной вершины, сохранение порядка; отсутствие silent truncation |
| Transition | Все строки таблицы раздела 6; corrupted current не исправляется автоматически |
| Fingerprint | Golden vectors раздела 7; эквивалентные числа; grid-equivalent intent; каждый значимый context field; обе representation branches; current/global settings/commandId не влияют |
| Policy/schema | Non-default backfill; direct SQL immutability; NOT NULL/CHECK; metadata parity; допустимый update revision/reopen |
| Lifecycle policy | Новая версия получает settings, старая сохраняет policy; новая session/restart; повтор migration без backfill |
| Migration | Upgrade/downgrade/upgrade на изолированной БД; atomic failure при invalid settings; geometry/revisions/history до и после backfill неизменны |
| Codec/storage | Canonical → PostGIS → GeoJSON → Decimal; baseline с >9 fractional digits; midpoint-adjacent baseline; EWKB comparison untouched coordinates/Revert; negative/signed-zero/boundary coordinates |
| HTTP readback | Existing workspace response сохраняет числовые значения после JSON parsing; неизменная публичная форма |
| Регрессия | Existing settings, open/reopen, workspace, first-save schema/ORM constraints и инфраструктурные проверки затронутого окружения |

Integration tests выполняются в изолированной test-БД по существующим правилам репозитория. Demo-БД не используется для destructive test setup. Наличие схемы command registry не выдаётся за готовую replay orchestration: в День 4 проверяется её числовой контракт, а полный Save/retry тест добавляется при реализации use case.

## 12. Соотношение с исходной документацией

Эта спецификация уточняет День 4 в пределах обсуждения:

- вместо запрета любого raw изменения проверяется resulting geometry;
- baseline вне сетки сохраняется точно;
- смена изменённой вершины требует отдельного Revert;
- grid хранится в EditVersion, а не читается заново из глобальных settings для каждого Save;
- default/minimum — сантиметровый шаг, прежняя поддержка любого finite positive grid сужается;
- пустой входной LineString — format error без registry record;
- source grid приходит из runtime configuration при создании/backfill; общий dataset-metadata механизм не вводится;
- format fingerprint не зависит от current snapshot и не различает UI-кнопки Save/Revert как разные команды;
- сохранённые ответы/отказы и access retry следуют уточнённой спецификации Дня 2.

Wiki и ранние документы не переписываются автоматически. Необходимость repository-change ingest оценивается после реализации по появлению нового durable технического знания; создание этой спецификации само по себе не запускает ingest. Отдельная agent memory не нужна: основания и решения сохранены в analysis/design.

## 13. Проверка документа и следующий этап

Проведена самопроверка согласованности parsing, baseline-aware canonicalization, transition guards, fingerprint, policy lifecycle и readback. Контрольные SHA-256 рассчитаны независимо от будущего production кода. Проверка `git diff --check` относится к документации; product tests в рамках этого обсуждения не выполнялись.

Пользователь принял письменную спецификацию, включая числовые пределы раздела 3.2. Следующий артефакт — отдельный план реализации в этой же папке. Product code пока не меняется. Git staging, commit и push выполняет пользователь.
