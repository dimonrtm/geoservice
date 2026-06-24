# Дизайн Доменного Слоя Базы Знаний

Date: 2026-06-24
Status: Approved for spec review

## Цель

Доработать project knowledge wiki так, чтобы она строила каноническую
доменную модель области из `RAW_inputs`, текущей wiki, sprint-документов,
`Code_wiki` и кода. Новый слой должен помогать:

- извлекать сущности, концепции, пользователей/роли и события системы;
- строить DDD-модель области;
- покрывать основные strategic и tactical DDD concepts: ubiquitous language,
  subdomains, bounded contexts, context map, entities, value objects,
  aggregates, aggregate roots, domain events, services, repositories,
  factories, modules, specifications, policies, commands и integration
  patterns;
- фиксировать конфликты, которые мешают получить непротиворечивую модель;
- генерировать вопросы для уточнения модели данных;
- помогать планировать 14-дневные спринты на основе доменной модели, кода и
  текущей базы знаний.

`Code_wiki` продолжает наполняться через `/ingest repository-change`.
`Vision_wiki` сохраняется как legacy/source layer и не является новым
каноническим доменным слоем.

## Выбранный Подход

Выбран подход Markdown-first с компактными реестрами.

Основное знание остается в человекочитаемых `.md` нодах, а реестры дают агенту
быстрый способ найти ноды, проверить полноту, увидеть статус и построить
следующий набор вопросов.

Отклоненные альтернативы:

1. Только Markdown-ноды без реестров. Этот вариант проще, но быстро усложнит
   поиск дублей, пробелов и конфликтов.
2. Schema-first модель в YAML/JSON с генерацией Markdown. Этот вариант строже,
   но преждевременно превращает wiki в мини-базу данных и усложняет ручное
   сопровождение.

## Новая Структура

```text
Wiki/
  glossary/
  entities/
  value_objects/
  concepts/
  actors/
  external_systems/
  commands/
  domain_events/
  system_events/
  policies/
  specifications/
  conflicts/
  questions/
  _registry/
    glossary.md
    entities.md
    value_objects.md
    concepts.md
    actors.md
    external_systems.md
    commands.md
    domain_events.md
    system_events.md
    policies.md
    specifications.md
    conflicts.md
    questions.md
  _templates/

DDD_Wiki/
  domains/
  subdomains/
  bounded_contexts/
  context_map/
  aggregates/
  services/
  repositories/
  factories/
  modules/
  relationships/
  state_machines/
  invariants/
  use_cases/
  integration_patterns/
  model_health.md
  index.md
```

`Wiki/` хранит атомарные доменные ноды: что известно о термине ubiquitous
language, сущности, value object, концепции, actor, external system, command,
domain event, system event, policy, specification или конфликте.

`DDD_Wiki/` хранит производную модель: bounded contexts, aggregates, связи,
state machines, invariants, services, repositories, factories, modules, context
map, integration patterns, use cases и диагностику полноты модели.

`Vision_wiki` читается при initialization-проходе и конфликтных уточнениях как
legacy/source layer. Новые канонические доменные знания после внедрения
пишутся в `Wiki/` и `DDD_Wiki/`.

## Реестры

Реестр является компактной навигацией и статусом, а не заменой нод.
Аргументация, источники, инварианты и подробности живут в отдельных `.md`
файлах.

Минимальные реестры:

- `Wiki/_registry/glossary.md` - термины ubiquitous language и контекст, в
  котором термин имеет конкретное значение.
- `Wiki/_registry/entities.md` - сущности, aggregate roots и внешние объекты
  домена.
- `Wiki/_registry/value_objects.md` - immutable concepts без собственной
  идентичности.
- `Wiki/_registry/concepts.md` - доменные понятия, правила и термины.
- `Wiki/_registry/actors.md` - пользователи, роли, персоны, команды и
  responsibilities.
- `Wiki/_registry/external_systems.md` - внешние системы, upstream/downstream
  dependencies и границы интеграции.
- `Wiki/_registry/commands.md` - намерения изменить состояние модели.
- `Wiki/_registry/domain_events.md` - значимые для домена события, которые
  произошли в прошлом.
- `Wiki/_registry/system_events.md` - события системы, triggers, actors и
  effects.
- `Wiki/_registry/policies.md` - доменные правила принятия решений.
- `Wiki/_registry/specifications.md` - predicates/business rules, проверяющие
  допустимость состояния или действия.
- `Wiki/_registry/conflicts.md` - конфликты модели и следующие вопросы.
- `Wiki/_registry/questions.md` - сохраненные candidate/top questions для
  `/discover` и планирования спринтов.

Пример полей для `entities.md`:

```markdown
| ID | Нода | Тип | Bounded context | Статус | Уверенность | Главный источник | Связи | Открыто |
|---|---|---|---|---|---|---|---|---|
| ENT-001 | [[../entities/work_order]] | aggregate root | work_order | active | verified | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md` | `User`, `AOI`, `Feeder`, `EditVersion` | - |
```

Пример полей для `system_events.md`:

```markdown
| ID | Событие | Нода | Actor | Trigger | Изменяет | Preconditions | Статус | Источник |
|---|---|---|---|---|---|---|---|---|
| EVT-001 | EditVersionOpened | [[../system_events/edit_version_opened]] | Editor | Первое открытие work order | `EditVersion`, `WorkOrder.status` | Editor назначен на WorkOrder | active | sprint docs |
```

Пример полей для `domain_events.md`:

```markdown
| ID | Domain event | Нода | Bounded context | Raised by | Значение для домена | Downstream reactions | Статус | Источник |
|---|---|---|---|---|---|---|---|---|
| DEV-001 | ReviewPackageApproved | [[../domain_events/review_package_approved]] | review_post | `ReviewDecision` | Reviewer подтвердил готовность package к post | Audit, post eligibility, notifications | planned | Release 2 RAW |
```

Пример полей для `conflicts.md`:

```markdown
| ID | Конфликт | Блокирует | Ноды | Источник A | Источник B | Severity | Следующий вопрос |
|---|---|---|---|---|---|---|---|
| CON-001 | Reviewer approve package или выполняет technical post? | Role model, permissions, sprint scope | `Reviewer`, `Post`, `ReviewDecision` | Release 1 docs | Release 2 reviewer decision | high | Кто в реальной организации имеет право менять authoritative Default? |
```

## Доверие К Источникам

При первичной инициализации доменной модели и обычном ingest используется такая
иерархия доверия:

1. Явные ответы пользователя и `RAW_inputs`.
2. Подтвержденные design/sprint docs.
3. Текущий код для фактического состояния реализации.
4. `Code_wiki` для технической интерпретации, если она не расходится с кодом.
5. `Vision_wiki` как legacy/source layer.

Противоречия не сглаживаются молча. Если источники расходятся и это влияет на
модель, создается или обновляется конфликт в `Wiki/conflicts/`, строка в
`Wiki/_registry/conflicts.md` и запись в `DDD_Wiki/model_health.md`.

## `/ingest`

`/ingest` работает с сырыми источниками. Его объектом всегда является один или
несколько файлов из `RAW_inputs/` либо явно указанный внешний source, который
нужно сначала обосновать как raw/source input. `/ingest` не должен превращаться
в repository snapshot, сканировать весь репозиторий или выполнять
initialization существующей базы знаний.

Если пользователь не указал путь, `/ingest` ищет только новые добавленные файлы
в `RAW_inputs/`, которых еще нет в обработанных source-записях `RAW_inputs/index.md`,
`Wiki/`, `DDD_Wiki/`, `Vision_wiki/`, `Code_wiki/` или `memory/project-state.md`.
Старые уже обработанные raw-файлы повторно не читать и не переобрабатывать.
Если старый raw-файл выглядит измененным, это неоднозначность: не запускать
повторный ingest автоматически, а запросить явное решение пользователя.

Обрабатывать нужно любые новые raw-файлы, а не только файлы с ответами на
вопросы. Новым raw source может быть документ, заметка, meeting transcript,
research result, planning answer, discovery answer, exported chat или другой
сырой материал, если он лежит в `RAW_inputs/` и еще не обработан.

Для переноса pipeline в другой репозиторий первичная модель может появиться
естественно: пользователь кладет первые сырые материалы в `RAW_inputs/`, а
обычный `/ingest` создает первые ноды `Wiki/` и первую DDD-проекцию.

В этом репозитории после первичной инициализации `/ingest` используется для
уточнения доменной модели из новых сырых файлов. Если сырой файл содержит
ответы на вопросы `/discover` или планирования спринта, `/ingest` извлекает из
него устойчивые доменные факты, закрывает или уточняет вопросы и обновляет
затронутые ноды. Само решение о составе спринта принимает planning skill.

Обычный `/ingest` получает два доменных прохода.

Первый проход извлекает атомарные знания:

- сущности;
- value objects;
- концепции;
- actors/roles/personas;
- external systems;
- commands;
- domain events;
- system events;
- policies;
- specifications;
- relationships;
- invariants;
- states и transitions;
- subdomain classification;
- context mapping hints;
- conflicts;
- gaps.

Результат пишется в `Wiki/` как отдельные `.md` ноды и компактные строки в
`Wiki/_registry/*.md`.

Второй проход обновляет `DDD_Wiki/`:

- domains и subdomains;
- bounded contexts;
- context map;
- aggregates;
- aggregate roots;
- domain/application services;
- repositories;
- factories;
- modules;
- relationships;
- state machines;
- invariants;
- integration patterns;
- use cases;
- `model_health.md`.

Если новые знания не позволяют построить непротиворечивую модель, агент не
выбирает одну трактовку без основания. Он фиксирует конфликт и отражает риск в
health-диагностике.

## Первичная Инициализация Доменной Модели

Для текущего репозитория начальная доменная модель строится отдельным
initialization-проходом после создания структуры `Wiki/`, `DDD_Wiki/` и
repo-local skills. Это не режим `/ingest`, а часть реализации нового доменного
слоя.

Initialization-проход один раз читает:

- `RAW_inputs/`;
- `Vision_wiki/`;
- sprint docs в `docs/release_*`;
- `Code_wiki/`;
- релевантный текущий код и тесты.

Результат initialization-прохода:

- стартовые ноды `Wiki/glossary/`, `Wiki/entities/`,
  `Wiki/value_objects/`, `Wiki/concepts/`, `Wiki/actors/`,
  `Wiki/external_systems/`, `Wiki/commands/`, `Wiki/domain_events/`,
  `Wiki/system_events/`, `Wiki/policies/`, `Wiki/specifications/`;
- стартовые `Wiki/conflicts/`;
- заполненные `Wiki/_registry/*.md`;
- стартовая модель `DDD_Wiki/`;
- `DDD_Wiki/model_health.md` со списком неполных областей, конфликтов и
  следующих действий.

Initialization-проход не переписывает `RAW_inputs`, не исправляет
legacy-документацию и не является регулярным workflow. После него новые знания
поступают через обычный `/ingest` из сырых файлов и через отдельный
`/ingest repository-change` для `Code_wiki`.

## `/discover`

Новый `/discover` стартует от состояния доменной модели, а не от общего списка
вопросов.

Перед генерацией вопросов он читает:

- `DDD_Wiki/model_health.md`;
- `Wiki/_registry/conflicts.md`;
- релевантные registry-файлы;
- нужные ноды `Wiki/`;
- legacy `Vision_wiki` как дополнительный источник;
- `Code_wiki` и текущий код, если вопрос связан с реализацией.

Затем `/discover` генерирует 150 candidate questions. Все 150 не показываются
пользователю по умолчанию; они могут сохраняться в `Wiki/questions/` или
`Wiki/_registry/questions.md` как рабочий артефакт.

Вопросы должны покрывать:

- неоднозначности ubiquitous language;
- classification `core/supporting/generic` для subdomains;
- границы bounded contexts и context map;
- context mapping patterns между bounded contexts;
- конфликты модели;
- неполные aggregates;
- неясные aggregate roots;
- missing value objects;
- неясные lifecycle/state transitions;
- спорные роли и permissions;
- external system boundaries;
- commands без owner/preconditions/outcome;
- domain events без source aggregate/reaction;
- policies и specifications без проверяемого правила;
- слабые invariants;
- system events без actor, trigger, affected entity или outcome;
- расхождения доменной модели и кода;
- риски для следующего sprint/release.

После генерации `/discover` ранжирует вопросы и показывает top 15. Для каждого
top-вопроса указывается:

- какую часть модели он разблокирует;
- почему он выбран;
- какие ноды будут затронуты;
- можно ли ответить в чате или лучше положить файл в `RAW_inputs`.

Ответ пользователя в чате может быть оформлен как source для обновления
`Wiki/DDD_Wiki`. Ответ файлом в `RAW_inputs` обрабатывается обычным `/ingest`.

## Планирование Спринтов

Для планирования нужен отдельный repo-local skill, например
`source-command-plan-sprint`. Не нужно перегружать `/discover`, потому что у
планирования другой scoring.

Спринт считается фиксированным таймбоксом 14 календарных дней.

Skill читает:

- `DDD_Wiki/model_health.md`;
- `Wiki/_registry/*.md`;
- open conflicts и gaps;
- `Code_wiki/index.md` и релевантные технические ноды;
- текущий код и тесты по выбранной области;
- roadmap и legacy `Vision_wiki` как справочный слой;
- существующие sprint docs в `docs/release_*`.

Если пользователь ответил на planning questions файлом в `RAW_inputs/`, skill
может читать этот файл как planning source. Если ответы содержат устойчивые
доменные уточнения, их нужно обработать обычным `/ingest <path>` до или после
подготовки sprint planning packet, в зависимости от того, блокируют ли они
выбор спринта.

Затем он генерирует 150 candidate planning questions и выбирает top 15.

Scoring planning questions:

- насколько ответ влияет на выбор feature;
- относится ли feature к core subdomain или supporting/generic области;
- снижает ли риск реализации;
- помогает ли выбрать следующий вертикальный инкремент;
- закрывает ли конфликт доменной модели;
- есть ли техническая готовность в коде;
- можно ли проверить результат в конце 14-дневного спринта;
- не расширяет ли scope за пределы release.

После ответов skill может подготовить sprint planning packet:

- цель 14-дневного спринта;
- top features;
- rejected/deferred items;
- affected domain nodes;
- code gaps;
- acceptance criteria;
- risks;
- вопросы или ответы, которые нужно положить в `RAW_inputs`.

## Проверки И Защита От Разъезжания

Нужны проверки консистентности wiki:

- каждый файл в `Wiki/` имеет `source`, `status`, `confidence` и `related`;
- каждый термин в `Wiki/_registry/glossary.md` имеет bounded context или явно
  помечен как cross-context term;
- каждая сущность из `Wiki/_registry/entities.md` имеет ноду;
- каждый value object имеет критерий equality и immutability notes;
- каждый bounded context имеет свою ubiquitous language boundary;
- каждый subdomain классифицирован как `core`, `supporting` или `generic`, либо
  явно помечен `needs-review`;
- context map отражает upstream/downstream отношения и integration pattern;
- каждый command имеет actor/source, target aggregate или service,
  preconditions и outcome;
- каждый domain event имеет source aggregate/context, happened-in-past
  формулировку и downstream reactions;
- каждая policy/specification имеет проверяемое правило или фиксирует
  открытый вопрос;
- каждый system event имеет actor, trigger, affected entity и outcome;
- каждый aggregate в `DDD_Wiki/aggregates/` ссылается на сущности из `Wiki/`;
- каждый conflict из `Wiki/conflicts/` попадает в
  `Wiki/_registry/conflicts.md` и `DDD_Wiki/model_health.md`;
- `/discover` и sprint planning задают вопросы, привязанные к
  gaps/conflicts/model health/code readiness, а не общие вопросы;
- `Vision_wiki` не обновляется как новый канон;
- `Code_wiki` продолжает обновляться через `/ingest repository-change` только
  для устойчивого технического знания.

Эти проверки можно добавить в `scripts/lint-wiki.py` или вынести в отдельный
read-only checker, если domain-layer проверки станут слишком объемными для
обычного wiki lint.

## DDD Coverage

Knowledge base должна уметь хранить и проверять следующие DDD concepts.

Strategic DDD:

- `Domain`;
- `Domain Model`;
- `Ubiquitous Language`;
- `Subdomain`;
- `Core Subdomain`;
- `Supporting Subdomain`;
- `Generic Subdomain`;
- `Bounded Context`;
- `Context Map`;
- context mapping patterns: `Partnership`, `Shared Kernel`,
  `Customer/Supplier`, `Conformist`, `Anti-Corruption Layer`,
  `Open Host Service`, `Published Language`, `Separate Ways`,
  `Big Ball of Mud`.

Tactical DDD:

- `Entity`;
- `Value Object`;
- `Aggregate`;
- `Aggregate Root`;
- `Domain Event`;
- `Domain Service`;
- `Application Service`;
- `Repository`;
- `Factory`;
- `Module`;
- `Specification`;
- `Policy`;
- `Command`;
- `Invariant`;
- `State Machine`.

Integration и implementation-adjacent concepts:

- `External System`;
- `Integration Event`;
- upstream/downstream dependency;
- published language/API contract;
- anti-corruption boundary;
- eventual consistency across aggregates;
- command/query separation, если это помогает выразить модель, но без
  обязательного внедрения CQRS.

Для GeoService особенно важны `Context Map`, `Subdomain classification`,
`Anti-Corruption Layer`, `Specification`, `Policy`, `Domain Event` и разделение
`Domain Event` / `System Event`, потому что модель должна объяснять
validation, review decision, post blockers, audit, external GIS boundaries и
границы `work_order`, `utility_network`, `review_post`, `audit`, `auth`.

## Изменяемые Области

Реализация должна согласованно обновить:

- `.agents/skills/source-command-ingest/SKILL.md`;
- `.agents/skills/source-command-discover/SKILL.md`;
- новый `.agents/skills/source-command-plan-sprint/SKILL.md`;
- `docs/knowledge-pipeline/README.md`;
- `AGENTS.md`;
- `index.md`;
- `memory/project-state.md`;
- `docs/agent-memory/file-map.md`;
- `scripts/lint-wiki.py` или отдельный domain checker;
- новую структуру `Wiki/`;
- новую структуру `DDD_Wiki/`.

## Acceptance Criteria

- `Wiki/` и `DDD_Wiki/` созданы как канонический доменный слой.
- `Vision_wiki` явно помечена как legacy/source layer для доменного знания.
- первичный initialization-проход строит начальную доменную модель из текущих
  источников без изменения `RAW_inputs` и не является режимом `/ingest`.
- Обычный `/ingest` извлекает доменные ноды и обновляет DDD-модель.
- Обычный `/ingest` без явного пути обрабатывает только новые добавленные
  файлы в `RAW_inputs/` и не читает повторно уже обработанные old raw sources.
- Обычный `/ingest` обрабатывает любые новые raw-файлы, а не только файлы с
  ответами на discovery/planning questions.
- `Wiki/` и `DDD_Wiki/` покрывают strategic и tactical DDD concepts из раздела
  `DDD Coverage`.
- В модели есть ubiquitous language, subdomains, bounded contexts, context map,
  aggregates, aggregate roots, value objects, commands, domain events,
  services, policies и specifications.
- Конфликты модели фиксируются в `Wiki/conflicts/`, реестре конфликтов и
  `DDD_Wiki/model_health.md`.
- `/discover` генерирует 150 candidate questions от состояния модели и
  показывает top 15.
- Sprint planning skill генерирует 150 planning questions и top 15 для
  14-дневного спринта.
- `Code_wiki` продолжает жить по правилу `/ingest repository-change`.
- Проверки находят отсутствующие ноды, неполные system events, несвязанные
  conflicts и вопросы без привязки к model health.

## Риски

- Риск: новый слой начнет дублировать `Vision_wiki`. Смягчение: `Vision_wiki`
  сделать legacy/source layer, а новые доменные факты писать только в
  `Wiki/DDD_Wiki`.
- Риск: реестры станут вторым источником истины. Смягчение: реестры хранят
  только компактный статус и ссылку на ноду, подробности остаются в нодах.
- Риск: initialization-проход будет слишком большим. Смягчение: делать его по
  областям и фиксировать неполные зоны в `model_health.md`.
- Риск: 150 вопросов создадут шум. Смягчение: пользователю показывать только
  top 15, а остальные сохранять только как рабочий артефакт при необходимости.
- Риск: planning skill начнет выбирать слишком большой scope. Смягчение:
  scoring должен учитывать фиксированный таймбокс 14 календарных дней и
  проверяемый вертикальный инкремент.
- Риск: knowledge base начнет требовать все DDD concepts даже для простых
  областей. Смягчение: обязательным является явный статус `not-applicable` или
  `needs-review`, а не искусственное создание лишних нод.

## Источники DDD

- [Martin Fowler: Bounded Context](https://martinfowler.com/bliki/BoundedContext.html)
- [Martin Fowler: DDD Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html)
- [Microsoft: Use domain analysis to model microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis)
- [Microsoft: Use tactical DDD to design microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design)
